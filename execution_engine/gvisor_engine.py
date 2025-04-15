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
            
            # Verify gVisor runtime is available
            self._check_gvisor_availability()
            
        except Exception as e:
            print(f"Error connecting to Docker daemon: {e}")
            print("Please make sure Docker is installed and running")
            
    def _check_gvisor_availability(self):
        """
        Check if gVisor runtime is available in Docker
        """
        self.gvisor_available = False
        
        try:
            # Try to create a simple container with gVisor runtime
            container_info = self.client.api.create_container(
                image="alpine:latest",
                command="echo 'gVisor test'",
                host_config=self.client.api.create_host_config(runtime="runsc-ptrace")
            )
            
            # Clean up the container immediately
            self.client.api.remove_container(container_info['Id'])
            
            print("✅ gVisor (runsc) runtime is available and working")
            self.gvisor_available = True
            return True
            
        except docker.errors.APIError as e:
            if "Unknown runtime specified" in str(e) or "runtime is not supported" in str(e):
                print("⚠️ WARNING: gVisor (runsc) runtime is NOT available in Docker")
                print("This engine will not provide isolation through gVisor!")
                print("Docker will silently fall back to the default runtime.")
                print("To fix this, please install gVisor by following instructions at:")
                print("https://gvisor.dev/docs/user_guide/install/")
                return False
            else:
                print(f"Error testing gVisor availability: {e}")
                return False
        except Exception as e:
            print(f"Unexpected error checking gVisor availability: {e}")
            return False
    
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
        if not function.container_image:
            raise ValueError("Function does not have a container image")
            
        event_json = json.dumps(event_data)
        
        try:
            runtime_args = {}
            if hasattr(self, 'gvisor_available') and self.gvisor_available:
                print(f"Executing function {function.id} with gVisor runtime (runsc)")
                runtime_args['runtime'] = "runsc-ptrace"
            else:
                print(f"WARNING: Executing function {function.id} with DEFAULT runtime (not gVisor)")
                print("Security isolation provided by gVisor will NOT be available!")
            
            # Use run instead of create+start to execute the function
            # This is the key change
            if function.language == "python":
                cmd = ["python", "-c",f"import json, sys; from function import handler; result = handler(json.loads('{event_json}')); print(json.dumps(result))"]
            else:  # JavaScript
                cmd = ["node", "-e", f"const handler = require('./function').handler; const result = handler(JSON.parse('{event_json}')); console.log(JSON.stringify(result))"]
                
            # Use run() to execute the container and wait for completion
            container = self.client.containers.run(
                image=function.container_image,
                environment={"EVENT_DATA": event_json},
                command=cmd,
                detach=True,  # Run in background so we can monitor it
                **runtime_args
            )
            
            # Monitor for timeout
            import time
            start_time = time.time()
            status = 'running'
            
            while status == 'running' and (time.time() - start_time) < timeout:
                container.reload()
                status = container.status
                time.sleep(0.1)
            
            if status == 'running':
                print(f"Container execution timed out after {timeout} seconds")
                container.stop()
                container.remove()
                raise RuntimeError(f"Function execution timed out after {timeout} seconds")
            
            # Get the logs
            logs = container.logs(stdout=True, stderr=True)
            
            # Clean up
            container.remove()
            
            log_output = logs.decode('utf-8').strip()
            print(f"Function output: {log_output}")
            
            try:
                return json.loads(log_output)
            except json.JSONDecodeError:
                return {"output": log_output}
                
        except docker.errors.ContainerError as e:
            error_message = f"Function execution failed: {str(e)}"
            print(error_message)
            raise RuntimeError(error_message)
            
        except docker.errors.ImageNotFound:
            error_message = "Function image not found"
            print(error_message)
            raise RuntimeError(error_message)
            
        except docker.errors.APIError as e:
            if "Unknown runtime specified" in str(e) or "runtime is not supported" in str(e):
                error_message = f"gVisor runtime error: {str(e)}"
                print("\u26a0\ufe0f ERROR: Docker could not use gVisor (runsc) runtime")
                print("Function execution failed because gVisor is not properly installed")
                print("or configured in Docker. Please install gVisor first.")
            else:
                error_message = f"Docker API error during function execution: {str(e)}"
                print(error_message)
            raise RuntimeError(error_message)
            
        except Exception as e:
            error_message = f"Unexpected error during function execution: {str(e)}"
            print(error_message)
            raise RuntimeError(error_message)