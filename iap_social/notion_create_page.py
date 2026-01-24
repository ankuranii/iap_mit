#!/usr/bin/env python3
"""
Create a Notion page directly in the workspace and import the Widvid overview
"""

import os
import sys
from notion_client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Your Notion token
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
if not NOTION_TOKEN:
    print("❌ Error: NOTION_TOKEN not found in .env file")
    sys.exit(1)

def create_workspace_page(notion, title):
    """Try to create a page at the workspace level"""
    try:
        # Try to create a page without a parent (workspace level)
        # This requires the integration to have workspace access
        page = notion.pages.create(
            parent={"workspace": True},
            properties={
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                }
            }
        )
        return page["id"], page.get("url", "")
    except Exception as e:
        error_msg = str(e)
        if "workspace" in error_msg.lower() or "parent" in error_msg.lower():
            return None, None
        raise

def main():
    notion = Client(auth=NOTION_TOKEN)
    
    print("🔗 Connecting to Notion...")
    
    # Try to create a page at workspace level
    print("📄 Attempting to create page in workspace...")
    page_id, page_url = create_workspace_page(notion, "Widvid: Comprehensive Company Overview")
    
    if page_id:
        print(f"✅ Successfully created page!")
        print(f"📎 Page ID: {page_id}")
        print(f"🔗 URL: {page_url}")
        print("\nNow importing content...")
        
        # Now import the content
        os.environ["NOTION_TOKEN"] = NOTION_TOKEN
        os.environ["NOTION_PARENT_PAGE_ID"] = page_id
        
        # Import the markdown content
        from notion_import import markdown_to_notion_blocks
        
        md_file = "WIDVID_OVERVIEW.md"
        if not os.path.exists(md_file):
            print(f"❌ Error: {md_file} not found")
            sys.exit(1)
        
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove title from content (already in page title)
        content_lines = content.split('\n')
        if content_lines[0].startswith('#'):
            content = '\n'.join(content_lines[1:])
        
        # Convert and add blocks
        blocks = markdown_to_notion_blocks(content)
        
        # Add content blocks (chunked for API limits)
        chunk_size = 100
        for i in range(0, len(blocks), chunk_size):
            chunk = blocks[i:i+chunk_size]
            notion.blocks.children.append(block_id=page_id, children=chunk)
        
        print(f"✅ Content imported successfully!")
        print(f"🔗 View your page: {page_url}")
        
    else:
        print("ℹ️  Cannot create page at workspace level.")
        print("\nYou need to provide a parent page ID.")
        print("\nTo do this:")
        print("1. Create a page in Notion")
        print("2. Share it with your integration (click '...' → 'Add connections')")
        print("3. Get the page ID from the URL")
        print("4. Run: export NOTION_PARENT_PAGE_ID='your_page_id' && python3 notion_import.py")
        print("\nOr run: python3 notion_setup.py to see available pages")

if __name__ == "__main__":
    main()
