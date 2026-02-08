from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import sys

# Add the backend module to the path
sys.path.insert(0, os.path.dirname(__file__))

from core.database import engine, Base
from routers import dash, test

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FraudProof Ledger Backend")

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup frontend path
frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend')
frontend_path = os.path.abspath(frontend_path)

# Include API routers FIRST (before static files to avoid conflicts)
app.include_router(dash.router)
app.include_router(test.router)

@app.get("/")
async def root():
    return FileResponse(os.path.join(frontend_path, 'scanner.html'))

@app.get("/scanner.html")
async def scanner_page():
    return FileResponse(os.path.join(frontend_path, 'scanner.html'))

@app.get("/dash.html")
async def dashboard_page():
    return FileResponse(os.path.join(frontend_path, 'dash.html'))

@app.get("/scanner.js")
async def scanner_js():
    return FileResponse(os.path.join(frontend_path, 'scanner.js'))

@app.get("/dashboard.js")
async def dashboard_js():
    return FileResponse(os.path.join(frontend_path, 'dashboard.js'))

@app.get("/styles.css")
async def styles_css():
    return FileResponse(os.path.join(frontend_path, 'styles.css'))

# Health check
@app.get("/health")
async def health():
    return {"status": "ok"}

# Mount static files LAST to avoid conflicts with API routes
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
