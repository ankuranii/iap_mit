#!/usr/bin/env python3
"""
Generate social media posts and automatically post to Mastodon
"""

import os
import sys
from dotenv import load_dotenv
from generate_social_posts import load_widvid_docs, generate_social_post
from openai import OpenAI
from post_to_mastodon import post_to_mastodon, MASTODON_INSTANCE, MASTODON_ACCESS_TOKEN

# Load environment variables
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    print("❌ Error: OPENROUTER_API_KEY not found in .env file")
    sys.exit(1)

def main():
    print("🚀 Generate & Post to Mastodon")
    print("=" * 60)
    
    # Initialize OpenRouter client
    print("\n🔗 Connecting to OpenRouter...")
    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )
    print("✅ Connected!")
    
    # Load documentation
    print("\n📄 Loading Widvid documentation...")
    doc_content = load_widvid_docs()
    print(f"✅ Loaded {len(doc_content)} characters")
    
    # Generate post
    print("\n🤖 Generating Mastodon post...")
    post = generate_social_post(
        client, 
        doc_content, 
        platform="twitter",  # Mastodon is similar to Twitter
        post_type="general"
    )
    
    if not post:
        print("❌ Failed to generate post")
        sys.exit(1)
    
    print("\n📝 Generated Post:")
    print("-" * 60)
    print(post)
    print("-" * 60)
    print(f"Character count: {len(post)}")
    
    # Confirm before posting
    print(f"\n🐘 Ready to post to Mastodon ({MASTODON_INSTANCE})")
    confirm = input("Post now? (y/n): ").strip().lower()
    
    if confirm == 'y':
        print("\n📤 Posting to Mastodon...")
        result = post_to_mastodon(post, MASTODON_INSTANCE, MASTODON_ACCESS_TOKEN)
        
        if result["success"]:
            print(f"\n✅ Successfully posted!")
            print(f"🔗 URL: {result.get('url', 'N/A')}")
            print(f"📅 Created: {result.get('created_at', 'N/A')}")
        else:
            print(f"\n❌ Failed to post: {result.get('error', 'Unknown error')}")
            if result.get('response'):
                print(f"Response: {result['response']}")
    else:
        print("Post cancelled")

if __name__ == "__main__":
    main()
