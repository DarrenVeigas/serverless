from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import os
import time

from backend.db.database import get_db
from backend.models.function import Function, Execution
from backend.models.schemas import FunctionCreate, Function as FunctionSchema, FunctionWithExecutions

# Import execution engine
from execution_engine.docker_engine import DockerExecutionEngine
from execution_engine.gvisor_engine import GVisorExecutionEngine
from execution_engine.performance_comparison import PerformanceComparison

router = APIRouter(
    prefix="/functions",
    tags=["functions"],
    responses={404: {"description": "Not found"}},
)

# Initialize execution engine
docker_engine = DockerExecutionEngine()
gvisor_engine = GVisorExecutionEngine()
performance_comparison = PerformanceComparison()

@router.post("/", response_model=FunctionSchema, status_code=status.HTTP_201_CREATED)
def create_function(function: FunctionCreate, db: Session = Depends(get_db)):
    """
    Create a new function
    """
    db_function = Function(
        name=function.name,
        route=function.route,
        language=function.language,
        code=function.code,
        timeout=function.timeout,
        virtualization=function.virtualization
    )
    
    db.add(db_function)
    db.commit()
    db.refresh(db_function)
    
    # Build container image for this function
    try:
        # Always build the Docker container image as the base image
        container_image = docker_engine.build_function_image(db_function)
        db_function.container_image = container_image
        db.commit()
        
        # If virtualization preference is gVisor, also build the gVisor image
        if db_function.virtualization == "gvisor":
            try:
                gvisor_image = gvisor_engine.build_function_image(db_function)
                db_function.gvisor_image = gvisor_image
                db.commit()
                print(f"Built gVisor image for function {db_function.id}")
            except Exception as e:
                print(f"Error building gVisor image: {e}")
                # Don't mark function as inactive if only gVisor build fails
        
        # Only warm Docker containers if Docker virtualization is preferred
        if db_function.virtualization == "docker" and db_function.container_image:
            docker_engine._warm_function_containers(db_function)
            
    except Exception as e:
        # If container build fails, we'll still save the function but mark it as inactive
        db_function.is_active = False
        db.commit()
        print(f"Error building container image: {e}")
    
    return db_function

@router.get("/", response_model=List[FunctionSchema])
def get_functions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get all functions
    """
    functions = db.query(Function).offset(skip).limit(limit).all()
    return functions

@router.get("/{function_id}", response_model=FunctionWithExecutions)
def get_function(function_id: int, db: Session = Depends(get_db)):
    """
    Get a specific function by ID
    """
    function = db.query(Function).filter(Function.id == function_id).first()
    if function is None:
        raise HTTPException(status_code=404, detail="Function not found")
    return function

@router.put("/{function_id}", response_model=FunctionSchema)
def update_function(function_id: int, function: FunctionCreate, db: Session = Depends(get_db)):
    """
    Update a function
    """
    db_function = db.query(Function).filter(Function.id == function_id).first()
    if db_function is None:
        raise HTTPException(status_code=404, detail="Function not found")
    
    # Update function attributes
    db_function.name = function.name
    db_function.route = function.route
    db_function.language = function.language
    db_function.code = function.code
    db_function.timeout = function.timeout
    
    # Rebuild container image
    try:
        container_image = docker_engine.build_function_image(db_function)
        db_function.container_image = container_image
        db_function.is_active = True
    except Exception as e:
        # If container build fails, mark function as inactive
        db_function.is_active = False
        print(f"Error rebuilding container image: {e}")
    
    db.commit()
    db.refresh(db_function)
    return db_function

@router.delete("/{function_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_function(function_id: int, db: Session = Depends(get_db)):
    """
    Delete a function
    """
    db_function = db.query(Function).filter(Function.id == function_id).first()
    if db_function is None:
        raise HTTPException(status_code=404, detail="Function not found")
    
    # Remove container image if it exists
    if db_function.container_image:
        try:
            docker_engine.remove_function_image(db_function.container_image)
        except Exception as e:
            print(f"Error removing container image: {e}")
    
    # Delete function from database
    db.delete(db_function)
    db.commit()
    return {"detail": "Function deleted"}

@router.post("/{function_id}/execute", status_code=status.HTTP_200_OK)
def execute_function(function_id: int, request_data: dict = None, db: Session = Depends(get_db)):
    """
    Execute a function and return its result
    """
    if request_data is None:
        request_data = {}
    db_function = db.query(Function).filter(Function.id == function_id).first()
    if db_function is None:
        raise HTTPException(status_code=404, detail="Function not found")
    
    if not db_function.is_active:
        raise HTTPException(status_code=400, detail="Function is not active")
    
    # Record execution start time
    start_time = time.time()
    virtualization = db_function.virtualization if hasattr(db_function, 'virtualization') else "docker"
    
    print(f"Using virtualization from database: {virtualization}")
    try:

        if virtualization == "gvisor":
            # If using gVisor but the function doesn't have a gVisor image yet, build one
            if not db_function.gvisor_image:
                gvisor_image = gvisor_engine.build_function_image(db_function)
                db_function.gvisor_image = gvisor_image
                db.commit()
                
            # Use the gVisor image
            original_image = db_function.container_image
            db_function.container_image = db_function.gvisor_image
            
            # Execute function using gVisor engine
            result = gvisor_engine.execute_function(
                db_function,
                request_data,
                timeout=db_function.timeout
            )
            
            # Restore original image
            db_function.container_image = original_image
        else: 
        # Execute function using Docker engine
            result = docker_engine.execute_function(
                db_function,
                request_data,
                timeout=db_function.timeout
            )
            docker_engine._warm_function_containers(db_function)
        # Record execution end time
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Store execution data
        execution = Execution(
            function_id=function_id,
            start_time=start_time,
            end_time=end_time,
            execution_time=execution_time,
            status="success",
            virtualization=virtualization
        )
        db.add(execution)
        db.commit()
        return result
    except Exception as e:
        # Record execution end time
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Store execution data with error
        execution = Execution(
            function_id=function_id,
            start_time=start_time,
            end_time=end_time,
            execution_time=execution_time,
            status="error",
            error_message=str(e),
            virtualization=virtualization
        )
        db.add(execution)
        db.commit()
        
        raise HTTPException(status_code=500, detail=f"Function execution failed: {str(e)}")


@router.post("/{function_id}/benchmark", status_code=status.HTTP_200_OK)
def benchmark_function(
    function_id: int, 
    request_data: dict = None, 
    iterations: int = 5, 
    db: Session = Depends(get_db)
):
    """
    Benchmark a function using both Docker and gVisor
    Returns performance comparison data
    """
    if request_data is None:
        request_data = {}
    
    db_function = db.query(Function).filter(Function.id == function_id).first()
    if db_function is None:
        raise HTTPException(status_code=404, detail="Function not found")
    
    if not db_function.is_active:
        raise HTTPException(status_code=400, detail="Function is not active")
    
    try:
        # Run benchmark tests
        results = performance_comparison.run_benchmark(db_function, request_data, iterations)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark failed: {str(e)}")
