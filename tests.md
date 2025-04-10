# Serverless Function Execution Platform - Testing Guide

This document provides a comprehensive testing plan for the serverless function execution platform, covering all functionalities as outlined in the project requirements.

## Project Setup

### Prerequisites

1. Operating System: Ubuntu 22.04 LTS (recommended) or compatible OS
2. Docker properly installed and running
3. Python 3.9+ installed
4. Node.js installed (for JavaScript functions)
5. gVisor runtime installed for second virtualization technology

### Running the Project

1. **Backend API Server**:
   ```bash
   # From the root directory
   pip install -r requirements.txt
   python backend/app.py
   ```

2. **Frontend Application**:
   ```bash
   # From the root directory
   pip install streamlit
   streamlit run frontend/app.py
   ```

3. **Access the Application**:
   - Backend API: http://localhost:8000
   - Frontend UI: http://localhost:8501

## Test Plan

### Week 1 Component Tests

#### 1. Project Environment Setup

- [ ] Verify Git repository is initialized
  ```bash
  git status
  ```

- [ ] Verify all dependencies are installed
  ```bash
  pip list | grep -E "fastapi|uvicorn|sqlalchemy|docker|streamlit"
  ```

- [ ] Verify project folder structure
  ```bash
  ls -la
  ```

#### 2. Backend API Foundation

- [ ] Test API health endpoint
  ```bash
  curl http://localhost:8000/health
  ```
  Expected result: `{"status": "healthy"}`

- [ ] Test API root endpoint
  ```bash
  curl http://localhost:8000/
  ```
  Expected result: `{"message": "Welcome to the Serverless Function Execution Platform"}`

- [ ] Test database connection
  *This is implicitly tested when the app starts*

#### 3. Function Management CRUD Operations

- [ ] Create a new function (Python)
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
  Expected result: New function JSON with an ID

- [ ] Create a new function (JavaScript)
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

- [ ] List all functions
  ```bash
  curl http://localhost:8000/functions/
  ```
  Expected result: List of created functions

- [ ] Get a specific function
  ```bash
  # Replace <function_id> with actual ID
  curl http://localhost:8000/functions/<function_id>
  ```
  Expected result: Function details

- [ ] Update a function
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
  Expected result: Updated function JSON

- [ ] Delete a function
  ```bash
  # Replace <function_id> with actual ID
  curl -X DELETE http://localhost:8000/functions/<function_id>
  ```
  Expected result: HTTP 204 No Content

#### 4. Docker Virtualization Technology

- [ ] Test Docker connectivity
  ```bash
  docker ps
  ```
  Expected result: List of running containers

- [ ] Execute a Python function in Docker
  ```bash
  # Replace <function_id> with actual ID
  curl -X POST http://localhost:8000/functions/<function_id>/execute \
    -H "Content-Type: application/json" \
    -d '{"name": "Docker Test"}'
  ```
  Expected result: `{"message": "Hello, Docker Test!"}`

- [ ] Execute a JavaScript function in Docker
  ```bash
  # Replace <function_id> with actual ID of JS function
  curl -X POST http://localhost:8000/functions/<function_id>/execute \
    -H "Content-Type: application/json" \
    -d '{"name": "Docker JS Test"}'
  ```
  Expected result: `{"message": "Hello, Docker JS Test!"}`

- [ ] Test timeout enforcement
  ```bash
  # Create a function that sleeps for longer than the timeout
  curl -X POST http://localhost:8000/functions/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "timeout-test",
      "route": "timeout",
      "language": "python",
      "code": "import time\n\ndef main(event):\n    time.sleep(31)\n    return {\"message\": \"Should not reach here\"}\n",
      "timeout": 5
    }'
  
  # Then execute it
  # Replace <function_id> with actual ID
  curl -X POST http://localhost:8000/functions/<function_id>/execute
  ```
  Expected result: Timeout error

### Week 2 Component Tests

#### 1. Enhanced Execution Engine

- [ ] Test function warm-up mechanism
  *This is an internal mechanism, but we can test warm start execution time*
  
  ```bash
  # Execute a function twice to see if the second execution is faster (warm start)
  # Replace <function_id> with actual ID
  time curl -X POST http://localhost:8000/functions/<function_id>/execute
  time curl -X POST http://localhost:8000/functions/<function_id>/execute
  ```
  Expected result: Second execution should be faster

- [ ] Test container pool functionality
  *This is also an internal mechanism but can be validated through Docker*
  
  ```bash
  # Create a function and check if warm containers are created
  # Replace <function_name> with actual function name
  docker ps | grep <function_name>
  ```
  Expected result: Should see containers in the pool

- [ ] Test request routing to appropriate function
  ```bash
  # Execute a function via its route
  curl -X POST http://localhost:8000/invoke/hello-python \
    -H "Content-Type: application/json" \
    -d '{"name": "Route Test"}'
  ```
  Expected result: Function result

#### 2. gVisor Virtualization Technology

- [ ] Test gVisor runtime installation
  ```bash
  docker info | grep runsc
  ```
  Expected result: Should show runsc runtime

