"""
HTML Email Templates for Advanced Autonomics
Beautiful, professional HTML emails with embedded images
"""

def get_html_template(
    first_name: str,
    last_name: str,
    company: str,
    email: str,
    industry: str = "Glassworks",
    from_email: str = "contact@advanced-autonomics.com"
) -> tuple[str, dict]:
    """
    Generate HTML email with embedded images.
    
    Returns:
        (html_body, images_dict)
        images_dict format: {"cid": "path/to/image"}
    """
    
    # Determine salutation
    if first_name and first_name not in ["UNKNOWN", "None", ""]:
        salutation = f"Hi {first_name},"
    else:
        salutation = "Hi,"
    
    company_name = company or "your company"
    
    # HTML email body
    html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            background-color: #f4f4f4;
        }}
        .email-container {{
            background-color: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 3px solid #667eea;
        }}
        .logo {{
            max-width: 200px;
            height: auto;
        }}
        .content {{
            margin-bottom: 25px;
        }}
        .content p {{
            margin-bottom: 15px;
        }}
        .highlight {{
            background-color: #f0f4ff;
            padding: 15px;
            border-left: 4px solid #667eea;
            margin: 20px 0;
        }}
        .benefits {{
            margin: 20px 0;
        }}
        .benefits li {{
            margin-bottom: 10px;
        }}
        .cta {{
            text-align: center;
            margin: 30px 0;
        }}
        .cta-button {{
            display: inline-block;
            padding: 15px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
        }}
        .signature {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }}
        .signature-image {{
            max-width: 150px;
            height: auto;
            margin-top: 10px;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 12px;
            color: #888;
        }}
        .unsubscribe {{
            margin-top: 15px;
            font-size: 11px;
        }}
        .unsubscribe a {{
            color: #667eea;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <!-- Header with Logo -->
        <div class="header">
            <img src="cid:company_logo" alt="Advanced Autonomics" class="logo">
            <p style="color: #667eea; font-size: 18px; margin-top: 10px;">
                <strong>Autonomous Robotics Solutions</strong>
            </p>
        </div>

        <!-- Main Content -->
        <div class="content">
            <p>{salutation}</p>

            <p>I'm reaching out from <strong>Advanced Autonomics</strong>, where we're currently offering <strong>no-cost pilot installations</strong> of our Robocrafter Series AMR—a fully autonomous mobile robot designed to handle high-risk, repetitive material handling tasks in environments like glassworks, where safety and precision are critical.</p>

            <p>If you're not the right person for this, I'd really appreciate it if you could point me to whoever oversees facility automation, production operations, or material handling systems at <strong>{company_name}</strong>.</p>

            <div class="highlight">
                <strong>🤖 These systems:</strong>
                <ul class="benefits">
                    <li>✅ Operate unattended during night shifts</li>
                    <li>✅ Handle inventory, production flow, and warehouse logistics</li>
                    <li>✅ Are custom-engineered for each site</li>
                    <li>✅ Require no upfront cost for pilot clients</li>
                </ul>
            </div>

            <p>Most importantly, they deliver a <strong>very short ROI</strong>, often within months, and qualify for <strong>Section 179 tax credits</strong> through accelerated depreciation.</p>

            <p><strong>About Us:</strong></p>
            <p>Our founder, <strong>Yudhistir Gauli</strong>, is a pioneer in autonomous robotics and software frameworks. He holds multiple patents—including one for a fully autonomous CNC processing station—and has led the development of two successful robotics companies: Framebotix and Advanced Autonomics.</p>

            <p>As for me, I've spent my career in capital equipment across Tool & Die, Aerospace & Defense, and the Stone Industry, where I've led sales teams, developed products, and built long-term partnerships.</p>

            <p style="margin-top: 25px;">Would you be open to a <strong>short intro call</strong> to explore if this could be a fit?</p>
        </div>

        <!-- Call to Action -->
        <div class="cta">
            <a href="https://calendly.com/advanced-autonomics" class="cta-button">
                📅 Schedule a Call
            </a>
        </div>

        <!-- Signature -->
        <div class="signature">
            <p style="margin-bottom: 5px;"><strong>Best regards,</strong></p>
            <p style="margin: 5px 0;"><strong>Gerry Van Der Bas</strong></p>
            <p style="margin: 5px 0;">Advanced Autonomics</p>
            <p style="margin: 5px 0;">📧 {from_email}</p>
            <p style="margin: 5px 0;">🌐 <a href="https://www.advanced-autonomics.com">www.advanced-autonomics.com</a></p>
            
            <!-- Optional: Add signature image -->
            <!-- <img src="cid:signature" alt="Signature" class="signature-image"> -->
        </div>

        <!-- Footer -->
        <div class="footer">
            <p>This email was sent to <strong>{email}</strong></p>
            <div class="unsubscribe">
                <p>
                    Don't want to receive these emails? 
                    <a href="{{{{unsubscribe_link}}}}">Unsubscribe here</a>
                </p>
            </div>
            <p style="margin-top: 10px;">
                © 2025 Advanced Autonomics | All Rights Reserved
            </p>
        </div>
    </div>
</body>
</html>
"""

    # Images to embed (CID mapping)
    # You'll need to place actual images in app/static/images/
    images = {
        "company_logo": "app/static/images/logo.png",
        # "signature": "app/static/images/signature.png",  # Optional
    }

    return html_body, images


def get_followup_html_template(
    first_name: str,
    company: str,
    email: str,
    followup_number: int = 1
) -> tuple[str, dict]:
    """
    Generate HTML follow-up email template.
    """
    
    salutation = f"Hi {first_name}," if first_name and first_name not in ["UNKNOWN", "None", ""] else "Hi,"
    company_name = company or "your company"
    
    html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
        }}
        .email-container {{
            background-color: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .logo {{
            max-width: 180px;
            height: auto;
        }}
        .content p {{
            margin-bottom: 15px;
        }}
        .signature {{
            margin-top: 25px;
            padding-top: 15px;
            border-top: 1px solid #ddd;
        }}
        .footer {{
            text-align: center;
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid #ddd;
            font-size: 12px;
            color: #888;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <img src="cid:company_logo" alt="Advanced Autonomics" class="logo">
        </div>

        <div class="content">
            <p>{salutation}</p>

            <p>I wanted to follow up on my previous email about our <strong>no-cost pilot program</strong> for autonomous material handling at {company_name}.</p>

            <p>I understand you're busy, but I thought it might be worth a quick conversation if:</p>
            <ul>
                <li>You're looking to improve safety in material handling</li>
                <li>You need to handle operations during night shifts</li>
                <li>You're exploring automation options</li>
            </ul>

            <p>Would a brief 15-minute call work for you this week?</p>
        </div>

        <div class="signature">
            <p><strong>Best regards,</strong></p>
            <p><strong>Gerry Van Der Bas</strong></p>
            <p>Advanced Autonomics</p>
        </div>

        <div class="footer">
            <p>Sent to {email} | <a href="{{{{unsubscribe_link}}}}">Unsubscribe</a></p>
        </div>
    </div>
</body>
</html>
"""

    images = {
        "company_logo": "app/static/images/logo.png"
    }

    return html_body, images