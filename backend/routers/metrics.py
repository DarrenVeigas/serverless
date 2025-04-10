from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
import time
from typing import List, Dict

from backend.db.database import get_db
from backend.models.function import Function, Execution

router = APIRouter(
    prefix="/metrics",
    tags=["metrics"],
    responses={404: {"description": "Not found"}},
)

@router.get("/function/{function_id}")
def get_function_metrics(function_id: int, db: Session = Depends(get_db)):
    """
    Get metrics for a specific function
    """
    # Check if function exists
    function = db.query(Function).filter(Function.id == function_id).first()
    if function is None:
        raise HTTPException(status_code=404, detail="Function not found")
    
    # Get execution metrics
    executions = db.query(Execution).filter(Execution.function_id == function_id).all()
    
    if not executions:
        return {
            "function_name": function.name,
            "total_executions": 0,
            "avg_execution_time": 0,
            "success_rate": 0,
            "recent_executions": []
        }
    
    # Calculate metrics
    total_executions = len(executions)
    successful_executions = len([e for e in executions if e.status == "success"])
    success_rate = (successful_executions / total_executions) * 100 if total_executions > 0 else 0
    avg_execution_time = sum(e.execution_time for e in executions) / total_executions if total_executions > 0 else 0
    
    # Get recent executions (last 10)
    recent_executions = sorted(executions, key=lambda x: x.start_time, reverse=True)[:10]
    recent_executions_data = [
        {
            "id": e.id,
            "start_time": e.start_time,
            "execution_time": e.execution_time,
            "status": e.status,
            "virtualization": e.virtualization
        }
        for e in recent_executions
    ]
    
    return {
        "function_name": function.name,
        "total_executions": total_executions,
        "avg_execution_time": avg_execution_time,
        "success_rate": success_rate,
        "recent_executions": recent_executions_data
    }

@router.get("/system")
def get_system_metrics(db: Session = Depends(get_db)):
    """
    Get system-wide metrics
    """
    # Get total functions
    total_functions = db.query(func.count(Function.id)).scalar()
    
    # Get total executions
    total_executions = db.query(func.count(Execution.id)).scalar()
    
    # Get successful executions
    successful_executions = db.query(func.count(Execution.id)).filter(Execution.status == "success").scalar()
    
    # Calculate success rate
    success_rate = (successful_executions / total_executions) * 100 if total_executions > 0 else 0
    
    # Get average execution time
    avg_execution_time = db.query(func.avg(Execution.execution_time)).scalar() or 0
    
    # Get executions by virtualization technology
    executions_by_tech = db.query(
        Execution.virtualization,
        func.count(Execution.id).label("count")
    ).group_by(Execution.virtualization).all()
    
    virtualization_breakdown = {tech: count for tech, count in executions_by_tech}
    
    return {
        "total_functions": total_functions,
        "total_executions": total_executions,
        "success_rate": success_rate,
        "avg_execution_time": avg_execution_time,
        "virtualization_breakdown": virtualization_breakdown
    }
