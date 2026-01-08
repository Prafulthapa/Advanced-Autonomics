# test_all_images.py
import os

images = {
    "company_logo": "app/static/images/logo.png",
    "footer_logo": "app/static/images/logo.png",
    "hero_robot": "app/static/images/robot_hero.jpg",
    "yudhistir_headshot": "app/static/images/yudhistir.jpg",
    "gerry_headshot": "app/static/images/gerry.jpg",
    "robot_1": "app/static/images/robot_1.jpg",
    "robot_2": "app/static/images/robot_2.jpg",
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