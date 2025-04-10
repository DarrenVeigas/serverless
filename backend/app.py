from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import time
from sqlalchemy.orm import Session

from backend.db.database import engine, get_db
from backend.models.function import Base, Function
from backend.routers import functions, metrics
from fastapi import Depends

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Serverless Function Execution Platform",
    description="A platform for executing serverless functions using Docker and other virtualization technologies",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(functions.router)
app.include_router(metrics.router)

# Add middleware for request timing
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Route functions to their endpoints
@app.api_route("/invoke/{function_route}", methods=["GET", "POST", "PUT", "DELETE"])
async def route_function(
    function_route: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Route requests to the appropriate function based on the route
    """
    # Find function by route
    function = db.query(Function).filter(Function.route == function_route).first()
    if not function:
        return {"error": "Function not found"}
    
    # Check if function is active
    if not function.is_active:
        return {"error": "Function is not active"}
    
    # Get request data
    request_data = {}
    if request.method in ["POST", "PUT"]:
        try:
            request_data = await request.json()
        except:
            # Handle case where no JSON body is provided
            request_data = {}
    
    # Import the function execution router
    from backend.routers.functions import execute_function
    
    # Execute the function and return the result
    try:
        # Call the execute_function directly with the correct arguments
        return execute_function(function_id=function.id, request_data=request_data, db=db)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"Error executing function: {str(e)}"}

@app.get("/")
def read_root():
    return {"message": "Welcome to the Serverless Function Execution Platform"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)
