"""Start Real Estate AI app with test configuration."""

import asyncio
import uvicorn
from main import app

# Import test database setup to override Redis
import test_db_setup

if __name__ == "__main__":
    print("🚀 Starting Real Estate AI App with Test Database")
    print("=" * 50)
    print("📊 Database: FakeRedis (in-memory)")
    print("🔐 Auth: JWT enabled")
    print("🧠 AI: Groq LLM integration")
    print("📱 API: All CRM endpoints active")
    print("🌐 Server: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    print("=" * 50)
    
    # Add health endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "real-estate-ai", "database": "connected"}
    
    # Run the app
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )
