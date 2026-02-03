#!/usr/bin/env python3
"""
Script to run the Wizard Engine server
"""
import asyncio
import uvicorn
from app.main import app

async def main():
    """Run the server"""
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info",
        reload=False
    )
    server = uvicorn.Server(config)

    print("🚀 Starting Wizard Engine Server on http://localhost:8002")
    print("📋 Available endpoints:")
    print("  GET  /health")
    print("  POST /v1/sessions/start")
    print("  POST /v1/wizard/turn")
    print("  POST /v1/wizard/generate")
    print("  GET  /docs (API documentation)")
    print("")
    print("Press Ctrl+C to stop the server")

    try:
        await server.serve()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

if __name__ == "__main__":
    asyncio.run(main())