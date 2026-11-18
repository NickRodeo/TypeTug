"""Start the server: python run.py"""
import uvicorn

from app.config import Settings

if __name__ == "__main__":
    settings = Settings.from_env()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        ws_ping_interval=settings.heartbeat_interval,  # heartbeat: detects dead connections
        ws_ping_timeout=settings.heartbeat_interval,
    )
