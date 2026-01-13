"""
Template selector based on lead industry.
Prevents sending wrong templates to leads.
"""
import os
from typing import Dict, Tuple

def get_template_for_lead(lead) -> Tuple[str, str]:
    """
    Select template based on lead's STORED preference.
    Priority: agent_notes → industry → default
    """
    
    # 🔥 Check agent_notes for stored template
    if hasattr(lead, 'agent_notes') and lead.agent_notes:
        if "template:glass" in lead.agent_notes:
            return "app/static/templates/glass_template.html", "glass"
        elif "template:wood" in lead.agent_notes:
            return "app/static/templates/wood_template.html", "wood"
    
    # Fallback to industry
    industry_lower = (lead.industry or "").lower()
    
    if any(word in industry_lower for word in ["wood", "carpentry", "timber", "furniture"]):
        return "app/static/templates/wood_template.html", "wood"
    elif any(word in industry_lower for word in ["glass", "glazing", "window"]):
        return "app/static/templates/glass_template.html", "glass"
    else:
        return "app/static/templates/glass_template.html", "glass"


def get_images_for_template(template_type: str) -> Dict[str, str]:
    """Get correct images for template type."""
    
    base_images = {
        "company_logo": "app/static/images/logo.png",
        "footer_logo": "app/static/images/logo.png",
    }
    
    if template_type == "glass":
        base_images.update({
            "robot_lift_module": "app/static/images/robot_lift.jpg",
            "robot_product_shot": "app/static/images/robot_product.jpg",
            "qr_code": "app/static/images/qr_code.jpg",
            "robot_amr_warehouse": "app/static/images/robot_amr_warehouse.jpg",
            "robot_amr_pallet": "app/static/images/robot_amr_pallet.jpg",
        })
    
    elif template_type == "wood":
        base_images.update({
            # 🔥 CORRECT NAMES MATCHING YOUR ACTUAL FILES
            "hero_robot_workshop": "app/static/images/hero_robot_workshop.png",
            "carpentry_applications_collage": "app/static/images/carpentry_applications_collage.jpg",
            "why_switch_left": "app/static/images/why_switch_left.jpg",
            "warranty_badge_5years": "app/static/images/warranty_badge_5years.png",
            "why_switch_right": "app/static/images/why_switch_right.jpg",
            "technical_left": "app/static/images/technical_left.jpg",
            "technical_right": "app/static/images/technical_right.jpg",
        })
    
    return base_images

def load_template_html(template_path: str, email: str, first_name: str = "", company: str = "") -> str:
    """Load and populate template HTML."""
    
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