- [ ] Execute function using gVisor
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
  
  # Execute it
  # Replace <function_id> with actual ID
  curl -X POST http://localhost:8000/functions/<function_id>/execute \
    -H "Content-Type: application/json" \
    -d '{"test": "gVisor Test"}'
  ```
  Expected result: `{"message": "Running in gVisor", "data": {"test": "gVisor Test"}}`

#### 3. Performance Comparison

- [ ] Run the performance comparison script
  ```bash
  python execution_engine/performance_comparison.py
  ```
  Expected result: Performance metrics for Docker vs gVisor

#### 4. Metrics Collection

- [ ] Test metrics storage for a function
  ```bash
  # Execute a function multiple times
  # Replace <function_id> with actual ID
  curl -X POST http://localhost:8000/functions/<function_id>/execute
  curl -X POST http://localhost:8000/functions/<function_id>/execute
  curl -X POST http://localhost:8000/functions/<function_id>/execute
  
  # Then fetch metrics
  curl http://localhost:8000/metrics/function/<function_id>
  ```
  Expected result: Execution metrics for the function

- [ ] Test system-wide metrics
  ```bash
  curl http://localhost:8000/metrics/system
  ```
  Expected result: System-wide metrics including total executions, avg response time, etc.

### Week 3 Component Tests

#### 1. Frontend Application

- [ ] Test the frontend application launch
  ```bash
  streamlit run frontend/app.py
  ```
  Expected result: Streamlit application runs and opens in browser

- [ ] Test function creation through UI
  1. Navigate to "Create Function" page
  2. Fill out the form with a new function
  3. Click "Create Function"
  
  Expected result: New function created and success message shown

- [ ] Test function listing and details
  1. Navigate to "Functions" page
  2. Verify functions are listed
  3. Select a function to view details
  
  Expected result: Function details shown including code and metrics

- [ ] Test function execution through UI
  1. Select a function
  2. Click "Execute Function"
  
  Expected result: Function executes and results are shown

#### 2. Monitoring Dashboard

- [ ] Test system dashboard
  1. Navigate to "Dashboard" page
  2. Check system-wide metrics
  
  Expected result: Dashboard shows total functions, executions, and other metrics

- [ ] Test function metrics visualization
  1. Select a function
  2. View the metrics section
  
  Expected result: Charts showing function execution metrics

#### 3. End-to-End Integration Tests

- [ ] Create a function through the UI
- [ ] Execute the function through the UI
- [ ] View metrics for the function
- [ ] Update the function code
- [ ] Execute again and verify changes
- [ ] Test with both virtualization technologies

### Bonus Features Tests (if implemented)

#### 1. Auto-scaling

- [ ] Test auto-scaling functionality
  *Create a load generator to execute many functions simultaneously*
  
  ```bash
  # Example with a simple bash loop
  for i in {1..50}; do
    curl -X POST http://localhost:8000/functions/<function_id>/execute &
  done
  ```
  Expected result: Container count should increase

#### 2. Environment Variables

- [ ] Test environment variable support
  ```bash
  # Create a function that uses environment variables
  curl -X POST http://localhost:8000/functions/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "env-test",
      "route": "env",
      "language": "python",
      "code": "import os\n\ndef main(event):\n    return {\"env_var\": os.environ.get(\"TEST_VAR\", \"not found\")}\n",
      "timeout": 30,
      "env_vars": {"TEST_VAR": "test value"}
    }'
  
  # Execute it
  # Replace <function_id> with actual ID
  curl -X POST http://localhost:8000/functions/<function_id>/execute
  ```
  Expected result: `{"env_var": "test value"}`

#### 3. Additional Languages

- [ ] Test additional programming languages (if implemented)
  ```bash
  # Example for Go
  curl -X POST http://localhost:8000/functions/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "go-test",
      "route": "go",
      "language": "go",
      "code": "package main\n\nimport (\n  \"encoding/json\"\n  \"fmt\"\n  \"os\"\n)\n\nfunc main() {\n  var event map[string]interface{}\n  json.NewDecoder(os.Stdin).Decode(&event)\n  name, ok := event[\"name\"].(string)\n  if !ok {\n    name = \"World\"\n  }\n  fmt.Printf(\"{\\\"message\\\": \\\"Hello, %s!\\\"}\", name)\n}\n",
      "timeout": 30
    }'
  
  # Execute it
  # Replace <function_id> with actual ID
  curl -X POST http://localhost:8000/functions/<function_id>/execute \
    -H "Content-Type: application/json" \
    -d '{"name": "Go Test"}'
  ```
  Expected result: `{"message": "Hello, Go Test!"}`

## Troubleshooting

### Common Issues and Solutions

1. **Docker Connection Issues**
   ```bash
   sudo systemctl status docker
   sudo systemctl restart docker
   sudo usermod -aG docker $USER && newgrp docker
   ```

2. **gVisor Runtime Issues**
   ```bash
   sudo runsc install
   sudo systemctl restart docker
   ```

3. **Database Connection Issues**
   ```bash
   # Check if database file exists
   ls -la backend/db/
   ```

4. **Port Conflicts**
   ```bash
   # Check if ports are already in use
   sudo lsof -i :8000
   sudo lsof -i :8501
   ```

## Project Requirements Validation Checklist

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
