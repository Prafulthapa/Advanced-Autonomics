from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.lead import Lead

router = APIRouter(tags=["Unsubscribe"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/unsubscribe", response_class=HTMLResponse)
async def unsubscribe_page(email: str, db: Session = Depends(get_db)):
    """Unsubscribe landing page."""
    
    lead = db.query(Lead).filter(Lead.email == email).first()
    
    if not lead:
        return """
        <html>
        <head><title>Unsubscribe</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>Email Not Found</h1>
            <p>This email address is not in our system.</p>
        </body>
        </html>
        """
    
    if lead.status == "unsubscribed":
        return """
        <html>
        <head><title>Already Unsubscribed</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>✓ Already Unsubscribed</h1>
            <p>You have already been removed from our mailing list.</p>
        </body>
        </html>
        """
    
    # Unsubscribe the lead
    lead.status = "unsubscribed"
    lead.agent_enabled = False
    lead.agent_paused = True
    db.commit()
    
    return f"""
    <html>
    <head>
        <title>Unsubscribed Successfully</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 50px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }}
            .container {{
                background: white;
                color: #333;
                padding: 40px;
                border-radius: 15px;
                max-width: 500px;
                margin: 0 auto;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            }}
            h1 {{ color: #4caf50; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>✓ Unsubscribed Successfully</h1>
            <p><strong>{email}</strong> has been removed from our mailing list.</p>
            <p>You will no longer receive emails from Advanced Autonomics.</p>
            <p style="margin-top: 30px; font-size: 14px; color: #666;">
                Changed your mind? Contact us at contact@advanced-autonomics.com
            </p>
        </div>
    </body>
    </html>
    """