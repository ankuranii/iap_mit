#!/usr/bin/env python3
"""
Helper script to list Notion pages and databases
"""

import os
import sys
from notion_client import Client

def list_pages_and_databases(notion_token):
    """List available pages and databases in the workspace"""
    notion = Client(auth=notion_token)
    
    try:
        # Search for all pages and databases
        results = notion.search()
        
        pages = []
        databases = []
        
        for item in results.get("results", []):
            if item["object"] == "page":
                pages.append(item)
            elif item["object"] == "database":
                databases.append(item)
        
        if pages:
            print("📄 Available Pages:")
            print("-" * 60)
            for item in pages:
                title = "Untitled"
                if "properties" in item:
                    for prop_name, prop_value in item["properties"].items():
                        if prop_value.get("type") == "title" and prop_value.get("title"):
                            title = "".join([t.get("plain_text", "") for t in prop_value["title"]])
                            break
                
                page_id = item["id"]
                url = item.get("url", "")
                print(f"Title: {title}")
                print(f"ID: {page_id}")
                print(f"URL: {url}")
                print()
        
        if databases:
            print("🗄️  Available Databases:")
            print("-" * 60)
            for item in databases:
                title = "Untitled"
                if "title" in item and item["title"]:
                    title = "".join([t.get("plain_text", "") for t in item["title"]])
                
                db_id = item["id"]
                url = item.get("url", "")
                print(f"Title: {title}")
                print(f"ID: {db_id}")
                print(f"URL: {url}")
                print()
        
        if not pages and not databases:
            print("ℹ️  No pages or databases found.")
            print("\nTo create a page:")
            print("1. Go to Notion and create a new page")
            print("2. Click '...' → 'Add connections' → Select your integration")
            print("3. Copy the page ID from the URL")
        
        print("\n💡 To use a page as parent:")
        print("   1. Copy the ID from above")
        print("   2. Make sure the page is shared with your integration")
        print("   3. Run: export NOTION_PARENT_PAGE_ID='your_page_id'")
        print("   4. Then run: python notion_import.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure:")
        print("1. Your integration token is correct")
        print("2. Your integration has access to the workspace")
        sys.exit(1)

def main():
    notion_token = os.getenv("NOTION_TOKEN")
    
    if not notion_token:
        print("❌ Error: NOTION_TOKEN environment variable not set")
        print("\nSet it with:")
        print("export NOTION_TOKEN='your_token_here'")
        sys.exit(1)
    
    list_pages_and_databases(notion_token)

if __name__ == "__main__":
    main()
