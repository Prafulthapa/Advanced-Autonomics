from app.services.template_selector import get_template_for_lead, get_images_for_template
import os

# Test cases
test_cases = [
    ("Glass Manufacturing", "glass"),
    ("Commercial Glazing", "glass"),
    ("Window Installation", "glass"),
    ("Wood Products Inc", "wood"),
    ("Custom Carpentry", "wood"),
    ("Timber Processing", "wood"),
    ("Furniture Manufacturing", "wood"),
    ("Cabinet Makers", "wood"),
    ("Random Industry", "glass"),  # Default
    ("", "glass"),  # Empty
]

print("🧪 Testing Template Selection:\n")
print("=" * 60)

for industry, expected_type in test_cases:
    template_path, template_type = get_template_for_lead(industry)
    status = "✅" if template_type == expected_type else "❌"
    print(f"{status} Industry: '{industry:30}' → Template: {template_type}")

print("\n" + "=" * 60)
print("\n📸 Testing Image Loading:\n")

for template_type in ["glass", "wood"]:
    images = get_images_for_template(template_type)
    print(f"\n{template_type.upper()} Template Images:")
    
    missing = []
    for key, path in images.items():
        exists = os.path.exists(path)
        status = "✅" if exists else "❌"
        print(f"  {status} {key}: {path}")
        if not exists:
            missing.append(path)
    
    if missing:
        print(f"\n  ⚠️  WARNING: {len(missing)} images missing!")