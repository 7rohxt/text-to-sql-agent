"""
FastAPI backend for SQL Agent - Clean Architecture
"""
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

# Import from main.py instead of directly from agent
from main import main as execute_sql_query

load_dotenv()

# Create FastAPI app
app = FastAPI()


# Define what data we expect from user
class QueryRequest(BaseModel):
    query: str


# Root endpoint - just to check if server is running
@app.get("/")
def home():
    return {"message": "SQL Agent API is running!"}


# Main endpoint - execute natural language query
@app.post("/query")
def execute_query(request: QueryRequest):
    # Get the query from request
    user_query = request.query
    
    # Use the main function from main.py
    result = execute_sql_query(user_query)
    
    # Return the result
    return result


# Run the server
if __name__ == "__main__":
    import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=8000)