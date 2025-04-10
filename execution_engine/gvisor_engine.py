import docker
import tempfile
import os
import json
import time
import uuid
from pathlib import Path

class GVisorExecutionEngine:
    """
    gVisor-based execution engine for serverless functions
    """
    def __init__(self):
        """
        Initialize the Docker client with gVisor runtime
        """
        self.client = docker.from_env()
        self.base_path = Path(__file__).parent
        
        # Test Docker connection
        try:
            self.client.ping()
            print("Connected to Docker daemon for gVisor execution")
        except Exception as e:
            print(f"Error connecting to Docker daemon: {e}")
            print("Please make sure Docker is installed and running")
    
    def _get_template_path(self, language, template_type):
        """
        Get the path to a template file (reusing Docker templates)
        """
        template_map = {
            "python": {
                "function": "python_function.py.template",
                "dockerfile": "Dockerfile.python.template"
            },
            "javascript": {
                "function": "javascript_function.js.template",
                "dockerfile": "Dockerfile.javascript.template"
            }
        }
        
        if language not in template_map:
            raise ValueError(f"Unsupported language: {language}")
        
        if template_type not in template_map[language]:
            raise ValueError(f"Unsupported template type: {template_type}")
        
        return self.base_path / "templates" / template_map[language][template_type]
    
    def _generate_function_file(self, function, temp_dir):
        """
        Generate function file from template
        """
        # Get the appropriate template
        template_path = self._get_template_path(function.language, "function")
        
        # Read template content
        with open(template_path, "r") as f:
            template_content = f.read()
        
        # Replace placeholder with function code
        function_content = template_content.replace("{{FUNCTION_CODE}}", function.code)
        
        # Determine the output file name based on language
        output_file = "function.py" if function.language == "python" else "function.js"
        output_path = os.path.join(temp_dir, output_file)
        
        # Write the function file
        with open(output_path, "w") as f:
            f.write(function_content)
        
        return output_path
    
    def _generate_dockerfile(self, function, temp_dir):
        """
        Generate Dockerfile from template
        """
        # Get the appropriate template
        template_path = self._get_template_path(function.language, "dockerfile")
        
        # Read template content
        with open(template_path, "r") as f:
            dockerfile_content = f.read()
        
        # Write the Dockerfile
        output_path = os.path.join(temp_dir, "Dockerfile")
        with open(output_path, "w") as f:
            f.write(dockerfile_content)
        
        return output_path
    
    def build_function_image(self, function):
        """
        Build a Docker image for the function
        """
        # Create a temporary directory for the function files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate function file
            self._generate_function_file(function, temp_dir)
            
            # Generate Dockerfile
            self._generate_dockerfile(function, temp_dir)
            
            # Build the Docker image
            image_name = f"serverless-gvisor-{function.id}-{uuid.uuid4().hex[:8]}"
            
            try:
                self.client.images.build(
                    path=temp_dir,
                    tag=image_name,
                    rm=True  # Remove intermediate containers
                )
                print(f"Built Docker image with gVisor: {image_name}")
                return image_name
            except Exception as e:
                print(f"Error building Docker image with gVisor: {e}")
                raise
    
    def remove_function_image(self, image_name):
        """
        Remove a Docker image
        """
        try:
            self.client.images.remove(image_name)
            print(f"Removed Docker image: {image_name}")
        except Exception as e:
            print(f"Error removing Docker image {image_name}: {e}")
            raise
    
    def execute_function(self, function, event_data, timeout=30):
        """
        Execute a function with the given event data using gVisor runtime
        """
        # Ensure we have a container image
        if not function.container_image:
            raise ValueError("Function does not have a container image")
        
        # Convert event data to JSON
        event_json = json.dumps(event_data)
        
        # Run the container with gVisor runtime
        try:
            # Run a new container with gVisor runtime
            result = self.client.containers.run(
                image=function.container_image,
                remove=True,  # Remove container after execution
                stdin_open=True,
                tty=False,
                command=None,  # Use the default command from the image
                input=event_json.encode('utf-8'),
                stdout=True,
                stderr=True,
                runtime="runsc",  # Use gVisor runtime
                timeout=timeout  # Set timeout
            )
            
            # Try to parse the result as JSON
            try:
                return json.loads(result.decode('utf-8'))
            except json.JSONDecodeError:
                return {"output": result.decode('utf-8')}
        
        except docker.errors.ContainerError as e:
            # Handle container execution error
            error_message = f"Function execution failed: {str(e)}"
            print(error_message)
            raise RuntimeError(error_message)
        
        except docker.errors.ImageNotFound:
            # Handle missing image
            error_message = "Function image not found"
            print(error_message)
            raise RuntimeError(error_message)
        
        except Exception as e:
            # Handle any other errors
            error_message = f"Unexpected error during function execution: {str(e)}"
            print(error_message)
            raise RuntimeError(error_message)
