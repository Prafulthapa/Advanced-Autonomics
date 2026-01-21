"""
Restore scraper progress from existing session file
This will let you continue from where you left off (search #41)
"""

import json
from pathlib import Path
from datetime import datetime

def restore_progress_from_session():
    """Create scraper_progress.json from session_20260120_124852.json"""
    
    print("=" * 70)
    print("🔄 RESTORING SCRAPER PROGRESS FROM SESSION FILE")
    print("=" * 70)
    
    # Your session file
    session_file = "data/session_20260120_124852.json"
    progress_file = "data/scraper_progress.json"
    
    # Check if session file exists
    if not Path(session_file).exists():
        print(f"❌ Session file not found: {session_file}")
        return
    
    print(f"📂 Loading session file: {session_file}")
    
    # Load the session data
    with open(session_file, 'r', encoding='utf-8') as f:
        leads = json.load(f)
    
    print(f"✅ Loaded {len(leads)} leads from session")
    
    # Analyze what was scraped
    locations_scraped = set()
    search_terms_used = set()
    
    for lead in leads:
        # Extract location from address or state
        state = lead.get('state', '')
        if state:
            locations_scraped.add(state)
    
    print(f"\n📊 Session Analysis:")
    print(f"   - Total leads: {len(leads)}")
    print(f"   - Locations found: {len(locations_scraped)}")
    print(f"   - Sample locations: {list(locations_scraped)[:5]}")
    
    # Based on your log: "Search 41/1729: carpentry in Stow OH"
    # This means searches 1-40 are complete
    
    # All search terms from the scraper
    search_terms = [
        "carpentry", "carpenter", "carpentry services", "carpentry contractor",
        "cabinet maker", "cabinetmaker", "custom cabinets", "kitchen cabinets",
        "woodworking", "custom woodworking", "wood shop",
        "finish carpentry", "trim carpentry", "framing contractor", "millwork",
        "kitchen remodeling", "bathroom remodeling", "home remodeling",
        "renovation contractor"
    ]
    
    # All locations
    locations = [
        "Columbus OH", "Cleveland OH", "Cincinnati OH", "Toledo OH", "Akron OH",
        "Dayton OH", "Parma OH", "Canton OH", "Youngstown OH", "Lorain OH",
        "Hamilton OH", "Springfield OH", "Kettering OH", "Elyria OH", "Lakewood OH",
        "Cuyahoga Falls OH", "Middletown OH", "Newark OH", "Mansfield OH", "Mentor OH",
        "Beavercreek OH", "Strongsville OH", "Dublin OH", "Fairfield OH", "Warren OH",
        "Lima OH", "Huber Heights OH", "Marion OH", "Findlay OH", "Lancaster OH",
        "Euclid OH", "Cleveland Heights OH", "Westerville OH", "Delaware OH", "Grove City OH",
        "Reynoldsburg OH", "Upper Arlington OH", "Gahanna OH", "Hilliard OH", "Mason OH",
        "Stow OH", "Brunswick OH", "North Olmsted OH", "North Royalton OH", "Westlake OH",
        "Boardman OH", "Kent OH", "Garfield Heights OH", "Sandusky OH", "Massillon OH",
        "Bowling Green OH", "Alliance OH", "Austintown OH", "Zanesville OH", "Fairborn OH",
        "Ashland OH", "Chillicothe OH", "Portsmouth OH", "Wooster OH", "Xenia OH",
        "Tiffin OH", "Miamisburg OH", "Medina OH", "Wadsworth OH", "Barberton OH",
        "Coshocton OH", "Fremont OH", "Sidney OH", "Oxford OH", "Troy OH",
        "Piqua OH", "Norwalk OH", "Defiance OH", "Cambridge OH", "Bucyrus OH",
        "Marysville OH", "Bellefontaine OH", "Salem OH", "Circleville OH",
        "Washington Court House OH", "Urbana OH", "New Philadelphia OH", "Galion OH",
        "Greenville OH", "Marietta OH", "Athens OH", "Mount Vernon OH", "Ashtabula OH",
        "Conneaut OH", "Willoughby OH", "Painesville OH"
    ]
    
    # Create search combinations (same order as scraper)
    all_searches = [(term, loc) for term in search_terms for loc in locations]
    
    print(f"\n📋 Total possible searches: {len(all_searches)}")
    
    # Your log shows: "Search 41/1729: carpentry in Stow OH"
    # This means index 40 was being processed (0-based index)
    # So searches 0-39 are complete (first 40 searches)
    
    completed_searches = []
    for idx in range(40):  # First 40 searches (indices 0-39)
        term, loc = all_searches[idx]
        search_key = f"{term}|{loc}"
        completed_searches.append(search_key)
    
    print(f"\n🔍 Marking first 40 searches as completed:")
    print(f"   - First search: {all_searches[0]}")
    print(f"   - Last completed: {all_searches[39]}")
    print(f"   - Next search (41): {all_searches[40]}")
    
    # Create progress data
    progress_data = {
        "completed_searches": completed_searches,
        "current_search_index": 40,  # Will resume at index 40 (search #41)
        "last_updated": datetime.now().isoformat(),
        "total_leads_collected": len(leads),
        "active_session_file": session_file,  # Track the session file to continue using
        "restored_from": session_file,
        "restoration_date": datetime.now().isoformat()
    }
    
    # Save progress file
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress_data, f, indent=2)
    
    print(f"\n✅ Progress file created: {progress_file}")
    print(f"\n📊 Progress Summary:")
    print(f"   - Completed searches: {len(completed_searches)}")
    print(f"   - Current index: 40")
    print(f"   - Will resume at: Search #41 (carpentry in Stow OH)")
    print(f"   - Total leads so far: {len(leads)}")
    print(f"   - Remaining searches: {len(all_searches) - 40}")
    
    print("\n" + "=" * 70)
    print("✅ RESTORATION COMPLETE!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Replace carpentry_lead_scraper.py with the updated version")
    print("2. Run: docker-compose exec lead-scraper python lead_scraper/lead_orchestrator.py")
    print("3. It will resume from search #41: 'carpentry in Stow OH'")
    print("=" * 70)


if __name__ == "__main__":
    restore_progress_from_session()