from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

# Function Schemas
class FunctionBase(BaseModel):
    name: str
    route: str
    language: str
    code: str
    timeout: int = 30
    virtualization: str = "docker"

class FunctionCreate(FunctionBase):
    pass

class Function(FunctionBase):
    id: int
    container_image: Optional[str] = None
    gvisor_image: Optional[str] = None  
    is_active: bool
    
    class Config:
        orm_mode = True

# Execution Schemas
class ExecutionBase(BaseModel):
    function_id: int
    status: str
    virtualization: str
    
class ExecutionCreate(ExecutionBase):
    start_time: float
    end_time: float
    execution_time: float
    error_message: Optional[str] = None

class Execution(ExecutionBase):
    id: int
    start_time: float
    end_time: float
    execution_time: float
    error_message: Optional[str] = None
    
    class Config:
        orm_mode = True

# Function with executions
class FunctionWithExecutions(Function):
    executions: List[Execution] = []
    
    class Config:
        orm_mode = True
