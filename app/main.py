from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.database import Base, engine
from app.models.lead import Lead
from app.models.email_log import EmailLog
from app.models.email_reply import EmailReply
from app.models.agent_config import AgentConfig
from app.models.agent_action_log import AgentActionLog

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize agent config if not exists
from app.database import SessionLocal
db = SessionLocal()
if not db.query(AgentConfig).first():
    print("🔧 Creating initial agent config...")
    config = AgentConfig(
        is_running=False,
        is_paused=False,
        daily_email_limit=50,
        hourly_email_limit=10,
        last_reset_date="2025-01-01"
    )
    db.add(config)
    db.commit()
    print("✅ Agent config created")
db.close()

app = FastAPI(
    title="Advanced Autonomics - AI Email Agent",
    description="Autonomous email outreach with AI decision-making",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and register routes
from app.routes.lead_routes import router as lead_router
from app.routes.ai_routes import router as ai_router
from app.routes.email_routes import router as email_router
from app.routes.import_routes import router as import_router
from app.routes.reply_routes import router as reply_router
from app.routes.agent_routes import router as agent_router  # NEW

app.include_router(lead_router, prefix="/leads", tags=["leads"])
app.include_router(ai_router)
app.include_router(email_router)
app.include_router(import_router)
app.include_router(reply_router)
app.include_router(agent_router)  # NEW: Agent control routes

# Serve static files (dashboard)
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/", tags=["root"])
async def root():
    """Serve the AI agent dashboard."""
    static_file = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(static_file):
        return FileResponse(static_file)

    return {
        "message": "Advanced Autonomics AI Email Agent",
        "version": "0.3.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "dashboard": "/",
            "leads": "/leads",
            "emails": "/emails",
            "replies": "/replies",
            "ai": "/ai",
            "import": "/import",
            "agent": "/agent"  # NEW
        }
    }

@app.get("/dashboard", tags=["root"])
async def dashboard():
    """Alternative dashboard route."""
    return await root()

@app.get("/health", tags=["health"])
async def health():
    """Health check endpoint."""
    from app.database import SessionLocal
    
    # Check database
    db = SessionLocal()
    config = db.query(AgentConfig).first()
    db.close()
    
    return {
        "status": "ok",
        "service": "ai-email-agent",
        "version": "0.3.0",
        "agent_running": config.is_running if config else False,
        "features": [
            "Lead Management",
            "AI Email Generation",
            "SMTP Sending",
            "IMAP Reply Fetching",
            "Reply Classification",
            "CSV Import",
            "Web Dashboard",
            "Autonomous Agent",  # NEW
            "Automated Follow-ups",  # NEW
            "Rate Limiting",  # NEW
        ]
    }