import docker
import tempfile
import os
import json
import time
import uuid
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

class DockerExecutionEngine:
    """
    Docker-based execution engine for serverless functions
    """
    def __init__(self):
        """
        Initialize the Docker client and create a pool of containers
        """
        self.client = docker.from_env()
        # Changed structure: Map of function_id to dict of container details including creation time
        self.container_pool = {}  # {function_id: [{"id": container_id, "created": timestamp}, ...]}
        self.pool_size = 3  # Number of warm containers to keep per function
        self.base_path = Path(__file__).parent
        self.container_max_age = 3600  # Max age in seconds (1 hour) before recycling a container
        
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
    
    def _recycle_old_containers(self, function_id):
        """
        Remove containers that are too old from the pool
        """
        if function_id not in self.container_pool:
            return
        
        current_time = time.time()
        containers_to_keep = []
        
        for container_info in self.container_pool[function_id]:
            container_id = container_info["id"]
            creation_time = container_info["created"]
            
            if current_time - creation_time > self.container_max_age:
                # Container is too old, remove it
                try:
                    container = self.client.containers.get(container_id)
                    container.remove(force=True)
                    print(f"Recycled old container {container_id[:12]} for function {function_id}")
                except Exception as e:
                    print(f"Error removing old container {container_id[:12]}: {e}")
            else:
                # Container is still fresh, keep it
                containers_to_keep.append(container_info)
        
        self.container_pool[function_id] = containers_to_keep
    
    def _warm_function_containers(self, function):
        """
        Create warm containers for a function that are properly initialized
        """
        if function.id not in self.container_pool:
            self.container_pool[function.id] = []
        
        # First, recycle any old containers
        self._recycle_old_containers(function.id)
        
        # Check how many containers we need to create
        num_to_create = self.pool_size - len(self.container_pool[function.id])
        
        if num_to_create <= 0:
            return
        
        # Create containers
        for _ in range(num_to_create):
            try:
                # Create container with proper initialization
                # Instead of sleep infinity, we use a command that keeps it running
                # but in a state ready for function execution
                container = self.client.containers.run(
                    image=function.container_image,
                    detach=True,
                    stdin_open=True,  # Keep STDIN open
                    tty=True,         # Allocate a pseudo-TTY
                    command="tail -f /dev/null"  # Keep container running but ready for exec
                )
                
                # Store container with creation timestamp
                self.container_pool[function.id].append({
                    "id": container.id,
                    "created": time.time()
                })
                print(f"Created warm container {container.id[:12]} for function {function.id}")
            except Exception as e:
                print(f"Error creating warm container for function {function.id}: {e}")
    
    def _get_container(self, function):
        """
        Get a container for the function from the pool or create a new one
        """
        if function.id in self.container_pool and self.container_pool[function.id]:
            # Get a container from the pool
            container_info = self.container_pool[function.id].pop(0)
            container_id = container_info["id"]
            
            try:
                # Make sure the container is actually running
                container = self.client.containers.get(container_id)
                if container.status != "running":
                    # If not running, try to restart it
                    container.start()
                    time.sleep(0.5)  # Brief pause to ensure container is ready
                
                print(f"Reusing warm container {container_id[:12]} for function {function.id}")
                return container
            except Exception as e:
                print(f"Error getting container {container_id[:12]} from pool: {e}")
        
        # If we couldn't get a container from the pool, create a new one
        print(f"Creating new container for function {function.id}")
        container = self.client.containers.create(
            image=function.container_image,
            detach=True,
            stdin_open=True,
            tty=False
        )
        return container
    
    def _return_container_to_pool(self, container, function_id):
        """
        Return a container to the pool after use if it's still in good condition
        """
        try:
            # Check if the container is still running
            container.reload()
            if container.status == "running":
                # If the pool for this function doesn't exist, create it
                if function_id not in self.container_pool:
                    self.container_pool[function_id] = []
                
                # If the pool isn't full, add this container back
                if len(self.container_pool[function_id]) < self.pool_size:
                    self.container_pool[function_id].append({
                        "id": container.id,
                        "created": time.time()  # Reset the creation time when returning to pool
                    })
                    print(f"Returned container {container.id[:12]} to pool for function {function_id}")
                    return True
                else:
                    # Pool is full, remove this container
                    container.remove(force=True)
                    print(f"Pool full for function {function_id}, removed container {container.id[:12]}")
            else:
                # Container isn't running, remove it
                container.remove(force=True)
                print(f"Container {container.id[:12]} not running, removed")
        except Exception as e:
            print(f"Error returning container {container.id} to pool: {e}")
            try:
                container.remove(force=True)
            except:
                pass
        
        return False
    
    def execute_function(self, function, event_data, timeout=30):
        """
        Execute a function with the given event data using a container from the pool
        """
        # Ensure we have a container image
        if not function.container_image:
            raise ValueError("Function does not have a container image")
        
        # Convert event data to JSON and escape it properly for shell commands
        event_json = json.dumps(event_data).replace("'", "\\'") 
        
        # Get a container from the pool or create a new one
        try:
            container = self._get_container(function)
            print(f"Using container {container.id[:12]} for function {function.id}")
        except Exception as e:
            print(f"Error getting container: {e}")
            raise
        
        try:
            # Make sure the container is running
            container.reload()  # Refresh container status
            if container.status != "running":
                container.start()
                time.sleep(0.5)  # Brief pause to ensure container is ready
                print(f"Started container {container.id[:12]}")
            
            # Prepare the execution command based on language
            cmd = []
            if function.language == "python":
                cmd = ["python", "-c", f"import json, sys; from function import handler; result = handler(json.loads('{event_json}')); print(json.dumps(result))"] 
            elif function.language == "javascript":
                cmd = ["node", "-e", f"const handler = require('./function').handler; const result = handler(JSON.parse('{event_json}')); console.log(JSON.stringify(result))"]
            else:
                raise ValueError(f"Unsupported language: {function.language}")
            
            print(f"Executing command in container: {cmd}")
            
            # Execute the function in the container
            exec_result = container.exec_run(
                cmd=cmd,
                stdout=True,
                stderr=True
            )
            
            # Get execution result
            exit_code = exec_result.exit_code
            output = exec_result.output.decode('utf-8')
            
            # Check execution exit code
            if exit_code != 0:
                raise RuntimeError(f"Function execution failed with exit code {exit_code}: {output}")
            
            # Clean the output (remove any extra whitespace/newlines)
            output = output.strip()
            
            # Try to parse the result as JSON
            try:
                parsed_result = json.loads(output)
                # Return container to pool for reuse
                self._return_container_to_pool(container, function.id)
                return parsed_result
            except json.JSONDecodeError:
                # Return container to pool for reuse
                self._return_container_to_pool(container, function.id)
                return {"output": output}
                
        except TimeoutError as te:
            # For timeout errors, we can try to reuse the container after cleaning up
            print(f"Timeout during function execution: {str(te)}")
            # Don't return to pool - container may be stuck
            try:
                container.remove(force=True)
            except Exception as rm_err:
                print(f"Error removing timed-out container: {rm_err}")
            raise
            
        except Exception as e:
            # On error, don't return the container to the pool
            print(f"Error during execution: {str(e)}")
            try:
                container.remove(force=True)
            except Exception as rm_err:
                print(f"Error removing failed container: {rm_err}")
            raise RuntimeError(f"Error during function execution: {str(e)}")
        
    def shutdown(self):
        """
        Cleanup all resources when shutting down
        """
        print("Shutting down Docker execution engine...")
        for function_id, containers in self.container_pool.items():
            for container_info in containers:
                try:
                    container = self.client.containers.get(container_info["id"])
                    container.remove(force=True)
                    print(f"Removed container {container_info['id'][:12]}")
                except Exception as e:
                    print(f"Error removing container {container_info['id'][:12]}: {e}")
        
        # Clear the container pool
        self.container_pool = {}
        print("Docker execution engine shutdown complete")