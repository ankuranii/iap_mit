#!/usr/bin/env python3
"""
Find recent Mastodon posts related to your business and generate replies
Uses structured outputs to generate all replies at once
"""

import os
import sys
import requests
import json
from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MASTODON_ACCESS_TOKEN = os.getenv("MASTODON_ACCESS_TOKEN")
MASTODON_INSTANCE = os.getenv("MASTODON_INSTANCE", "https://mastodon.social")

if not OPENROUTER_API_KEY:
    print("❌ Error: OPENROUTER_API_KEY not found in .env file")
    sys.exit(1)
if not MASTODON_ACCESS_TOKEN:
    print("❌ Error: MASTODON_ACCESS_TOKEN not found in .env file")
    sys.exit(1)

# Business keywords related to Widvid
KEYWORDS = [
    "AI video generation",
    "text to video",
    "diffusion models",
    "video AI",
    "generative video",
    "AI content creation"
]

def search_mastodon(keyword, limit=5):
    """Search Mastodon for posts containing the keyword"""
    url = f"{MASTODON_INSTANCE}/api/v2/search"
    
    headers = {
        "Authorization": f"Bearer {MASTODON_ACCESS_TOKEN}"
    }
    
    params = {
        "q": keyword,
        "type": "statuses",
        "limit": limit,
        "resolve": True
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        statuses = data.get("statuses", [])
        
        return statuses
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error searching Mastodon: {e}")
        return []

def get_recent_posts(keywords, total_limit=5):
    """Get recent posts across multiple keywords"""
    all_posts = []
    seen_ids = set()
    
    for keyword in keywords:
        print(f"🔍 Searching for: '{keyword}'...")
        posts = search_mastodon(keyword, limit=10)
        
        for post in posts:
            post_id = post.get("id")
            if post_id not in seen_ids:
                seen_ids.add(post_id)
                all_posts.append({
                    "id": post_id,
                    "url": post.get("url", ""),
                    "content": post.get("content", ""),
                    "account": post.get("account", {}).get("acct", "unknown"),
                    "created_at": post.get("created_at", ""),
                    "keyword": keyword
                })
        
        if len(all_posts) >= total_limit:
            break
    
    # Sort by created_at (most recent first) and limit
    all_posts.sort(key=lambda x: x["created_at"], reverse=True)
    return all_posts[:total_limit]

def generate_replies_structured(client, posts, widvid_docs):
    """Generate replies for all posts using structured outputs"""
    
    # Prepare posts data for the LLM
    posts_data = []
    for idx, post in enumerate(posts, 1):
        # Clean HTML content (basic)
        content = post["content"]
        # Remove HTML tags (simple approach)
        import re
        content = re.sub(r'<[^>]+>', '', content)
        content = content.replace('&nbsp;', ' ').strip()
        
        posts_data.append({
            "post_number": idx,
            "author": post["account"],
            "content": content[:500],  # Limit content length
            "url": post["url"],
            "keyword": post["keyword"]
        })
    
    system_prompt = """You are a social media manager for Widvid, an AI video generation platform.
Generate engaging, helpful replies to Mastodon posts about AI video generation, diffusion models, or related topics.

Guidelines:
- Be friendly and conversational
- Mention Widvid naturally when relevant
- Provide value, don't just promote
- Keep replies concise (under 500 characters for Mastodon)
- Use emojis sparingly and appropriately
- Include relevant hashtags when appropriate
- Be authentic and helpful

Return structured JSON with a reply for each post."""

    user_message = f"""Here are {len(posts_data)} recent Mastodon posts related to AI video generation:

{json.dumps(posts_data, indent=2)}

Here's information about Widvid:
{widvid_docs[:4000]}

Generate engaging replies for each post. Return a JSON array with this structure:
[
  {{
    "post_number": 1,
    "reply": "Your reply text here",
    "tone": "friendly/informative/supportive",
    "mentions_widvid": true/false
  }},
  ...
]

Make each reply:
- Relevant to the original post
- Engaging and conversational
- Under 500 characters
- Valuable to the conversation"""

    try:
        # Use structured output format
        response = client.chat.completions.create(
            model="nvidia/nemotron-3-nano-30b-a3b:free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=2000,
            response_format={"type": "json_object"}  # Request JSON output
        )
        
        # Parse the response
        response_text = response.choices[0].message.content.strip()
        
        # Try to extract JSON from the response
        # Sometimes the model wraps JSON in markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        # Parse JSON
        try:
            data = json.loads(response_text)
            
            # Handle both object and array formats
            if isinstance(data, dict):
                if "replies" in data:
                    replies = data["replies"]
                elif "responses" in data:
                    replies = data["responses"]
                else:
                    # Assume the dict values are replies
                    replies = list(data.values())
            else:
                replies = data
            
            # Ensure we have the right structure
            if isinstance(replies, list) and len(replies) > 0:
                return replies
            else:
                # Fallback: create replies from the data
                return [{"reply": str(data), "post_number": i+1} for i in range(len(posts))]
        
        except json.JSONDecodeError:
            # Fallback: split response into individual replies
            print("⚠️  JSON parsing failed, using fallback method")
            lines = response_text.split('\n')
            replies = []
            current_reply = []
            
            for line in lines:
                if line.strip() and not line.strip().startswith('{') and not line.strip().startswith('['):
                    current_reply.append(line.strip())
                elif current_reply:
                    replies.append({
                        "reply": ' '.join(current_reply),
                        "post_number": len(replies) + 1
                    })
                    current_reply = []
            
            if current_reply:
                replies.append({
                    "reply": ' '.join(current_reply),
                    "post_number": len(replies) + 1
                })
            
            return replies[:len(posts)]
    
    except Exception as e:
        print(f"❌ Error generating replies: {e}")
        import traceback
        traceback.print_exc()
        return None

def post_reply(status_id, reply_text, in_reply_to_id=None):
    """Post a reply to a Mastodon status"""
    url = f"{MASTODON_INSTANCE}/api/v1/statuses"
    
    headers = {
        "Authorization": f"Bearer {MASTODON_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Mastodon has a 500 character limit
    if len(reply_text) > 500:
        reply_text = reply_text[:497] + "..."
    
    data = {
        "status": reply_text,
        "in_reply_to_id": in_reply_to_id or status_id,
        "visibility": "public"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        return {
            "success": True,
            "id": result.get("id"),
            "url": result.get("url"),
            "created_at": result.get("created_at")
        }
    
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    print("🔍 Finding Recent Posts & Generating Replies")
    print("=" * 60)
    
    # Load Widvid docs
    print("\n📄 Loading Widvid documentation...")
    try:
        with open("WIDVID_OVERVIEW.md", 'r', encoding='utf-8') as f:
            widvid_docs = f.read()
        print(f"✅ Loaded {len(widvid_docs)} characters")
    except FileNotFoundError:
        print("⚠️  WIDVID_OVERVIEW.md not found, using minimal context")
        widvid_docs = "Widvid is an AI video generation platform using diffusion models."
    
    # Search for posts
    print("\n🔍 Searching Mastodon for relevant posts...")
    posts = get_recent_posts(KEYWORDS, total_limit=5)
    
    if not posts:
        print("❌ No posts found. Try different keywords or check your connection.")
        return
    
    print(f"\n✅ Found {len(posts)} recent posts:")
    print("-" * 60)
    for idx, post in enumerate(posts, 1):
        content = post["content"][:100].replace('\n', ' ')
        print(f"{idx}. @{post['account']} - {content}...")
        print(f"   Keyword: {post['keyword']}")
        print(f"   URL: {post['url']}\n")
    
    # Generate replies using structured outputs
    print("🤖 Generating replies using AI (structured output)...")
    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )
    
    replies = generate_replies_structured(client, posts, widvid_docs)
    
    if not replies:
        print("❌ Failed to generate replies")
        return
    
    # Display generated replies
    print(f"\n✅ Generated {len(replies)} replies:")
    print("=" * 60)
    
    for idx, reply_data in enumerate(replies):
        post = posts[idx] if idx < len(posts) else None
        reply_text = reply_data.get("reply", str(reply_data))
        
        print(f"\n📝 Reply {idx + 1} for @{post['account'] if post else 'unknown'}:")
        print("-" * 60)
        print(reply_text)
        print(f"Character count: {len(reply_text)}")
        if "mentions_widvid" in reply_data:
            print(f"Mentions Widvid: {reply_data['mentions_widvid']}")
    
    # Ask for confirmation
    print("\n" + "=" * 60)
    try:
        confirm = input("Post all replies to Mastodon? (y/n): ").strip().lower()
    except EOFError:
        # Non-interactive mode - ask via command line arg
        if len(sys.argv) > 1 and sys.argv[1] == "--auto-post":
            confirm = 'y'
            print("Auto-posting mode enabled")
        else:
            print("\n💡 To auto-post, run: python3 find_and_reply.py --auto-post")
            print("💡 Or review the replies above and post manually using post_to_mastodon.py")
            return
    
    if confirm == 'y':
        print("\n📤 Posting replies to Mastodon...")
        print("=" * 60)
        
        for idx, reply_data in enumerate(replies):
            if idx >= len(posts):
                break
            
            post = posts[idx]
            reply_text = reply_data.get("reply", str(reply_data))
            
            print(f"\n📤 Posting reply {idx + 1} to @{post['account']}...")
            result = post_reply(post["id"], reply_text, post["id"])
            
            if result["success"]:
                print(f"✅ Posted successfully!")
                print(f"🔗 URL: {result.get('url', 'N/A')}")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        
        print("\n✅ All replies posted!")
    else:
        print("Posting cancelled. Replies are shown above.")

if __name__ == "__main__":
    main()
