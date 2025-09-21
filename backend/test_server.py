#!/usr/bin/env python3
"""
Simple test server to verify backend functionality
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="PropertyAI Test Server", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "PropertyAI Test Server is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "Test server is working"}

@app.get("/api/v1/health")
async def api_health():
    return {"status": "healthy", "api": "v1", "message": "API is working"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
