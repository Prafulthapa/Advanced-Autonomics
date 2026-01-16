"""
Template selector - WOOD ONLY VERSION
Glass template logic completely removed
"""
import os
from typing import Dict, Tuple

def get_template_for_lead(lead) -> Tuple[str, str]:
    """
    WOOD ONLY: Always returns wood template.
    Glass logic completely removed.
    """
    # 🔥 WOOD ONLY - No glass logic whatsoever
    return "app/static/templates/wood_template.html", "wood"


def get_images_for_template(template_type: str) -> Dict[str, str]:
    """Get correct images - WOOD ONLY"""

    # 🔥 WOOD ONLY - No images needed (templates use CDN)
    return {}


def load_template_html(template_path: str, email: str, first_name: str = "", company: str = "") -> str:
    """Load and populate template HTML - WOOD ONLY"""

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found: {template_path}")

    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Replace placeholders
    html = html.replace('{{EMAIL}}', email)
    html = html.replace('{{FIRST_NAME}}', first_name or '')
    html = html.replace('{{COMPANY}}', company or 'your company')
    html = html.replace('{{UNSUBSCRIBE_LINK}}', f'http://localhost:8000/unsubscribe?email={email}')

    return html