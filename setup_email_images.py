#!/usr/bin/env python3
"""
Setup script to organize your robot images for email templates
Run this ONCE to set up your image directory structure
"""

import os
import shutil
from pathlib import Path

def setup_image_directories():
    """Create proper directory structure for email images."""
    
    print("🎨 Setting up Advanced Autonomics Email Images")
    print("=" * 60)
    
    # Create directories
    dirs = [
        "app/static/images",
        "app/static/templates"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {dir_path}")
    
    print("\n📁 Directory structure ready!")
    print("\n" + "=" * 60)
    print("NEXT STEPS - ADD YOUR IMAGES:")
    print("=" * 60)
    
    instructions = """
    
1. COMPANY LOGO (Required):
   → Place at: app/static/images/logo.png
   → Recommended: 600x200 pixels, PNG with transparent background
   → Your Advanced Autonomics logo
   
2. HERO ROBOT IMAGE (Required):
   → Place at: app/static/images/robot_hero.jpg
   → Recommended: 1200x800 pixels, high quality
   → Best choice: Image 5 (robot collage with blue robots and warranty badge)
   → This is the MAIN image recipients see first

3. PROBLEM/CHALLENGE IMAGE (Optional but recommended):
   → Place at: app/static/images/robot_problem.jpg
   → Recommended: 1200x800 pixels
   → Best choice: Image 4 (robots building with "WHY IMPORT PROBLEMS?" text)
   → Shows the problem you solve
   
4. ROBOT SHOWCASE 1 (Required):
   → Place at: app/static/images/robot_1.jpg
   → Recommended: 800x800 pixels
   → Best choice: Image 6 (close-up of robot arm with technical overlay)
   → Shows detail and precision

5. ROBOT SHOWCASE 2 (Required):
   → Place at: app/static/images/robot_2.jpg
   → Recommended: 800x800 pixels
   → Best choice: Image 7 (clean robot shot with blue gradient background)
   → Shows professional branding
   
COPY COMMAND EXAMPLES:
----------------------
# If your images are in current directory:
cp your_logo.png app/static/images/logo.png
cp robot_collage.jpg app/static/images/robot_hero.jpg
cp robot_building.jpg app/static/images/robot_problem.jpg
cp robot_closeup.jpg app/static/images/robot_1.jpg
cp robot_branded.jpg app/static/images/robot_2.jpg
"""
    
    print(instructions)
    
    # Check if images exist
    print("\n" + "=" * 60)
    print("CURRENT STATUS:")
    print("=" * 60)
    
    required_images = {
        "app/static/images/logo.png": "Company Logo",
        "app/static/images/robot_hero.jpg": "Hero Robot Image",
        "app/static/images/robot_1.jpg": "Robot Showcase 1",
        "app/static/images/robot_2.jpg": "Robot Showcase 2",
    }
    
    optional_images = {
        "app/static/images/robot_problem.jpg": "Problem Image",
    }
    
    all_good = True
    
    print("\nRequired Images:")
    for path, name in required_images.items():
        if os.path.exists(path):
            size = os.path.getsize(path) / 1024  # KB
            print(f"  ✅ {name}: Found ({size:.1f} KB)")
        else:
            print(f"  ❌ {name}: MISSING")
            all_good = False
    
    print("\nOptional Images:")
    for path, name in optional_images.items():
        if os.path.exists(path):
            size = os.path.getsize(path) / 1024
            print(f"  ✅ {name}: Found ({size:.1f} KB)")
        else:
            print(f"  ⚠️  {name}: Not added (recommended)")
    
    print("\n" + "=" * 60)
    
    if all_good:
        print("🎉 ALL REQUIRED IMAGES PRESENT!")
        print("✅ You're ready to send professional emails!")
        print("\nRun: python test_professional_email.py")
    else:
        print("⚠️  MISSING REQUIRED IMAGES")
        print("📋 Follow the instructions above to add images")
    
    print("=" * 60)


if __name__ == "__main__":
    setup_image_directories()