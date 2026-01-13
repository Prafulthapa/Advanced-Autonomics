"""
Email templates for Advanced Autonomics campaigns
Based on approved templates from Outreach_Emails_Advanced_Autonomics.docx
"""

GLASSWORKS_TEMPLATE = """You are writing a professional B2B cold outreach email for Advanced Autonomics, a robotics automation company.

Lead Information:
- First Name: {first_name}
- Last Name: {last_name}
- Company: {company}
- Email: {email}
- Industry: Glassworks

CRITICAL INSTRUCTIONS - FOLLOW EXACTLY:
1. If first_name is empty, "UNKNOWN", or None, use "Hi," (no name after comma)
2. If first_name exists, use "Hi {first_name},"
3. Do NOT use [First Name] or any placeholders
4. Write ONLY the email body (no subject line)
5. Sign as "Gerry Van Der Bas" with "Advanced Autonomics" on the next line
6. Keep under 300 words total

APPROVED EMAIL STRUCTURE (follow this closely):

Hi {first_name},

I'm reaching out from Advanced Autonomics, where we're currently offering no-cost pilot installations of our Robocrafter Series AMR—a fully autonomous mobile robot designed to handle high-risk, repetitive material handling tasks in environments like glassworks, where safety and precision are critical.

If you're not the right person for this, I'd really appreciate it if you could point me to whoever oversees facility automation, production operations, or material handling systems at {company}.

These systems:
- Operate unattended during night shifts
- Handle inventory, production flow, and warehouse logistics
- Are custom-engineered for each site
- Require no upfront cost for pilot clients

Most importantly, they deliver a very short ROI, often within months, and qualify for Section 179 tax credits through accelerated depreciation.

About Us:
Our founder, Yudhistir Gauli, is a pioneer in autonomous robotics and software frameworks. He holds multiple patents—including one for a fully autonomous CNC processing station—and has led the development of two successful robotics companies: Framebotix and Advanced Autonomics. His work has helped reshape how factories and job sites operate, bringing precision, safety, and scalability to industries facing labor and safety challenges.

As for me, I've spent my career in capital equipment across Tool & Die, Aerospace & Defense, and the Stone Industry, where I've led sales teams, developed products, and built long-term partnerships. I also owned two successful manufacturing companies focused on dust management systems for stone fabricators, so I understand firsthand the value of automation that's reliable, safe, and well-supported.

Would you be open to a short intro call to explore if this could be a fit?

Best regards,
Gerry Van Der Bas
Advanced Autonomics

NOW WRITE THIS EMAIL - use the actual first name and company name provided above. Write ONLY the email body (no subject line).
"""


def get_template_for_industry(industry: str) -> str:
    """
    Get the appropriate email template based on industry.
    """
    if not industry:
        return GLASSWORKS_TEMPLATE

    industry_lower = industry.lower()

    if "glass" in industry_lower:
        return GLASSWORKS_TEMPLATE
    else:
        # Default to glassworks
        return GLASSWORKS_TEMPLATE


def get_subject_for_industry(industry: str, company: str = None) -> str:
    """
    Get the appropriate subject line based on industry.
    These are the approved subject lines from the template document.
    """
    if not industry:
        return "One Price. Total Coverage. AMR + Scissor Lift Included."

    industry_lower = industry.lower()

    if "glass" in industry_lower:
        return "One Price. Total Coverage. AMR + Scissor Lift Included"
    else:
        return f"8th Generation Autonomous Woodworking Robots" if company else "8th Generation Autonomous Woodworking Robots."