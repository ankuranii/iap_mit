#!/usr/bin/env python3
"""
Complete Notion integration setup and import
"""

import os
import sys
from notion_client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
if not NOTION_TOKEN:
    print("❌ Error: NOTION_TOKEN not found in .env file")
    sys.exit(1)

def test_connection():
    """Test the Notion API connection"""
    try:
        notion = Client(auth=NOTION_TOKEN)
        # Try a simple search to test connection
        results = notion.search()
        return True, notion
    except Exception as e:
        return False, str(e)

def find_or_create_parent(notion):
    """Try to find an existing page or guide user to create one"""
    print("\n🔍 Searching for available pages...")
    results = notion.search()
    
    pages = [item for item in results.get("results", []) if item["object"] == "page"]
    
    if pages:
        print(f"\n✅ Found {len(pages)} page(s) accessible to your integration:")
        print("-" * 60)
        for idx, page in enumerate(pages[:5], 1):  # Show first 5
            title = "Untitled"
            if "properties" in page:
                for prop_name, prop_value in page["properties"].items():
                    if prop_value.get("type") == "title" and prop_value.get("title"):
                        title = "".join([t.get("plain_text", "") for t in prop_value["title"]])
                        break
            
            page_id = page["id"]
            url = page.get("url", "")
            print(f"{idx}. {title}")
            print(f"   ID: {page_id}")
            print(f"   URL: {url}\n")
        
        if len(pages) == 1:
            return pages[0]["id"], pages[0].get("url", "")
        else:
            print("💡 You can use any of these page IDs as NOTION_PARENT_PAGE_ID")
            return None, None
    else:
        print("ℹ️  No pages found that are shared with your integration.")
        print("\n📝 To create a parent page:")
        print("1. Go to Notion and create a new page")
        print("2. Click '...' (top right) → 'Add connections'")
        print("3. Search for and select your integration")
        print("4. Copy the page ID from the URL")
        print("5. Run: export NOTION_PARENT_PAGE_ID='your_page_id' && python3 notion_import.py")
        return None, None

def main():
    print("🚀 Notion Integration Setup")
    print("=" * 60)
    
    # Test connection
    print("\n1️⃣ Testing Notion API connection...")
    success, result = test_connection()
    
    if not success:
        print(f"❌ Connection failed: {result}")
        print("\nTroubleshooting:")
        print("1. Verify your integration token is correct")
        print("2. Make sure your integration is active")
        print("3. Check that you have workspace access")
        sys.exit(1)
    
    print("✅ Connection successful!")
    notion = result
    
    # Find parent page
    print("\n2️⃣ Looking for parent page...")
    parent_id, parent_url = find_or_create_parent(notion)
    
    if parent_id:
        print(f"\n✅ Found parent page!")
        print(f"📎 Using page ID: {parent_id}")
        
        # Ask if user wants to import now
        print("\n3️⃣ Ready to import WIDVID_OVERVIEW.md")
        print("   Run the following command to import:")
        print(f"   export NOTION_PARENT_PAGE_ID='{parent_id}' && python3 notion_import.py")
        
        # Auto-import if single page found
        if parent_url:
            response = input("\n   Import now? (y/n): ").strip().lower()
            if response == 'y':
                os.environ["NOTION_PARENT_PAGE_ID"] = parent_id
                os.environ["NOTION_TOKEN"] = NOTION_TOKEN
                print("\n📥 Importing content...")
                os.system("python3 notion_import.py")
    else:
        print("\n⚠️  No parent page found. Please create and share a page first.")
        print("\nNext steps:")
        print("1. Create a page in Notion")
        print("2. Share it with your integration")
        print("3. Run this script again or use: python3 notion_import.py")

if __name__ == "__main__":
    main()
