# How to Run the Serverless Function Execution Platform

This guide provides step-by-step instructions to set up and run the serverless function execution platform.

## Prerequisites

1. **Operating System:**
   - Ubuntu 22.04 LTS (recommended) or compatible OS

2. **Required Software:**
   - Docker
   - Python 3.9+
   - Node.js (for JavaScript functions)
   - gVisor runtime (for second virtualization technology)

## Installation Steps

### 1. Install Dependencies

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
# Download and install runsc
wget https://storage.googleapis.com/gvisor/releases/release/latest/x86_64/runsc
chmod +x runsc
sudo mv runsc /usr/local/bin
sudo /usr/local/bin/runsc install
sudo systemctl restart docker
```

### 2. Running the Backend API Server

```bash
# From the project root directory
python backend/app.py
```

The backend API should now be running at: http://localhost:8000

You can verify it's working by accessing:
- Health check: http://localhost:8000/health
- API root: http://localhost:8000/

### 3. Running the Frontend Application

```bash
# From the project root directory
streamlit run frontend/app.py
```

The Streamlit frontend should automatically open in your browser at: http://localhost:8501

If it doesn't open automatically, manually navigate to http://localhost:8501

## Using the Platform

### Creating and Running Functions

1. **Create a Function:**
   - Navigate to the "Create Function" page in the frontend
   - Fill out the function name, route, select a language (Python or JavaScript)
   - Write your function code
   - Click "Create Function"

2. **Execute a Function:**
   - Navigate to the "Functions" page
   - Select your function from the list
   - Click "Execute Function"
   - View the execution results

3. **Monitor Performance:**
   - Navigate to the "Dashboard" page to see system-wide metrics
   - Select individual functions to see their specific metrics

### API Usage

You can also interact with the API directly:

```bash
# Create a function
curl -X POST http://localhost:8000/functions/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hello-world",
    "route": "hello",
    "language": "python",
    "code": "def main(event):\n    name = event.get(\"name\", \"World\")\n    return {\"message\": f\"Hello, {name}!\"}\n",
    "timeout": 30
  }'

# Execute a function (replace <function_id> with actual ID)
curl -X POST http://localhost:8000/functions/<function_id>/execute \
  -H "Content-Type: application/json" \
  -d '{"name": "API User"}'

# Or execute via route
curl -X POST http://localhost:8000/invoke/hello \
  -H "Content-Type: application/json" \
  -d '{"name": "API User"}'
```

## Troubleshooting

### Common Issues

1. **Docker Connection Issues:**
   ```bash
   sudo systemctl status docker
   sudo systemctl restart docker
   ```

2. **Port Conflicts:**
   If ports 8000 or 8501 are already in use:
   ```bash
   # Check if ports are already in use
   sudo lsof -i :8000
   sudo lsof -i :8501
   
   # For backend, modify in backend/app.py, change port number
   # For frontend, use:
   streamlit run frontend/app.py --server.port 8502
   ```

3. **Database Issues:**
   ```bash
   # Remove the database file and let it recreate
   rm backend/db/serverless.db
   ```

4. **Virtualization Issues:**
   ```bash
   # Check Docker status
   docker info
   
   # Check gVisor availability
   docker info | grep runsc
   ```

For more detailed testing instructions, see the `tests.md` file in the project root.
