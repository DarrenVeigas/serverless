import docker
import tempfile
import os
import json
import time
import uuid
import subprocess
from pathlib import Path

class DockerExecutionEngine:
    """
    Docker-based execution engine for serverless functions
    """
    def __init__(self):
        """
        Initialize the Docker client and create a pool of containers
        """
        self.client = docker.from_env()
        self.container_pool = {}  # Map of function_id to list of container IDs
        self.pool_size = 3  # Number of warm containers to keep per function
        self.base_path = Path(__file__).parent
        
        # Test Docker connection
        try:
            self.client.ping()
            print("Connected to Docker daemon")
        except Exception as e:
            print(f"Error connecting to Docker daemon: {e}")
            print("Please make sure Docker is installed and running")
    
    def _get_template_path(self, language, template_type):
        """
        Get the path to a template file
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
            image_name = f"serverless-function-{function.id}-{uuid.uuid4().hex[:8]}"
            
            try:
                self.client.images.build(
                    path=temp_dir,
                    tag=image_name,
                    rm=True  # Remove intermediate containers
                )
                print(f"Built Docker image: {image_name}")
                return image_name
            except Exception as e:
                print(f"Error building Docker image: {e}")
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
    
    def _warm_function_containers(self, function):
        """
        Create warm containers for a function
        """
        if function.id not in self.container_pool:
            self.container_pool[function.id] = []
        
        # Check how many containers we need to create
        num_to_create = self.pool_size - len(self.container_pool[function.id])
        
        if num_to_create <= 0:
            return
        
        # Create containers
        for _ in range(num_to_create):
            try:
                container = self.client.containers.create(
                    image=function.container_image,
                    command="sleep infinity",  # Keep container running
                    detach=True
                )
                self.container_pool[function.id].append(container.id)
                print(f"Created warm container {container.id[:12]} for function {function.id}")
            except Exception as e:
                print(f"Error creating warm container for function {function.id}: {e}")
    
    def _get_container(self, function):
        """
        Get a container for the function, either from the pool or create a new one
        """
        if function.id in self.container_pool and self.container_pool[function.id]:
            # Get a container from the pool
            container_id = self.container_pool[function.id].pop(0)
            try:
                return self.client.containers.get(container_id)
            except Exception as e:
                print(f"Error getting container {container_id} from pool: {e}")
        
        # Create a new container
        return self.client.containers.run(
            image=function.container_image,
            detach=True,
            remove=False  # We'll remove it manually after execution
        )
        
    def execute_function(self, function, event_data, timeout=30):
        """
        Execute a function with the given event data
        """
        # Ensure we have a container image
        if not function.container_image:
            raise ValueError("Function does not have a container image")
        
        # Convert event data to JSON
        event_json = json.dumps(event_data)
        
        # Run the container
        try:
            # Create a new container without starting it
            container = self.client.containers.create(
                image=function.container_image,
                stdin_open=True,
                tty=False,
                command=None,  # Use the default command from the image
            )
            
            try:
                # Start the container
                container.start()
                
                # Attach to the container to get logs
                output = container.attach(stdout=True, stderr=True, stream=False)
                
                # Use low-level API to send input to the container
                socket = self.client.api.attach_socket(
                    container=container.id, 
                    params={'stdin': 1, 'stream': 1}
                )
                
                # Send the input data
                os.write(socket.fileno(), event_json.encode('utf-8'))
                os.close(socket.fileno())
                
                # Wait for container to finish with timeout
                start_time = time.time()
                status = container.wait(timeout=timeout)
                
                # Get container output
                logs = container.logs(stdout=True, stderr=True).decode('utf-8')
                
                # Check container exit code
                if status['StatusCode'] != 0:
                    raise RuntimeError(f"Function execution failed with exit code {status['StatusCode']}: {logs}")
                
                # Try to parse the result as JSON
                try:
                    return json.loads(logs)
                except json.JSONDecodeError:
                    return {"output": logs}
                    
            finally:
                # Always clean up the container
                try:
                    container.remove(force=True)
                except Exception as e:
                    print(f"Error removing container {container.id}: {e}")
        
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