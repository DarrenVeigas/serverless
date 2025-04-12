# Serverless Function Execution Platform - Complete Testing Guide

This guide provides comprehensive instructions on how to test each functionality of the Serverless Function Execution Platform as specified in the project requirements document. It is organized by week to match the project implementation plan.

## First-Time Setup Instructions

Before testing, you need to set up the project environment:

### Prerequisites

1. **Operating System:** Ubuntu 22.04 LTS (recommended)
2. **Required Software:**
   - Docker
   - Python 3.9+
   - Node.js (for JavaScript functions)
   - gVisor runtime (for second virtualization technology)

### Installation Steps

```bash
# Update package manager
sudo apt update

# Install project dependencies
pip install -r requirements.txt

# Install Docker (if needed)
sudo apt install docker.io
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
# Log out and log back in

# Install gVisor
wget https://storage.googleapis.com/gvisor/releases/release/latest/x86_64/runsc
chmod +x runsc
sudo mv runsc /usr/local/bin
sudo /usr/local/bin/runsc install
sudo systemctl restart docker
```

### Running the Project

1. **Start Backend API Server:**
   ```bash
   # From the project root directory
   python backend/app.py
   ```
   The API will be available at http://localhost:8000

2. **Start Frontend Application:**
   ```bash
   # From the project root directory
   streamlit run frontend/app.py
   ```
   The frontend will be available at http://localhost:8501

## Week 1: Project Setup and Core Infrastructure Testing

### 1. Project Setup and Environment Verification

- **Git Repository:**
  ```bash
  git status
  ```
  ✓ Verify the project has Git version control properly initialized

- **Project Structure:**
  ```bash
  ls -la
  ```
  ✓ Confirm the project structure matches the expected layout
  
- **Dependencies:**
  ```bash
  pip list | grep -E "fastapi|uvicorn|sqlalchemy|docker|streamlit"
  ```
  ✓ Verify all required dependencies are installed

### 2. Backend API Foundation Testing

- **API Health Check:**
  ```bash
  curl http://localhost:8000/health
  ```
  ✓ Expected: `{"status": "healthy"}`

- **API Welcome Endpoint:**
  ```bash
  curl http://localhost:8000/
  ```
  ✓ Expected: Welcome message

- **Database Connection:**
  ✓ This is implicitly tested when the backend starts successfully
  ✓ Check if the database file is created in backend/db/

### 3. Function Metadata Storage Testing

- **Create Function (Python):**
  ```bash
  curl -X POST http://localhost:8000/functions/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "test-python-function",
      "route": "test-python",
      "language": "python",
      "code": "def main(event):\n    return {\"message\": \"Hello from Python!\", \"input\": event}\n",
      "timeout": 30
    }'
  ```
  ✓ Expected: JSON response with function details including ID

- **Create Function (JavaScript):**
  ```bash
  curl -X POST http://localhost:8000/functions/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "test-js-function",
      "route": "test-js",
      "language": "javascript",
      "code": "function main(event) {\n    return {message: \"Hello from JavaScript!\", input: event};\n}\n",
      "timeout": 30
    }'
  ```
  ✓ Expected: JSON response with function details including ID

- **Retrieve Function List:**
  ```bash
  curl http://localhost:8000/functions/
  ```
  ✓ Expected: List of all created functions

- **Retrieve Specific Function:**
  ```bash
  # Replace <function_id> with actual ID
  curl http://localhost:8000/functions/<function_id>
  ```
  ✓ Expected: Details of the specified function

- **Update Function:**
  ```bash
  # Replace <function_id> with actual ID
  curl -X PUT http://localhost:8000/functions/<function_id> \
    -H "Content-Type: application/json" \
    -d '{
      "name": "updated-function",
      "route": "updated-route",
      "language": "python",
      "code": "def main(event):\n    return {\"message\": \"Updated function!\", \"input\": event}\n",
      "timeout": 45
    }'
  ```
  ✓ Expected: Updated function details

- **Delete Function:**
  ```bash
  # Replace <function_id> with actual ID
  curl -X DELETE http://localhost:8000/functions/<function_id>
  ```
  ✓ Expected: HTTP 204 No Content or success message

### 4. Docker Virtualization Testing

- **Docker Connectivity:**
  ```bash
  docker ps
  ```
  ✓ Expected: List of running containers

- **Function Execution in Docker:**
  ```bash
  # Create a test function
  curl -X POST http://localhost:8000/functions/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "docker-test",
      "route": "docker-test",
      "language": "python",
      "code": "def main(event):\n    name = event.get(\"name\", \"Docker\")\n    return {\"message\": f\"Hello, {name} from Docker container!\"}\n",
      "timeout": 30
    }'
  
  # Store the function ID
  FUNCTION_ID=$(curl -s http://localhost:8000/functions/ | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
  
  # Execute the function
  curl -X POST http://localhost:8000/functions/$FUNCTION_ID/execute \
    -H "Content-Type: application/json" \
    -d '{"name": "Tester"}'
  ```
  ✓ Expected: `{"message": "Hello, Tester from Docker container!"}`

