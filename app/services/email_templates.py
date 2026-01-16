"""
Email templates - WOOD ONLY VERSION
Glass template completely removed
"""

WOOD_TEMPLATE = """You are writing a professional B2B cold outreach email for Advanced Autonomics, a robotics automation company.

Lead Information:
- First Name: {first_name}
- Last Name: {last_name}
- Company: {company}
- Email: {email}
- Industry: Wood/Carpentry

CRITICAL INSTRUCTIONS - FOLLOW EXACTLY:
1. If first_name is empty, "UNKNOWN", or None, use "Hi," (no name after comma)
2. If first_name exists, use "Hi {first_name},"
3. Do NOT use [First Name] or any placeholders
4. Write ONLY the email body (no subject line)
5. Sign as "Gerry Van Der Bas" with "Advanced Autonomics" on the next line
6. Keep under 300 words total

APPROVED EMAIL STRUCTURE (follow this closely):

Hi {first_name},

I'm reaching out from Advanced Autonomics, where we specialize in 8th generation autonomous woodworking robots designed specifically for carpentry, furniture manufacturing, and timber processing operations.

If you're not the right person for this, I'd really appreciate it if you could point me to whoever oversees facility automation, production operations, or material handling systems at {company}.

These systems:
- Operate autonomously during night shifts
- Handle precision cutting, routing, and assembly tasks
- Are custom-engineered for woodworking environments
- Deliver ROI within months

Most importantly, they qualify for Section 179 tax credits through accelerated depreciation, making them extremely cost-effective for growing operations.

About Us:
Our founder, Yudhistir Gauli, holds multiple patents in autonomous robotics, including fully autonomous CNC processing stations. His work has helped reshape how woodworking facilities operate, bringing precision, safety, and scalability to an industry facing labor challenges.

As for me, I've spent my career in capital equipment and manufacturing, so I understand firsthand the value of automation that's reliable, safe, and well-supported.

Would you be open to a short intro call to explore if this could be a fit?

Best regards,
Gerry Van Der Bas
Advanced Autonomics

NOW WRITE THIS EMAIL - use the actual first name and company name provided above. Write ONLY the email body (no subject line).
"""


def get_template_for_industry(industry: str) -> str:
    """
    WOOD ONLY: Always returns wood template.
    """
    return WOOD_TEMPLATE


def get_subject_for_industry(industry: str, company: str = None) -> str:
    """
    WOOD ONLY: Always returns wood subject line.
    """
    return "8th Generation Autonomous Woodworking Robots"