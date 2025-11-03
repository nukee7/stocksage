from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import all routers
from routes import (
    # prediction_route as prediction_routes,
    # sentiment_route as sentiment_routes,
    # chatbot_route as chatbot_routes,
    portfolio_route as portfolio_routes,
    # simulation_route as simulation_routes,
    stock_routes,
)

# Initialize FastAPI
app = FastAPI(
    title="AI Financial Assistant API",
    description="Backend for AI-powered financial analytics, portfolio management, and chatbot assistant.",
    version="1.0.0"
)

# --- Middleware ---
# Get frontend port from environment
frontend_port = os.getenv("FRONTEND_PORT", "8501")
frontend_url = f"http://localhost:{frontend_port}"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        frontend_url,
        "http://localhost:8501",  # Default Streamlit port
        "*"  # Allow all for development (restrict in production)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include Routers ---
# app.include_router(prediction_routes.router, prefix="/prediction", tags=["Prediction"])
app.include_router(stock_routes.router, prefix="/api", tags=["Stocks & Portfolio"])
# app.include_router(sentiment_routes.router, prefix="/sentiment", tags=["Sentiment"])
# app.include_router(chatbot_routes.router, prefix="/chatbot", tags=["Chatbot"])
app.include_router(portfolio_routes.router, prefix="/portfolio", tags=["Portfolio"])
# app.include_router(simulation_routes.router, prefix="/simulation", tags=["Simulation"])

# --- Root Endpoint ---
@app.get("/")
async def root():
    backend_port = os.getenv("BACKEND_PORT", "8001")
    return {
        "message": "🚀 AI Financial Assistant API is live!",
        "modules": [
            "/prediction",
            "/sentiment",
            "/chatbot",
            "/portfolio",
            "/simulation",
            "/api/stock/*"
        ],
        "environment": os.getenv("ENVIRONMENT", "development"),
        "api_docs": "/docs",
        "backend_port": backend_port,
        "frontend_url": frontend_url
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "polygon_api_configured": bool(os.getenv("POLYGON_API_KEY"))
    }

# Run with uvicorn programmatically for development
if __name__ == "__main__":
    import uvicorn
    # Get port from environment variable, default to 8001
    port = int(os.getenv("BACKEND_PORT", "8001"))
    print(f"🚀 Starting backend server on port {port}...")
    print(f"📊 API Documentation: http://localhost:{port}/docs")
    print(f"🔗 Frontend URL: {frontend_url}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)