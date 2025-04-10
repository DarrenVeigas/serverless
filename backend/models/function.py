from sqlalchemy import Column, Integer, String, Boolean, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.db.database import Base

class Function(Base):
    """
    Model for storing function metadata
    """
    __tablename__ = "functions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    route = Column(String, unique=True)
    language = Column(String)  # python, javascript, etc.
    code = Column(Text)  # The actual function code
    timeout = Column(Integer, default=30)  # Timeout in seconds
    container_image = Column(String, nullable=True)  # Docker image name
    is_active = Column(Boolean, default=True)
    
    # Relationship to executions
    executions = relationship("Execution", back_populates="function")


class Execution(Base):
    """
    Model for storing function execution data
    """
    __tablename__ = "executions"

    id = Column(Integer, primary_key=True, index=True)
    function_id = Column(Integer, ForeignKey("functions.id"))
    start_time = Column(Float)  # Unix timestamp
    end_time = Column(Float)  # Unix timestamp
    execution_time = Column(Float)  # In milliseconds
    status = Column(String)  # success, error, timeout
    error_message = Column(Text, nullable=True)
    virtualization = Column(String)  # docker, gvisor, etc.
    
    # Relationship to function
    function = relationship("Function", back_populates="executions")
