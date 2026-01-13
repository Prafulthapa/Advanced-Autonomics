# test_all_images.py
import os

    # CRITICAL: All cid: references in HTML must have matching keys here
images = {
        "company_logo": "app/static/images/logo.png",
        "hero_robot_workshop": "app/static/images/hero_robot_workshop.jpg",
        "carpentry_applications_collage": "app/static/images/carpentry_applications_collage.jpg",
        "why_switch_left": "app/static/images/why_switch_left.jpg",  # ADD THIS
        "why_switch_right": "app/static/images/why_switch_right.jpg",  # ADD THIS
        "technical_left": "app/static/images/technical_left.jpg",
        "technical_right": "app/static/images/technical_right.jpg",
        "warranty_badge_5years": "app/static/images/warranty_badge_5years.png",
    }
print("🖼️ Checking ALL image paths:")
all_exist = True
for cid, path in images.items():
    exists = os.path.exists(path)
    status = "✅ EXISTS" if exists else "❌ NOT FOUND"
    print(f"  {cid}: {status} - {path}")
    if not exists:
        all_exist = False

if all_exist:
    print("\n✅ ALL IMAGES READY! You can send emails now.")
else:
    print("\n❌ MISSING IMAGES - Add them before sending emails.")