- **Function Timeout Testing:**
  ```bash
  # Create a function that sleeps longer than its timeout
  curl -X POST http://localhost:8000/functions/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "timeout-test",
      "route": "timeout",
      "language": "python",
      "code": "import time\n\ndef main(event):\n    time.sleep(10)\n    return {\"message\": \"This should time out\"}\n",
      "timeout": 5
    }'
  
  # Get the function ID
  TIMEOUT_FUNCTION_ID=$(curl -s http://localhost:8000/functions/ | grep -o '"id":"[^"]*".*timeout-test' | cut -d'"' -f4)
  
  # Execute the function
  curl -X POST http://localhost:8000/functions/$TIMEOUT_FUNCTION_ID/execute
  ```
  ✓ Expected: Timeout error response

## Week 2: Enhanced Execution and Second Virtualization Technology Testing

### 1. Execution Engine Improvements Testing

- **Request Routing Testing:**
  ```bash
  # Create a function with a specific route
  curl -X POST http://localhost:8000/functions/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "route-test",
      "route": "custom-route",
      "language": "python",
      "code": "def main(event):\n    return {\"message\": \"Accessed via custom route\"}\n",
      "timeout": 30
    }'
  
  # Execute via the route instead of function ID
  curl -X POST http://localhost:8000/invoke/custom-route
  ```
  ✓ Expected: `{"message": "Accessed via custom route"}`

