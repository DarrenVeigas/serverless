# Serverless Function Execution Platform - Comprehensive Testing Guide

This guide provides detailed instructions on how to test all functionalities of the Serverless Function Execution Platform according to the project requirements in the PDF. It includes first-time setup instructions and testing procedures organized by the weekly implementation plan.

## First-Time Setup

### Prerequisites

1. **Operating System:**
   - Ubuntu 22.04 LTS (recommended)

2. **Required Software:**
   - Docker
   - Python 3.9+
   - Node.js (for JavaScript functions)
   - gVisor runtime (for second virtualization technology)

### Installation and Setup

```bash
# Update package manager
sudo apt update

# Install Python dependencies
pip install -r requirements.txt

# Install Docker (if not already installed)
sudo apt install docker.io
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
# Log out and log back in for group changes to take effect

# Install gVisor (for second virtualization technology)
wget https://storage.googleapis.com/gvisor/releases/release/latest/x86_64/runsc
chmod +x runsc
sudo mv runsc /usr/local/bin
sudo /usr/local/bin/runsc install
sudo systemctl restart docker
```

### Running the Project

1. **Start the Backend API Server:**
   ```bash
   # From the project root directory
   python backend/app.py
   ```
   The backend API should be available at: http://localhost:8000

2. **Start the Frontend Application:**
   ```bash
   # From the project root directory
   streamlit run frontend/app.py
   ```
   The frontend should be available at: http://localhost:8501

## Week 1: Project Setup and Core Infrastructure Tests

### 1. Project Environment Setup Tests

- **Verify Git Repository:**
  ```bash
  git status
  ```
  ✓ Confirm Git repository is properly initialized

- **Verify Project Structure:**
  ```bash
  ls -la
  ```
  ✓ Verify the project has the expected folder structure (backend, frontend, execution_engine, etc.)

- **Verify Dependencies:**
  ```bash
  pip list | grep -E "fastapi|uvicorn|sqlalchemy|docker|streamlit"
  ```
  ✓ Confirm all required dependencies are installed

### 2. Backend API Foundation Tests

- **Test API Health Endpoint:**
  ```bash
  curl http://localhost:8000/health
  ```
  ✓ Expected response: `{"status": "healthy"}`

- **Test API Root Endpoint:**
  ```bash
  curl http://localhost:8000/
  ```
  ✓ Expected response: Welcome message

- **Verify Database Connection:**
  ```bash
  # Check if database file exists
  ls -la backend/db/
  ```
  ✓ Database file should be created automatically when the backend starts

### 3. Function Management CRUD Tests

- **Create a Python Function:**
  ```bash
  curl -X POST http://localhost:8000/functions/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "hello-world-python",
      "route": "hello-python",
      "language": "python",
      "code": "def main(event):\n    name = event.get(\"name\", \"World\")\n    return {\"message\": f\"Hello, {name}!\"}\n",
      "timeout": 30
    }'
  ```
  ✓ Should return JSON with function details including ID

- **Create a JavaScript Function:**
  ```bash
  curl -X POST http://localhost:8000/functions/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "hello-world-js",
      "route": "hello-js",
      "language": "javascript",
      "code": "function main(event) {\n    const name = event.name || \"World\";\n    return {message: `Hello, ${name}!`};\n}\n",
      "timeout": 30
    }'
  ```
  ✓ Should return function details with ID

- **List All Functions:**
  ```bash
  curl http://localhost:8000/functions/
  ```
  ✓ Should return a list of all created functions

- **Get a Specific Function:**
  ```bash
  # Replace <function_id> with actual ID from previous responses
  curl http://localhost:8000/functions/<function_id>
  ```
  ✓ Should return details of the specified function

- **Update a Function:**
  ```bash
  # Replace <function_id> with actual ID
  curl -X PUT http://localhost:8000/functions/<function_id> \
    -H "Content-Type: application/json" \
    -d '{
      "name": "updated-function",
      "route": "updated-route",
      "language": "python",
      "code": "def main(event):\n    name = event.get(\"name\", \"Updated World\")\n    return {\"message\": f\"Updated Hello, {name}!\"}\n",
      "timeout": 60
    }'
  ```
  ✓ Should return updated function details

