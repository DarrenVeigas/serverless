# Serverless Function Execution Platform - System Architecture

## Overview

The Serverless Function Execution Platform is designed to allow users to deploy and execute serverless functions using multiple virtualization technologies. The system consists of several components working together to provide function management, execution, and monitoring.

## System Components

### 1. Backend API Server

The backend API server is built with FastAPI and provides endpoints for:
- Function management (create, read, update, delete)
- Function execution
- Metrics collection and retrieval

#### Key Files:
- `backend/app.py`: Main application entry point
- `backend/models/function.py`: Database models for functions and executions
- `backend/routers/functions.py`: API endpoints for function management
- `backend/routers/metrics.py`: API endpoints for metrics retrieval

#### Database Schema:
- `functions`: Stores function metadata (name, route, language, code, timeout)
- `executions`: Stores execution data (execution time, status, virtualization type)

### 2. Execution Engine

The execution engine is responsible for running functions in isolated environments using different virtualization technologies:

- **Docker Execution Engine**: Executes functions in Docker containers
- **gVisor Execution Engine**: Executes functions with additional security isolation using gVisor

#### Key Files:
- `execution_engine/docker_engine.py`: Docker-based execution engine
- `execution_engine/gvisor_engine.py`: gVisor-based execution engine
- `execution_engine/templates/`: Templates for function code and Dockerfiles
- `execution_engine/performance_comparison.py`: Tool for comparing performance between virtualization technologies

### 3. Frontend

The frontend is built with Streamlit and provides a user interface for:
- Function management
- Function testing and execution
- Metrics visualization

#### Key Files:
- `frontend/app.py`: Main application entry point and UI definition

## Data Flow

1. **Function Creation**:
   - User creates a function through the frontend
   - Frontend sends function data to backend API
   - Backend stores function metadata in database
   - Backend builds Docker image for the function

2. **Function Execution**:
   - User executes a function through the frontend
   - Frontend sends execution request to backend API
   - Backend routes request to appropriate function
   - Execution engine runs function in isolated environment
   - Results are returned to user
   - Execution metrics are stored in database

3. **Metrics Collection**:
   - Each function execution generates metrics
   - Metrics are stored in database
   - Metrics are aggregated for dashboard visualization

## Virtualization Technologies

### Docker

Default virtualization technology used for function execution. Provides:
- Container isolation
- Resource limits
- Environment consistency

### gVisor

Secondary virtualization technology that provides:
- Enhanced security isolation
- Additional sandboxing of functions
- Different performance characteristics

## Deployment

The platform can be deployed using Docker Compose, which sets up:
- Backend API container
- Frontend container
- Database container

## Performance Comparison

The platform includes tools for comparing the performance of different virtualization technologies:
- Execution time measurement
- Statistical analysis
- Visualization of performance differences
