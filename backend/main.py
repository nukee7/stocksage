from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Routers
from backend.routes import (
    portfolio_route,
    stock_route,
)

# Initialize FastAPI
app = FastAPI(
    title="AI Financial Assistant API",
    description="Backend for AI-powered financial analytics, portfolio management, and chatbot assistant.",
    version="1.0.0"
)

# -----------------------------------
# CORS Middleware
# -----------------------------------
frontend_port = os.getenv("FRONTEND_PORT", "8501")
frontend_url = f"http://localhost:{frontend_port}"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        frontend_url,
        "http://localhost:8501",  # Default Streamlit port
        "*"  # Allow all for development (tighten for production)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------
# Include Routers (all under /api)
# -----------------------------------
app.include_router(stock_route.router, prefix="/api", tags=["Stocks"])
app.include_router(portfolio_route.router, prefix="/api", tags=["Portfolio"])

# -----------------------------------
# Root & Health Endpoints
# -----------------------------------
@app.get("/")
async def root():
    backend_port = os.getenv("BACKEND_PORT", "8001")
    return {
        "message": "🚀 AI Financial Assistant API is live!",
        "routes": [
            "/api/stocks/*",
            "/api/portfolio/*"
        ],
        "environment": os.getenv("ENVIRONMENT", "development"),
        "docs": f"http://localhost:{backend_port}/docs",
        "frontend_url": frontend_url
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "polygon_api_configured": bool(os.getenv("POLYGON_API_KEY"))
    }


# -----------------------------------
# Run Backend
# -----------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", "8001"))
    print(f"🚀 Starting backend server on port {port}...")
    print(f"📊 API Docs: http://localhost:{port}/docs")
    print(f"🔗 Frontend: {frontend_url}")
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=False)