- **Delete a Function:**
  ```bash
  # Replace <function_id> with actual ID
  curl -X DELETE http://localhost:8000/functions/<function_id>
  ```
  ✓ Should return HTTP 204 No Content or success message

### 4. Docker Virtualization Tests

- **Test Docker Connectivity:**
  ```bash
  docker ps
  ```
  ✓ Should list running Docker containers

- **Execute a Python Function in Docker:**
  ```bash
  # Create a test function if needed
  curl -X POST http://localhost:8000/functions/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "docker-test-python",
      "route": "docker-py",
      "language": "python",
      "code": "def main(event):\n    return {\"message\": \"Running in Docker\", \"data\": event}\n",
      "timeout": 30
    }'
  
  # Get function ID and store it
  FUNCTION_ID=$(curl -s http://localhost:8000/functions/ | grep -o '"id":"[^"]*".*docker-test-python' | cut -d'"' -f4)
  
  # Execute the function
  curl -X POST http://localhost:8000/functions/$FUNCTION_ID/execute \
    -H "Content-Type: application/json" \
    -d '{"test": "Docker Container Test"}'
  ```
  ✓ Should return: `{"message": "Running in Docker", "data": {"test": "Docker Container Test"}}`

- **Test Function Timeout:**
  ```bash
  # Create a function that sleeps longer than its timeout
  curl -X POST http://localhost:8000/functions/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "timeout-test",
      "route": "timeout",
      "language": "python",
      "code": "import time\n\ndef main(event):\n    time.sleep(10)\n    return {\"message\": \"This should not be reached\"}\n",
      "timeout": 5
    }'
  
  # Get function ID
  TIMEOUT_ID=$(curl -s http://localhost:8000/functions/ | grep -o '"id":"[^"]*".*timeout-test' | cut -d'"' -f4)
  
  # Execute the function
  curl -X POST http://localhost:8000/functions/$TIMEOUT_ID/execute
  ```
  ✓ Should return a timeout error message

## Week 2: Enhanced Execution and Second Virtualization Technology Tests

### 1. Execution Engine Improvement Tests

