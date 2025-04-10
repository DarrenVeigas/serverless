# Serverless Function Execution Platform

A platform for executing serverless functions using multiple virtualization technologies.

## Features

- Function management API
- Multiple virtualization technologies (Docker and Firecracker/gVisor)
- Metrics collection and monitoring
- Web-based dashboard
- Function execution with timeout enforcement

## Project Structure

```
serverless/
│
├── backend/            # API server and core logic
├── frontend/           # Web UI for function management
├── execution_engine/   # Function execution components
├── docs/               # Documentation
└── deployment/         # Deployment configurations
```

## Setup Instructions

### Prerequisites

- Ubuntu 22.04 LTS
- Docker
- Node.js (for JavaScript functions)
- Python 3.9+ (for Python functions)

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   cd serverless
   pip install -r requirements.txt
   ```
3. Set up Docker:
   ```
   sudo apt update
   sudo apt install docker.io
   sudo systemctl enable docker
   sudo systemctl start docker
   sudo usermod -aG docker $USER
   ```
4. Start the server:
   ```
   python backend/app.py
   ```

## Getting Started

1. Access the web UI at http://localhost:8080
2. Create a new function through the interface
3. Deploy and test your function

## Development Timeline

- Week 1: Project Setup and Core Infrastructure
- Week 2: Enhanced Execution and Second Virtualization Technology
- Week 3: Frontend, Monitoring Dashboard, and Integration
