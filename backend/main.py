import os
import subprocess
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# -----------------------------------
# Load environment variables
# -----------------------------------
load_dotenv()

# --- Safe threading limits for macOS (must be set before imports using NumPy/SciPy) ---
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

# -----------------------------------
# Import Routers (after limiting threads)
# -----------------------------------
from backend.routes import (
    portfolio_route,
    prediction_route,
    news_route,
    chatbot_route
)

# -----------------------------------
# Initialize FastAPI
# -----------------------------------
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
        "*"  # Allow all for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------
# Include Routers (all under /api)
# -----------------------------------
app.include_router(portfolio_route.router, prefix="/api", tags=["Portfolio"])
app.include_router(prediction_route.router, prefix="/api", tags=["Stocks"])
app.include_router(news_route.router, prefix="/api", tags=["News"])
app.include_router(chatbot_route.router, prefix="/api", tags=["Chatbot"])
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
            "/api/portfolio/*",
            "/api/news/*",
            "/api/predict/*"
            "/api/chat/*"
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
# Run Backend Safely (macOS Mutex Fix)
# -----------------------------------
if __name__ == "__main__":
    port = int(os.getenv("BACKEND_PORT", "8001"))
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8501")
    num_workers = 1  # ✅ Force single worker for macOS stability

    print(f"\n🚀 Starting backend server on port {port}...")
    print(f"📊 API Docs: http://localhost:{port}/docs")
    print(f"🔗 Frontend: {frontend_url}")
    print(f"🧵 Workers: {num_workers}\n")

    # ✅ Launch uvicorn in subprocess with enforced env vars
    env = os.environ.copy()
    env.update({
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "VECLIB_MAXIMUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1"
    })

    subprocess.run([
        "uvicorn", "backend.main:app",
        "--host", "0.0.0.0",
        "--port", str(port),
        "--workers", str(num_workers),
        "--no-access-log"
    ], env=env)