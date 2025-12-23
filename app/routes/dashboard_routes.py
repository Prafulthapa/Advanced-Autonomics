from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Dashboard"])

@router.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the web dashboard (handled by main.py now)."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Redirecting...</title>
        <meta http-equiv="refresh" content="0; url=/docs" />
    </head>
    <body>
        <p>Redirecting to API docs...</p>
    </body>
    </html>
    """