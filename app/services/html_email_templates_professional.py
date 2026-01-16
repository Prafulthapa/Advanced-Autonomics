"""
HTML Email Templates - WOOD ONLY VERSION
Glass template completely removed
"""

def get_simple_professional_template(
    first_name: str,
    company: str,
    email: str
) -> tuple[str, dict]:
    """
    WOOD ONLY: Simple fallback template.
    Not used in production (wood_template.html is used instead).
    """
    salutation = f"Hi {first_name}," if first_name and first_name not in ["UNKNOWN", "None", ""] else "Hi,"
    company_name = company or "your company"

    html_body = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <p>{salutation}</p>
    <p>I'm reaching out from Advanced Autonomics regarding our 8th generation autonomous woodworking robots.</p>
    <p>Best regards,<br>Gerry Van Der Bas<br>Advanced Autonomics</p>
</body>
</html>
"""
    return html_body, {}


def get_full_professional_template(
    first_name: str,
    company: str,
    email: str,
    lead=None
) -> tuple[str, dict]:
    """
    WOOD ONLY: Always uses wood template.
    Glass logic completely removed.
    """
    from app.services.template_selector import load_template_html
    import logging

    logger = logging.getLogger(__name__)

    # 🔥 WOOD ONLY - No template selection needed
    template_path = "app/static/templates/wood_template.html"
    template_type = "wood"

    logger.info(f"🪵 Lead: {email} → Template: {template_type}")

    try:
        # Load wood template
        html_body = load_template_html(template_path, email, first_name, company)

        # 🔥 RETURN EMPTY IMAGES - CDN URLs are already in HTML template
        images = {}

        logger.info(f"✅ Wood template loaded successfully")
        return html_body, images

    except FileNotFoundError as e:
        # Fallback to simple template
        logger.error(f"❌ Template error: {e}, falling back to simple template")
        return get_simple_professional_template(first_name, company, email)