- **Test Request Routing:**
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
  curl -X POST http://localhost:8000/invoke/custom-route \
    -H "Content-Type: application/json" \
    -d '{"test": "route invocation"}'
  ```
  ✓ Should return: `{"message": "Accessed via custom route"}`

- **Test Function Warm-up Mechanism:**
  ```bash
  # Create a test function
  curl -X POST http://localhost:8000/functions/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "warmup-test",
      "route": "warmup",
      "language": "python",
      "code": "def main(event):\n    return {\"message\": \"Testing warm-up\"}\n",
      "timeout": 30
    }'
  
  # Get function ID
  WARMUP_ID=$(curl -s http://localhost:8000/functions/ | grep -o '"id":"[^"]*".*warmup-test' | cut -d'"' -f4)
  
  # Execute once (cold start)
  time curl -X POST http://localhost:8000/functions/$WARMUP_ID/execute
  
  # Execute again (warm start)
  time curl -X POST http://localhost:8000/functions/$WARMUP_ID/execute
  ```
  ✓ Second execution should be faster due to warm-up mechanism

- **Test Container Pool:**
  ```bash
  # Check for warm containers in the pool
  docker ps | grep warmup-test
  ```
  ✓ Should show container(s) for the function in the pool

### 2. Second Virtualization Technology (gVisor) Tests

- **Verify gVisor Installation:**
  ```bash
  docker info | grep runsc
  ```
  ✓ Should show runsc runtime in the output

- **Execute Function Using gVisor:**
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
  
  # Get function ID
  GVISOR_ID=$(curl -s http://localhost:8000/functions/ | grep -o '"id":"[^"]*".*gvisor-test' | cut -d'"' -f4)
  
  # Execute the function
  curl -X POST http://localhost:8000/functions/$GVISOR_ID/execute \
    -H "Content-Type: application/json" \
    -d '{"test": "gVisor Test"}'
  ```
  ✓ Should return: `{"message": "Running in gVisor", "data": {"test": "gVisor Test"}}`

### 3. Performance Comparison Tests

- **Run Performance Comparison:**
  ```bash
  # If there's a specific performance comparison script
  python execution_engine/performance_comparison.py
  
  # Or manually compare performance
  # Create Docker function
  curl -X POST http://localhost:8000/functions/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "perf-docker",
      "route": "perf-docker",
      "language": "python",
      "code": "def main(event):\n    # Some CPU-intensive work\n    result = 0\n    for i in range(1000000):\n        result += i\n    return {\"message\": \"Docker performance test\", \"result\": result}\n",
      "timeout": 30,
      "virtualization": "docker"
    }'
  
  # Create gVisor function (same code)
  curl -X POST http://localhost:8000/functions/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "perf-gvisor",
      "route": "perf-gvisor",
      "language": "python",
      "code": "def main(event):\n    # Some CPU-intensive work\n    result = 0\n    for i in range(1000000):\n        result += i\n    return {\"message\": \"gVisor performance test\", \"result\": result}\n",
      "timeout": 30,
      "virtualization": "gvisor"
    }'
  
  # Get function IDs
  DOCKER_PERF_ID=$(curl -s http://localhost:8000/functions/ | grep -o '"id":"[^"]*".*perf-docker' | cut -d'"' -f4)
  GVISOR_PERF_ID=$(curl -s http://localhost:8000/functions/ | grep -o '"id":"[^"]*".*perf-gvisor' | cut -d'"' -f4)
  
  # Test Docker performance (5 executions)
  time for i in {1..5}; do curl -s -X POST http://localhost:8000/functions/$DOCKER_PERF_ID/execute > /dev/null; done
  
  # Test gVisor performance (5 executions)
  time for i in {1..5}; do curl -s -X POST http://localhost:8000/functions/$GVISOR_PERF_ID/execute > /dev/null; done
  ```
  ✓ Compare execution times between Docker and gVisor

### 4. Metrics Collection Tests

- **Test Function-specific Metrics:**
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
  
  # Get function ID
  METRICS_ID=$(curl -s http://localhost:8000/functions/ | grep -o '"id":"[^"]*".*metrics-test' | cut -d'"' -f4)
  
  # Execute the function multiple times
  for i in {1..5}; do curl -s -X POST http://localhost:8000/functions/$METRICS_ID/execute > /dev/null; done
  
  # Retrieve metrics for the function
  curl http://localhost:8000/metrics/function/$METRICS_ID
  ```
  ✓ Should return metrics data for the function

- **Test System-wide Metrics:**
  ```bash
  curl http://localhost:8000/metrics/system
  ```
  ✓ Should return system-wide metrics

## Week 3: Frontend, Monitoring Dashboard, and Integration Tests

### 1. Frontend Application Tests

- **Access the Frontend Application:**
  1. Open a browser and navigate to http://localhost:8501
  2. Verify the frontend loads correctly

- **Test Function Creation through UI:**
  1. Navigate to "Create Function" page or section
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
  3. Submit the form
  
  ✓ Function should be created and appear in the function list

- **Test Function Management UI:**
  1. Navigate to the functions list page
  2. View details of a function
  3. Try updating a function
  4. Try deleting a function
  
  ✓ All operations should work correctly

- **Test Function Execution through UI:**
  1. Select a function
  2. Provide input parameters if needed
  3. Execute the function
  
  ✓ Function should execute and display results

### 2. Monitoring Dashboard Tests

- **Access the Dashboard:**
  1. Navigate to the dashboard section of the UI
  2. Verify it loads correctly

- **Test System Metrics Visualization:**
  1. Check if system-wide metrics are displayed
  2. Verify charts and graphs are rendered correctly
  
  ✓ Should show metrics in visual format

- **Test Function-specific Metrics Visualization:**
  1. Select a specific function
  2. View its metrics dashboard
  
  ✓ Should display function-specific metrics with visualizations

### 3. Integration Tests

- **End-to-End Function Lifecycle Test:**
  1. Create a new function through the UI
  2. Execute the function and verify results
  3. View execution metrics for the function
  4. Update the function
  5. Execute again and verify changes
  6. Delete the function
  
  ✓ All steps should work seamlessly together

- **Cross-Virtualization Test:**
  1. Create two identical functions, one using Docker and one using gVisor
  2. Execute both with the same input
  3. Compare results and performance
  
  ✓ Both should return identical results with potential performance differences

## Bonus Features Tests (If Implemented)

### 1. Auto-scaling Tests

- **Test Auto-scaling Functionality:**
  ```bash
  # Create a function for load testing
  curl -X POST http://localhost:8000/functions/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "autoscale-test",
      "route": "autoscale",
      "language": "python",
      "code": "def main(event):\n    import time\n    time.sleep(1)\n    return {\"message\": \"Auto-scaling test\"}\n",
      "timeout": 30
    }'
  
  # Get function ID
  AUTOSCALE_ID=$(curl -s http://localhost:8000/functions/ | grep -o '"id":"[^"]*".*autoscale-test' | cut -d'"' -f4)
  
  # Generate load with many concurrent requests
  for i in {1..30}; do
    curl -X POST http://localhost:8000/functions/$AUTOSCALE_ID/execute &
  done
  
  # Check container count during load
  docker ps | grep autoscale-test | wc -l
  ```
  ✓ Multiple containers should be created to handle the load

### 2. Environment Variables Tests

- **Test Environment Variables Support:**
  ```bash
  # Create a function that uses environment variables
  curl -X POST http://localhost:8000/functions/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "env-vars-test",
      "route": "env-vars",
      "language": "python",
      "code": "import os\n\ndef main(event):\n    return {\"env_var\": os.environ.get(\"TEST_VAR\", \"not found\")}\n",
      "timeout": 30,
      "env_vars": {"TEST_VAR": "test value"}
    }'
  
  # Get function ID
  ENV_VARS_ID=$(curl -s http://localhost:8000/functions/ | grep -o '"id":"[^"]*".*env-vars-test' | cut -d'"' -f4)
  
  # Execute the function
  curl -X POST http://localhost:8000/functions/$ENV_VARS_ID/execute
  ```
  ✓ Should return: `{"env_var": "test value"}`

### 3. Additional Programming Languages Tests

- **Test Additional Language Support:**
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
  
  # Get function ID
  GO_ID=$(curl -s http://localhost:8000/functions/ | grep -o '"id":"[^"]*".*go-test' | cut -d'"' -f4)
  
  # Execute the function
  curl -X POST http://localhost:8000/functions/$GO_ID/execute \
    -H "Content-Type: application/json" \
    -d '{"name": "Go User"}'
  ```
  ✓ Should return appropriate response from Go function

## Project Requirements Verification Checklist

Use this checklist to ensure all required project features are implemented and tested:

### Week 1 Requirements
- [ ] Project environment setup complete
- [ ] Git repository initialized with basic structure and README
- [ ] Basic API server implemented
- [ ] Database schema for function storage created
- [ ] Function metadata storage working
- [ ] CRUD endpoints for function management
- [ ] Docker set up as first virtualization technology
- [ ] Base container images for Python and JavaScript
- [ ] Function packaging mechanism implemented
- [ ] Basic execution engine that runs functions in Docker
- [ ] Timeout enforcement implemented

### Week 2 Requirements
- [ ] Request/response handling and error management
- [ ] Function warm-up mechanism implemented
- [ ] Container pool for improved performance
- [ ] Second virtualization technology (gVisor) implemented
- [ ] Function packaging for second technology
- [ ] Execution engine support for both technologies
- [ ] Performance comparison between virtualization technologies
- [ ] Metrics collection for function execution
- [ ] Storage mechanism for metrics
- [ ] Basic aggregation of metrics

### Week 3 Requirements
- [ ] Frontend application structure created
- [ ] Function deployment interface implemented
- [ ] Function management views (list, create, update, delete)
- [ ] Metrics visualization components
- [ ] Dashboard views for function performance
- [ ] System-wide statistics view
- [ ] All components integrated
- [ ] Authentication/authorization (if implemented)
- [ ] End-to-end testing completed
- [ ] Documentation created

### Bonus Features
- [ ] Auto-scaling based on request load
- [ ] Environment variables support in functions
- [ ] Cost analysis comparing virtualization technologies
- [ ] Support for additional programming languages

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
   
   # If needed, reset the database
   rm backend/db/serverless.db
   ```

4. **Port Conflicts:**
   ```bash
   # Check if ports are already in use
   sudo lsof -i :8000
   sudo lsof -i :8501
   
   # Use different ports if needed
   # For backend, modify in backend/app.py
   # For frontend:
   streamlit run frontend/app.py --server.port 8502
   ```

5. **Permission Issues:**
   ```bash
   # Fix permissions for Docker socket
   sudo chmod 666 /var/run/docker.sock
   ```
