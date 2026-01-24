#!/usr/bin/env python3
"""
Script to import WIDVID_OVERVIEW.md into Notion
Requires: pip install notion-client
"""

import os
import sys
from notion_client import Client
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

def markdown_to_notion_blocks(markdown_content):
    """Convert markdown content to Notion blocks"""
    blocks = []
    lines = markdown_content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Headers
        if line.startswith('# '):
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": line[2:].strip()}}]
                }
            })
        elif line.startswith('## '):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": line[3:].strip()}}]
                }
            })
        elif line.startswith('### '):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": line[4:].strip()}}]
                }
            })
        # Horizontal rule
        elif line.startswith('---'):
            blocks.append({
                "object": "block",
                "type": "divider",
                "divider": {}
            })
        # Bullet lists
        elif line.startswith('- ') or line.startswith('* '):
            items = []
            content = line[2:].strip()
            # Check for bold text
            rich_text = parse_rich_text(content)
            items.append(rich_text)
            
            # Collect consecutive list items
            i += 1
            while i < len(lines) and (lines[i].strip().startswith('- ') or lines[i].strip().startswith('* ')):
                content = lines[i].strip()[2:].strip()
                items.append(parse_rich_text(content))
                i += 1
            i -= 1  # Adjust for outer loop increment
            
            for item in items:
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": item
                    }
                })
        # Numbered lists
        elif re.match(r'^\d+\.\s', line):
            items = []
            content = re.sub(r'^\d+\.\s', '', line).strip()
            items.append(parse_rich_text(content))
            
            # Collect consecutive numbered items
            i += 1
            while i < len(lines) and re.match(r'^\d+\.\s', lines[i].strip()):
                content = re.sub(r'^\d+\.\s', '', lines[i].strip()).strip()
                items.append(parse_rich_text(content))
                i += 1
            i -= 1
            
            for item in items:
                blocks.append({
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": item
                    }
                })
        # Regular paragraphs
        else:
            rich_text = parse_rich_text(line)
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": rich_text
                }
            })
        
        i += 1
    
    return blocks

def parse_rich_text(text):
    """Parse markdown formatting (bold, italic) into Notion rich text format"""
    rich_text = []
    i = 0
    
    while i < len(text):
        # Bold text **text**
        if text[i:i+2] == '**' and text.find('**', i+2) != -1:
            end = text.find('**', i+2)
            rich_text.append({
                "type": "text",
                "text": {"content": text[i+2:end]},
                "annotations": {"bold": True}
            })
            i = end + 2
        # Regular text
        else:
            start = i
            # Find next formatting or end of string
            next_bold = text.find('**', i)
            if next_bold == -1:
                next_bold = len(text)
            
            if start < next_bold:
                content = text[start:next_bold]
                if content:
                    rich_text.append({
                        "type": "text",
                        "text": {"content": content}
                    })
                i = next_bold
            else:
                i += 1
    
    return rich_text if rich_text else [{"type": "text", "text": {"content": text}}]

def create_notion_page(notion_token, parent_page_id, title, content):
    """Create a Notion page with the given content"""
    notion = Client(auth=notion_token)
    
    # Convert markdown to Notion blocks
    blocks = markdown_to_notion_blocks(content)
    
    # Create the page
    try:
        page = notion.pages.create(
            parent={"page_id": parent_page_id},
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
        
        page_id = page["id"]
        
        # Add content blocks (Notion API has a limit, so we'll chunk them)
        chunk_size = 100
        for i in range(0, len(blocks), chunk_size):
            chunk = blocks[i:i+chunk_size]
            notion.blocks.children.append(block_id=page_id, children=chunk)
        
        print(f"✅ Successfully created Notion page: {page['url']}")
        return page_id
        
    except Exception as e:
        print(f"❌ Error creating Notion page: {e}")
        sys.exit(1)

def main():
    # Read environment variables
    notion_token = os.getenv("NOTION_TOKEN")
    parent_page_id = os.getenv("NOTION_PARENT_PAGE_ID")
    
    if not notion_token:
        print("❌ Error: NOTION_TOKEN not found in .env file")
        print("Please add NOTION_TOKEN to your .env file")
        sys.exit(1)
    
    if not parent_page_id:
        print("❌ Error: NOTION_PARENT_PAGE_ID environment variable not set")
        print("\nTo get your parent page ID:")
        print("1. Open the Notion page where you want to add the document")
        print("2. Make sure the page is shared with your integration")
        print("3. Look at the URL: https://www.notion.so/Your-Page-Title-XXXXXXXXXXXX")
        print("4. Copy the ID (the part after the last dash, remove dashes)")
        print("5. Set it as: export NOTION_PARENT_PAGE_ID='your_page_id'")
        print("\nOr run: python3 notion_setup.py to see available pages")
        sys.exit(1)
    
    # Read the markdown file
    md_file = "WIDVID_OVERVIEW.md"
    if not os.path.exists(md_file):
        print(f"❌ Error: {md_file} not found")
        sys.exit(1)
    
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract title from first line
    first_line = content.split('\n')[0]
    if first_line.startswith('# '):
        title = first_line[2:].strip()
    else:
        title = "Widvid: Comprehensive Company Overview"
    
    # Remove the title from content (already in page title)
    content_lines = content.split('\n')
    if content_lines[0].startswith('#'):
        content = '\n'.join(content_lines[1:])
    
    print("📝 Creating Notion page...")
    create_notion_page(notion_token, parent_page_id, title, content)

if __name__ == "__main__":
    main()
