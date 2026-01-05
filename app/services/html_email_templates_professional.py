"""
PROFESSIONAL HTML Email Templates for Advanced Autonomics
Uses actual robot images from your collection
"""

def get_simple_professional_template(
    first_name: str,
    company: str,
    email: str
) -> tuple[str, dict]:
    """
    Professional HTML email with multiple robot images.
    
    Returns:
        (html_body, images_dict)
    """
    
    salutation = f"Hi {first_name}," if first_name and first_name not in ["UNKNOWN", "None", ""] else "Hi,"
    company_name = company or "your company"
    
    html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Inter', sans-serif; margin: 0; padding: 0; background-color: #0a0a0a; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: #1a1a1a; }}
        .header {{ background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%); padding: 30px; text-align: center; }}
        .hero {{ padding: 40px 30px; background: linear-gradient(180deg, #0f172a 0%, #1a1a1a 100%); }}
        .content {{ padding: 40px 30px; }}
        .cta-button {{ display: inline-block; background: linear-gradient(135deg, #38bdf8 0%, #3b82f6 100%); color: white !important; padding: 16px 40px; border-radius: 50px; text-decoration: none; font-weight: 700; }}
        .benefit-box {{ background: rgba(56, 189, 248, 0.1); border-left: 4px solid #38bdf8; padding: 20px; margin: 15px 0; border-radius: 8px; }}
        .footer {{ background-color: #0a0a0a; padding: 30px; text-align: center; color: #64748b; font-size: 12px; }}
        h1 {{ color: #ffffff; font-size: 42px; margin: 0 0 20px 0; line-height: 1.2; }}
        h2 {{ color: #ffffff; font-size: 32px; margin: 0 0 15px 0; }}
        p {{ color: #cbd5e1; line-height: 1.6; }}
        .highlight {{ color: #38bdf8; }}
        @media screen and (max-width: 600px) {{
            h1 {{ font-size: 32px !important; }}
            h2 {{ font-size: 24px !important; }}
            .content {{ padding: 20px !important; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <img src="cid:company_logo" alt="Advanced Autonomics" style="height: 50px;">
        </div>
        
        <!-- Hero -->
        <div class="hero">
            <img src="cid:hero_robot" alt="Advanced Autonomics Robots" style="width: 100%; border-radius: 12px; margin-bottom: 30px;">
            <h1>No-Cost Pilot.<br>Immediate ROI.<br><span class="highlight">Zero Risk.</span></h1>
            <p style="font-size: 18px; margin-bottom: 30px;">
                {salutation}
            </p>
            <p style="font-size: 16px; margin-bottom: 30px;">
                I'm reaching out from <strong>Advanced Autonomics</strong>, where we're offering <strong>no-cost pilot installations</strong> of our Robocrafter Series AMR—fully autonomous mobile robots designed for high-risk, repetitive material handling in environments like glassworks.
            </p>
            <p style="font-size: 16px; margin-bottom: 30px;">
                If you're not the right person, I'd appreciate if you could point me to whoever oversees facility automation, production operations, or material handling at <strong>{company_name}</strong>.
            </p>
            <a href="https://calendly.com/advanced-autonomics" class="cta-button">
                SCHEDULE DISCOVERY CALL →
            </a>
        </div>
        
        <!-- Benefits -->
        <div class="content" style="background-color: #0f172a;">
            <h2>What You Get</h2>
            
            <div class="benefit-box">
                <p style="margin: 0; color: #ffffff; font-weight: 600;">✓ Operate Unattended During Night Shifts</p>
                <p style="margin: 8px 0 0 0; font-size: 14px;">24/7 autonomous operation without supervision.</p>
            </div>
            
            <div class="benefit-box">
                <p style="margin: 0; color: #ffffff; font-weight: 600;">✓ Handle Inventory & Production Flow</p>
                <p style="margin: 8px 0 0 0; font-size: 14px;">Warehouse logistics fully automated.</p>
            </div>
            
            <div class="benefit-box">
                <p style="margin: 0; color: #ffffff; font-weight: 600;">✓ Custom-Engineered for Your Site</p>
                <p style="margin: 8px 0 0 0; font-size: 14px;">Tailored to your specific facility needs.</p>
            </div>
            
            <div class="benefit-box">
                <p style="margin: 0; color: #ffffff; font-weight: 600;">✓ No Upfront Cost for Pilot</p>
                <p style="margin: 8px 0 0 0; font-size: 14px;">We prove ROI before you commit a single dollar.</p>
            </div>
            
            <div class="benefit-box">
                <p style="margin: 0; color: #ffffff; font-weight: 600;">✓ ROI Within Months + Section 179 Tax Credits</p>
                <p style="margin: 8px 0 0 0; font-size: 14px;">Very short payback period with accelerated depreciation.</p>
            </div>
        </div>
        
        <!-- Product Showcase -->
        <div class="content" style="background-color: #1a1a1a;">
            <h2>Robocrafter Series AMR</h2>
            <p>Fully autonomous. Precision-engineered. Battle-tested.</p>
            
            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td width="48%" style="padding: 10px; vertical-align: top;">
                        <img src="cid:robot_1" alt="Robot Detail" style="width: 100%; border-radius: 12px; display: block;">
                        <p style="color: #94a3b8; font-size: 14px; margin: 10px 0 0 0;">
                            <strong style="color: #38bdf8;">Precision Engineering</strong><br>
                            Custom-built for demanding environments
                        </p>
                    </td>
                    <td width="4%"></td>
                    <td width="48%" style="padding: 10px; vertical-align: top;">
                        <img src="cid:robot_2" alt="Robot in Action" style="width: 100%; border-radius: 12px; display: block;">
                        <p style="color: #94a3b8; font-size: 14px; margin: 10px 0 0 0;">
                            <strong style="color: #38bdf8;">Night Shift Ready</strong><br>
                            Operates 24/7 without supervision
                        </p>
                    </td>
                </tr>
            </table>
        </div>
        
        <!-- About -->
        <div class="content" style="background-color: #0a0a0a;">
            <h2 style="font-size: 28px;">About Us</h2>
            
            <div style="background: linear-gradient(135deg, #1e3a8a 0%, #312e81 100%); padding: 25px; border-radius: 12px; margin: 20px 0;">
                <p style="margin: 0 0 10px 0;">
                    <strong style="color: #ffffff; font-size: 18px;">Yudhistir Gauli</strong> – Founder<br>
                    <span style="color: #94a3b8; font-size: 14px;">Multiple U.S. Patents | 2x Successful Robotics Companies</span>
                </p>
                <p style="font-size: 14px; margin: 0;">
                    Pioneer in autonomous robotics and software frameworks. Holds multiple patents including one for a fully autonomous CNC processing station. Founded Framebotix and Advanced Autonomics.
                </p>
            </div>
            
            <div style="background: linear-gradient(135deg, #0f766e 0%, #134e4a 100%); padding: 25px; border-radius: 12px; margin: 20px 0;">
                <p style="margin: 0 0 10px 0;">
                    <strong style="color: #ffffff; font-size: 18px;">Gerry Van Der Bas</strong> – Sales Director<br>
                    <span style="color: #94a3b8; font-size: 14px;">30+ Years Capital Equipment | Former Business Owner</span>
                </p>
                <p style="font-size: 14px; margin: 0;">
                    Extensive experience in Tool & Die, Aerospace & Defense, and Stone Industries. Former owner of two successful manufacturing companies. Expert in building long-term partnerships.
                </p>
            </div>
            
            <p style="font-size: 16px; margin: 25px 0;">
                Would you be open to a <strong>short intro call</strong> to explore if this could be a fit?
            </p>
        </div>
        
        <!-- Final CTA -->
        <div style="background: linear-gradient(135deg, #1e3a8a 0%, #7c3aed 100%); padding: 50px 30px; text-align: center;">
            <h2 style="font-size: 36px; margin-bottom: 15px;">Ready to Automate?</h2>
            <p style="margin-bottom: 30px; font-size: 16px;">Limited pilot spots available. Let's discuss your specific needs.</p>
            <a href="https://calendly.com/advanced-autonomics" class="cta-button" style="background: #ffffff; color: #1e3a8a;">
                📅 BOOK YOUR CONSULTATION
            </a>
            <p style="font-size: 14px; margin-top: 20px;">15-minute call • No obligation • Free facility assessment</p>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <img src="cid:footer_logo" alt="Advanced Autonomics" style="height: 35px; margin-bottom: 15px;">
            <p style="margin: 10px 0;">
                <strong style="color: #94a3b8;">Advanced Autonomics</strong><br>
                Autonomous Robotics Solutions | Assembled in USA 🇺🇸
            </p>
            <p style="margin: 15px 0;">
                📧 contact@advanced-autonomics.com<br>
                🌐 <a href="https://www.advanced-autonomics.com" style="color: #38bdf8;">www.advanced-autonomics.com</a>
            </p>
            <p style="margin-top: 20px; color: #334155; font-size: 11px;">
                This email was sent to {email}<br>
                <a href="{{{{UNSUBSCRIBE_LINK}}}}" style="color: #475569;">Unsubscribe</a> | 
                <a href="https://www.advanced-autonomics.com/privacy" style="color: #475569;">Privacy Policy</a>
            </p>
            <p style="color: #1e293b; font-size: 10px; margin: 15px 0 0 0;">
                © 2025 Advanced Autonomics. All Rights Reserved.
            </p>
        </div>
    </div>
</body>
</html>
"""

    images = {
        "company_logo": "app/static/images/logo.png",
        "footer_logo": "app/static/images/logo.png",
        "hero_robot": "app/static/images/robot_hero.jpg",
        "robot_1": "app/static/images/robot_1.jpg",
        "robot_2": "app/static/images/robot_2.jpg",
    }

    return html_body, images


def get_full_professional_template(
    first_name: str,
    company: str,
    email: str
) -> tuple[str, dict]:
    """Full professional HTML template."""
    
    import os
    
    # USE THE SAFE VERSION
    template_path = "app/static/templates/professional_email_safe.html"  # ← CHANGED
    
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            html_body = f.read()
    else:
        return get_simple_professional_template(first_name, company, email)
    
    # Replace placeholders
    html_body = html_body.replace('{{EMAIL}}', email)
    html_body = html_body.replace('{{UNSUBSCRIBE_LINK}}', f'http://localhost:8000/unsubscribe?email={email}')
    
    images = {
        "company_logo": "app/static/images/logo.png",
        "footer_logo": "app/static/images/logo.png",
        "hero_robot": "app/static/images/robot_hero.jpg",
        "problem_image": "app/static/images/robot_problem.jpg",
        "robot_1": "app/static/images/robot_1.jpg",
        "robot_2": "app/static/images/robot_2.jpg",
    }
    
    return html_body, images