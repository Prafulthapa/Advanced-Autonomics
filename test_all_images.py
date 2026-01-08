# test_all_images.py
import os

    # CRITICAL: All cid: references in HTML must have matching keys here
images = {
        "company_logo": "app/static/images/logo.png",
        "footer_logo": "app/static/images/logo.png",
        "robot_lift_module": "app/static/images/robot_lift.jpg",
        "robot_product_shot": "app/static/images/robot_product.jpg",  # ADD THIS
        "qr_code": "app/static/images/qr_code.jpg",  # ADD THIS
        "robot_amr_warehouse": "app/static/images/robot_amr_warehouse.jpg",
        "robot_amr_pallet": "app/static/images/robot_amr_pallet.jpg",
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