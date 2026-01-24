# Connecting to Notion

This guide will help you import the Widvid overview document into Notion.

## Prerequisites

1. A Notion account
2. Python 3.7+ installed
3. A Notion integration token

## Setup Steps

### 1. Create a Notion Integration

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **"+ New integration"**
3. Give it a name (e.g., "Widvid Import")
4. Select the workspace where you want to add the document
5. Click **"Submit"**
6. Copy the **"Internal Integration Token"** (starts with `secret_`)

### 2. Share a Page with the Integration

1. Open the Notion page where you want to add the Widvid overview
2. Click the **"..."** menu in the top right
3. Click **"Add connections"** or **"Connections"**
4. Search for and select your integration
5. Copy the **Page ID** from the URL:
   - URL format: `https://www.notion.so/Your-Page-Title-XXXXXXXXXXXX`
   - The ID is the part after the last dash (32 characters)

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables

```bash
export NOTION_TOKEN="your_integration_token_here"
export NOTION_PARENT_PAGE_ID="your_page_id_here"
```

Or create a `.env` file:

```bash
NOTION_TOKEN=your_integration_token_here
NOTION_PARENT_PAGE_ID=your_page_id_here
```

### 5. Run the Import Script

```bash
python notion_import.py
```

The script will:
- Read `WIDVID_OVERVIEW.md`
- Convert it to Notion blocks
- Create a new page in your specified Notion workspace
- Display the URL of the created page

## Alternative: Manual Import

If you prefer to import manually:

1. Open Notion
2. Create a new page
3. Use Notion's **"Import"** feature:
   - Click **"..."** → **"Import"**
   - Select **"Markdown"**
   - Upload `WIDVID_OVERVIEW.md`

## Troubleshooting

### "Unauthorized" Error
- Make sure you've shared the parent page with your integration
- Verify your integration token is correct

### "Parent page not found"
- Check that the page ID is correct (32 characters, no dashes)
- Ensure the page is shared with your integration

### Blocks not appearing correctly
- Notion has some limitations with complex markdown
- You may need to manually adjust formatting after import