- **Warm-up Mechanism Testing:**
  ```bash
  # Create a test function
  curl -X POST http://localhost:8000/functions/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "hello_world",
      "route": "test",
      "language": "python",
      "code": "def main(event):\n    name = event.get(\"name\", \"World\")\n    return {\"message\": f\"Hello, {name}!\", \"received_event\": event}",
      "timeout": 30
    }'

    curl -X POST http://localhost:8000/functions/1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User"
  }'

    # Execute multiple times to verify warm container reuse
  for i in {1..5}; do
    echo "Request $i:"
    time curl -X POST http://localhost:8000/functions/1/execute \
      -H "Content-Type: application/json" \
      -d '{"name": "Test User", "iteration": '"$i"'}'
    echo -e "\n"
    sleep 1
  done


- **Container Pool Testing:**
  ```bash
  # Create a function that will use the container pool
  curl -X POST http://localhost:8000/functions/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "pool-test",
      "route": "pool",
      "language": "python",
      "code": "def main(event):\n    return {\"message\": \"Container pool function\"}\n",
      "timeout": 30
    }'
  
  # Check for warm containers in the pool
  docker ps | grep pool-test
  ```
  ✓ Expected: Should see at least one warm container

### 2. Second Virtualization Technology (gVisor) Testing

- **gVisor Runtime Verification:**
  ```bash
  docker info | grep runsc
  ```
  ✓ Expected: runsc runtime should be listed

- **gVisor Function Execution:**
  ```bash
  # Create a function specifically for gVisor
  curl -X POST http://localhost:8000/functions/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "gvisor-test",
      "route": "gvisor",
      "language": "python",
      "code": "def main(event):\n    return {\"message\": \"Running in gVisor\", \"data\": event}\n",
      "timeout": 30,
      "virtualization": "gvisor"
    }'
  
  # Get the function ID
  GVISOR_FUNCTION_ID=$(curl -s http://localhost:8000/functions/ | grep -o '"id":"[^"]*".*gvisor-test' | cut -d'"' -f4)
  
  # Execute the function
  curl -X POST http://localhost:8000/functions/$GVISOR_FUNCTION_ID/execute \
    -H "Content-Type: application/json" \
    -d '{"test": "gVisor execution"}'
  ```
  ✓ Expected: `{"message": "Running in gVisor", "data": {"test": "gVisor execution"}}`

### 3. Performance Comparison Testing

- **Run Performance Comparison:**
  ```bash
  # If there's a script
  python execution_engine/performance_comparison.py
  
  # Or manually create functions with both virtualization types and compare
  # Create Docker function
  curl -X POST http://localhost:8000/functions/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "perf-docker",
      "route": "perf-docker",
      "language": "python",
      "code": "def main(event):\n    return {\"message\": \"Docker performance test\"}\n",
      "timeout": 30,
      "virtualization": "docker"
    }'
  
  # Create gVisor function
  curl -X POST http://localhost:8000/functions/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "perf-gvisor",
      "route": "perf-gvisor",
      "language": "python",
      "code": "def main(event):\n    return {\"message\": \"gVisor performance test\"}\n",
      "timeout": 30,
      "virtualization": "gvisor"
    }'
  
  # Get function IDs
  DOCKER_FUNCTION_ID=$(curl -s http://localhost:8000/functions/ | grep -o '"id":"[^"]*".*perf-docker' | cut -d'"' -f4)
  GVISOR_FUNCTION_ID=$(curl -s http://localhost:8000/functions/ | grep -o '"id":"[^"]*".*perf-gvisor' | cut -d'"' -f4)
  
  # Test Docker performance (multiple executions)
  time for i in {1..5}; do curl -s -X POST http://localhost:8000/functions/$DOCKER_FUNCTION_ID/execute > /dev/null; done
  
  # Test gVisor performance (multiple executions)
  time for i in {1..5}; do curl -s -X POST http://localhost:8000/functions/$GVISOR_FUNCTION_ID/execute > /dev/null; done
  ```
  ✓ Expected: Performance metrics for both virtualization technologies

### 4. Metrics Collection Testing

- **Check Function Metrics:**
  ```bash
  # Create a function for metrics testing
  curl -X POST http://localhost:8000/functions/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "metrics-test",
      "route": "metrics",
      "language": "python",
      "code": "def main(event):\n    return {\"message\": \"Testing metrics collection\"}\n",
      "timeout": 30
    }'
  
  # Get the function ID
  METRICS_FUNCTION_ID=$(curl -s http://localhost:8000/functions/ | grep -o '"id":"[^"]*".*metrics-test' | cut -d'"' -f4)
  
  # Execute the function multiple times
  for i in {1..5}; do curl -s -X POST http://localhost:8000/functions/$METRICS_FUNCTION_ID/execute > /dev/null; done
  
  # Retrieve metrics for the function
  curl http://localhost:8000/metrics/function/$METRICS_FUNCTION_ID
  ```
  ✓ Expected: Metrics data including execution count, average response time, etc.

- **Check System-wide Metrics:**
  ```bash
  curl http://localhost:8000/metrics/system
  ```
  ✓ Expected: System-wide metrics including total executions, system load, etc.

## Week 3: Frontend, Monitoring Dashboard, and Integration Testing

### 1. Frontend Application Testing

- **Frontend Access Verification:**
  1. Navigate to http://localhost:8501 in your browser
  2. Verify the application loads correctly

- **Function Creation through UI:**
  1. Navigate to "Create Function" page
  2. Fill out the form with:
     - Name: "ui-test-function"
     - Route: "ui-test"
     - Language: Python
     - Code: 
       ```python
       def main(event):
           return {"message": "Created via UI", "data": event}
       ```
     - Timeout: 30 seconds
  3. Click "Create Function"
  
  ✓ Expected: Success message and function appears in function list

- **Function Management Testing:**
  1. Navigate to "Functions" page
  2. Verify the list includes previously created functions
  3. Select a function to view details
  4. Try to update a function
  5. Try to delete a function
  
  ✓ Expected: All management operations work correctly

- **Function Execution through UI:**
  1. Select a function from the list
  2. Click "Execute Function"
  3. Provide input parameters if needed
  
  ✓ Expected: Function executes and results are displayed

### 2. Monitoring Dashboard Testing

- **Dashboard Access:**
  1. Navigate to "Dashboard" or metrics page in the UI
  2. Verify the dashboard loads correctly

- **System-wide Metrics Visualization:**
  1. Check if system metrics are displayed
  2. Verify charts and graphs render correctly
  
  ✓ Expected: Visual representation of system metrics

- **Individual Function Metrics:**
  1. Select a specific function
  2. View its metrics dashboard
  
  ✓ Expected: Function-specific metrics displayed with charts

### 3. Integration Testing

- **End-to-End Function Lifecycle:**
  1. Create a new function through the UI
  2. Execute the function through the UI
  3. View execution metrics for the function
  4. Update the function code
  5. Execute again and verify changes
  6. Delete the function
  
  ✓ Expected: Complete lifecycle works seamlessly

- **Virtualization Technology Comparison:**
  1. Create two identical functions, one using Docker and one using gVisor
  2. Execute both functions with the same input
  3. Compare execution metrics
  
  ✓ Expected: Performance differences should be visible in metrics

- **Documentation Verification:**
  1. Check that all API endpoints are documented
  2. Verify user guides are complete
  
  ✓ Expected: Complete documentation available

## Bonus Features Testing (if implemented)

### 1. Auto-scaling Testing

- **Load Testing for Auto-scaling:**
  ```bash
  # Create a function for load testing
  curl -X POST http://localhost:8000/functions/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "load-test",
      "route": "load",
      "language": "python",
      "code": "def main(event):\n    return {\"message\": \"Auto-scaling test\"}\n",
      "timeout": 30
    }'
  
  # Get the function ID
  LOAD_FUNCTION_ID=$(curl -s http://localhost:8000/functions/ | grep -o '"id":"[^"]*".*load-test' | cut -d'"' -f4)
  
  # Execute many concurrent requests
  for i in {1..50}; do
    curl -X POST http://localhost:8000/functions/$LOAD_FUNCTION_ID/execute &
  done
  
  # Check container count
  docker ps | grep load-test | wc -l
  ```
  ✓ Expected: Multiple containers should be created to handle the load

### 2. Environment Variables Testing

- **Function with Environment Variables:**
  ```bash
  # Create a function that uses environment variables
  curl -X POST http://localhost:8000/functions/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "env-var-test",
      "route": "env-var",
      "language": "python",
      "code": "import os\n\ndef main(event):\n    return {\"env_var\": os.environ.get(\"TEST_VAR\", \"not found\")}\n",
      "timeout": 30,
      "env_vars": {"TEST_VAR": "environment variable value"}
    }'
  
  # Get the function ID
  ENV_FUNCTION_ID=$(curl -s http://localhost:8000/functions/ | grep -o '"id":"[^"]*".*env-var-test' | cut -d'"' -f4)
  
  # Execute the function
  curl -X POST http://localhost:8000/functions/$ENV_FUNCTION_ID/execute
  ```
  ✓ Expected: `{"env_var": "environment variable value"}`

### 3. Additional Programming Languages Testing

- **Testing Additional Language Support:**
  ```bash
  # Example for Go (if implemented)
  curl -X POST http://localhost:8000/functions/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "go-test",
      "route": "go",
      "language": "go",
      "code": "package main\n\nimport (\n  \"encoding/json\"\n  \"fmt\"\n  \"os\"\n)\n\nfunc main() {\n  var event map[string]interface{}\n  json.NewDecoder(os.Stdin).Decode(&event)\n  name, ok := event[\"name\"].(string)\n  if !ok {\n    name = \"World\"\n  }\n  fmt.Printf(\"{\\\"message\\\": \\\"Hello from Go, %s!\\\"}\", name)\n}\n",
      "timeout": 30
    }'
  
  # Get the function ID
  GO_FUNCTION_ID=$(curl -s http://localhost:8000/functions/ | grep -o '"id":"[^"]*".*go-test' | cut -d'"' -f4)
  
  # Execute the function
  curl -X POST http://localhost:8000/functions/$GO_FUNCTION_ID/execute \
    -H "Content-Type: application/json" \
    -d '{"name": "Go Developer"}'
  ```
  ✓ Expected: `{"message": "Hello from Go, Go Developer!"}`

## Troubleshooting

### Common Issues and Solutions

1. **Docker Connection Issues:**
   ```bash
   sudo systemctl status docker
   sudo systemctl restart docker
   sudo usermod -aG docker $USER && newgrp docker
   ```

2. **gVisor Runtime Issues:**
   ```bash
   sudo runsc install
   sudo systemctl restart docker
   ```

3. **Database Connection Issues:**
   ```bash
   # Check if database file exists
   ls -la backend/db/
   
   # If needed, remove and let system recreate it
   rm backend/db/serverless.db
   ```

4. **Port Conflicts:**
   ```bash
   # Check if ports are already in use
   sudo lsof -i :8000
   sudo lsof -i :8501
   
   # Modify ports in configuration if needed
   ```

## Feature Checklist

Use this checklist to ensure all required project features are implemented and tested:

### Week 1
- [ ] Project environment setup complete
- [ ] Basic API server implemented
- [ ] Function metadata storage working
- [ ] CRUD endpoints for function management
- [ ] Docker set up as first virtualization technology
- [ ] Function execution in Docker containers
- [ ] Timeout enforcement implemented

### Week 2
- [ ] Request routing working
- [ ] Function warm-up mechanism implemented
- [ ] Container pool for improved performance
- [ ] Second virtualization technology (gVisor) implemented
- [ ] Performance comparison between virtualization technologies
- [ ] Metrics collection for function execution

### Week 3
- [ ] Frontend application implemented
- [ ] Function deployment interface working
- [ ] Function management views implemented
- [ ] Metrics visualization components working
- [ ] Dashboard displays metrics and statistics
- [ ] All components integrated successfully
- [ ] Documentation completed

### Bonus Features
- [ ] Auto-scaling based on request load
- [ ] Environment variables support in functions
- [ ] Cost analysis comparing virtualization technologies
- [ ] Support for additional programming languages
