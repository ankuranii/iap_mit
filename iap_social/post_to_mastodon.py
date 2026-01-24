#!/usr/bin/env python3
"""
Post generated social media content to Mastodon
"""

import os
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Mastodon API credentials
MASTODON_ACCESS_TOKEN = os.getenv("MASTODON_ACCESS_TOKEN")
MASTODON_CLIENT_KEY = os.getenv("MASTODON_CLIENT_KEY")
MASTODON_CLIENT_SECRET = os.getenv("MASTODON_CLIENT_SECRET")
MASTODON_INSTANCE = os.getenv("MASTODON_INSTANCE", "https://mastodon.social")

def upload_media_to_mastodon(image_path_or_url, instance_url=None, access_token=None):
    """Upload media to Mastodon and return media_id"""
    if instance_url is None:
        instance_url = MASTODON_INSTANCE
    
    if access_token is None:
        access_token = MASTODON_ACCESS_TOKEN
    
    url = f"{instance_url}/api/v2/media"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    # Check if it's a URL or local file
    if image_path_or_url.startswith("http://") or image_path_or_url.startswith("https://"):
        # Download the image first
        import tempfile
        response = requests.get(image_path_or_url, timeout=30)
        response.raise_for_status()
        
        # Determine file extension
        ext = "webp"  # Default
        if ".png" in image_path_or_url.lower():
            ext = "png"
        elif ".jpg" in image_path_or_url.lower() or ".jpeg" in image_path_or_url.lower():
            ext = "jpg"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp_file:
            tmp_file.write(response.content)
            image_path = tmp_file.name
    else:
        image_path = image_path_or_url
    
    # Upload the file
    try:
        with open(image_path, "rb") as f:
            files = {"file": f}
            data = {}
            
            response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            media_id = result.get("id")
            
            # Clean up temp file if we created it
            if image_path_or_url.startswith("http://") or image_path_or_url.startswith("https://"):
                os.unlink(image_path)
            
            return {
                "success": True,
                "media_id": media_id
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def post_to_mastodon(content, instance_url=None, access_token=None, image_path_or_url=None):
    """Post content to Mastodon with optional image"""
    if instance_url is None:
        instance_url = MASTODON_INSTANCE
    
    if access_token is None:
        access_token = MASTODON_ACCESS_TOKEN
    
    # Mastodon API endpoint
    url = f"{instance_url}/api/v1/statuses"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Mastodon has a 500 character limit for posts
    if len(content) > 500:
        print(f"⚠️  Warning: Post is {len(content)} characters (Mastodon limit: 500)")
        print("Truncating to 500 characters...")
        content = content[:497] + "..."
    
    data = {
        "status": content,
        "visibility": "public"  # Options: public, unlisted, private, direct
    }
    
    # Upload image if provided
    if image_path_or_url:
        print("📤 Uploading image to Mastodon...")
        media_result = upload_media_to_mastodon(image_path_or_url, instance_url, access_token)
        if media_result["success"]:
            data["media_ids"] = [media_result["media_id"]]
            print("✅ Image uploaded successfully")
        else:
            print(f"⚠️  Warning: Could not upload image: {media_result.get('error')}")
            print("Posting without image...")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return {
            "success": True,
            "id": result.get("id"),
            "url": result.get("url"),
            "content": result.get("content"),
            "created_at": result.get("created_at")
        }
    
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "response": getattr(e.response, 'text', '') if hasattr(e, 'response') else ''
        }

def post_from_file(filename="social_media_posts.txt", instance_url=None):
    """Post content from a generated posts file"""
    if not os.path.exists(filename):
        print(f"❌ Error: {filename} not found")
        print("Generate posts first using: python3 generate_social_posts.py")
        return False
    
    # Read the file and extract posts
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse posts (simple extraction)
    posts = []
    current_platform = None
    current_post = []
    
    for line in content.split('\n'):
        if line.startswith("PLATFORM:"):
            if current_platform and current_post:
                posts.append({
                    "platform": current_platform,
                    "content": '\n'.join(current_post).strip()
                })
            current_platform = line.replace("PLATFORM:", "").strip()
            current_post = []
        elif line.startswith("Character count:") or line.startswith("-" * 80):
            continue
        elif current_platform and line.strip():
            current_post.append(line)
    
    if current_platform and current_post:
        posts.append({
            "platform": current_platform,
            "content": '\n'.join(current_post).strip()
        })
    
    if not posts:
        print("❌ No posts found in file")
        return False
    
    # Display posts and let user choose
    print("📋 Available posts to publish:")
    print("=" * 60)
    for idx, post in enumerate(posts, 1):
        preview = post["content"][:100].replace('\n', ' ')
        print(f"{idx}. {post['platform']} ({len(post['content'])} chars)")
        print(f"   Preview: {preview}...")
        print()
    
    choice = input("Enter post number to publish (or 'all' for all posts): ").strip()
    
    if choice.lower() == 'all':
        selected_posts = posts
    else:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(posts):
                selected_posts = [posts[idx]]
            else:
                print("❌ Invalid selection")
                return False
        except ValueError:
            print("❌ Invalid input")
            return False
    
    # Post to Mastodon
    print(f"\n📤 Posting to Mastodon ({MASTODON_INSTANCE})...")
    print("=" * 60)
    
    for post in selected_posts:
        print(f"\n📱 Posting {post['platform']} post...")
        result = post_to_mastodon(post['content'], instance_url)
        
        if result["success"]:
            print(f"✅ Successfully posted!")
            print(f"🔗 URL: {result.get('url', 'N/A')}")
            print(f"📅 Created: {result.get('created_at', 'N/A')}")
        else:
            print(f"❌ Failed to post: {result.get('error', 'Unknown error')}")
            if result.get('response'):
                print(f"Response: {result['response']}")
    
    return True

def post_direct(content, instance_url=None, visibility="public"):
    """Post content directly to Mastodon"""
    result = post_to_mastodon(content, instance_url)
    
    if result["success"]:
        print(f"✅ Successfully posted to Mastodon!")
        print(f"🔗 URL: {result.get('url', 'N/A')}")
        return True
    else:
        print(f"❌ Failed to post: {result.get('error', 'Unknown error')}")
        if result.get('response'):
            print(f"Response: {result['response']}")
        return False

def main():
    print("🐘 Mastodon Post Publisher")
    print("=" * 60)

    if not MASTODON_ACCESS_TOKEN:
        print("❌ Error: MASTODON_ACCESS_TOKEN not found in .env file")
        sys.exit(1)
    
    # Check if instance URL is set
    instance_url = os.getenv("MASTODON_INSTANCE", MASTODON_INSTANCE)
    print(f"Instance: {instance_url}")
    print(f"Access Token: {MASTODON_ACCESS_TOKEN[:20]}...")
    print()
    
    print("Select an option:")
    print("1. Post from generated social_media_posts.txt file")
    print("2. Post custom text directly")
    print("3. Generate posts and post to Mastodon")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        post_from_file(instance_url=instance_url)
    
    elif choice == "2":
        print("\nEnter your post content (max 500 characters):")
        content = input("> ").strip()
        if content:
            post_direct(content, instance_url)
        else:
            print("❌ No content provided")
    
    elif choice == "3":
        print("\n📱 Generating posts first...")
        os.system("python3 generate_social_posts.py")
        print("\n📤 Now posting to Mastodon...")
        post_from_file(instance_url=instance_url)
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
