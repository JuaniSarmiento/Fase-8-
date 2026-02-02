"""
Main entry point for AI-Native MVP V3

Starts the FastAPI application.
"""
from backend.src_v3.infrastructure.http.app import create_app

# Create FastAPI app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Development mode
        log_level="info"
    )
