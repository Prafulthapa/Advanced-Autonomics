"""
Comprehensive Health Check System
Monitor all system components
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import httpx

from app.database import SessionLocal
from app.models.agent_config import AgentConfig

router = APIRouter(prefix="/health", tags=["Health"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def check_database(db: Session) -> dict:
    """Check database connectivity."""
    try:
        config = db.query(AgentConfig).first()
        return {
            "status": "healthy",
            "message": "Database connection OK",
            "config_exists": config is not None
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Database error: {str(e)}"
        }


async def check_redis() -> dict:
    """Check Redis connectivity."""
    try:
        import redis
        import os
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        r = redis.from_url(redis_url)
        r.ping()
        return {
            "status": "healthy",
            "message": "Redis connection OK"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Redis error: {str(e)}"
        }


async def check_ollama() -> dict:
    """Check Ollama AI service."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://ollama:11434/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return {
                    "status": "healthy",
                    "message": "Ollama service OK",
                    "models_loaded": len(models)
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": f"Ollama returned status {response.status_code}"
                }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Ollama error: {str(e)}"
        }


async def check_celery_workers() -> dict:
    """Check Celery worker status."""
    try:
        from app.worker.celery_app import celery_app
        inspect = celery_app.control.inspect()
        
        active = inspect.active()
        stats = inspect.stats()
        
        if not active or not stats:
            return {
                "status": "unhealthy",
                "message": "No Celery workers responding"
            }
        
        worker_count = len(stats.keys())
        
        return {
            "status": "healthy",
            "message": f"{worker_count} worker(s) active",
            "workers": list(stats.keys())
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Celery error: {str(e)}"
        }


async def check_smtp() -> dict:
    """Check SMTP connectivity (quick test)."""
    try:
        import smtplib
        import os
        
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        
        with smtplib.SMTP(smtp_host, smtp_port, timeout=5) as server:
            server.ehlo()
            return {
                "status": "healthy",
                "message": f"SMTP connection to {smtp_host} OK"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"SMTP error: {str(e)}"
        }


@router.get("/full")
async def full_health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check of all system components.
    Returns detailed status of each service.
    """
    
    checks = {
        "timestamp": datetime.utcnow().isoformat(),
        "database": await check_database(db),
        "redis": await check_redis(),
        "ollama": await check_ollama(),
        "celery": await check_celery_workers(),
        "smtp": await check_smtp(),
    }
    
    # Overall health
    all_healthy = all(
        check["status"] == "healthy" 
        for check in checks.values() 
        if isinstance(check, dict) and "status" in check
    )
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "overall": "All systems operational" if all_healthy else "Some systems degraded",
        "checks": checks
    }


@router.get("/quick")
async def quick_health_check(db: Session = Depends(get_db)):
    """Quick health check - database only."""
    try:
        config = db.query(AgentConfig).first()
        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
            "agent_running": config.is_running if config else False
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }