#!/usr/bin/env python3
"""
Generate social media posts from Widvid documentation using OpenRouter
"""

import os
import sys
from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenRouter API configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    print("❌ Error: OPENROUTER_API_KEY not found in .env file")
    sys.exit(1)

def load_widvid_docs():
    """Load the Widvid overview document"""
    md_file = "WIDVID_OVERVIEW.md"
    if not os.path.exists(md_file):
        print(f"❌ Error: {md_file} not found")
        sys.exit(1)
    
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return content

def generate_social_post(client, doc_content, platform="twitter", post_type="general", topic=None):
    """Generate a social media post using OpenRouter"""
    
    # Platform-specific guidelines
    platform_guidelines = {
        "twitter": {
            "max_length": 280,
            "style": "Engaging, concise, use hashtags, emojis when appropriate",
            "format": "Tweet format with line breaks"
        },
        "linkedin": {
            "max_length": 3000,
            "style": "Professional, informative, thought leadership tone",
            "format": "LinkedIn post with engaging hook and call-to-action"
        },
        "instagram": {
            "max_length": 2200,
            "style": "Visual storytelling, engaging captions, use emojis, hashtags",
            "format": "Instagram caption with relevant hashtags"
        },
        "facebook": {
            "max_length": 5000,
            "style": "Conversational, engaging, community-focused",
            "format": "Facebook post with engaging content"
        }
    }
    
    guidelines = platform_guidelines.get(platform.lower(), platform_guidelines["twitter"])
    
    # Post type prompts
    post_types = {
        "general": "Create an engaging post about Widvid's AI video generation platform",
        "product": "Highlight Widvid's key product features and capabilities",
        "technology": "Focus on Widvid's cutting-edge diffusion model technology",
        "use_case": "Showcase specific use cases and applications of Widvid",
        "announcement": "Create an announcement-style post about Widvid",
        "educational": "Create an educational post explaining AI video generation"
    }
    
    post_prompt = post_types.get(post_type.lower(), post_types["general"])
    
    if topic:
        post_prompt += f" focused on: {topic}"
    
    system_prompt = f"""You are a social media content creator specializing in AI and technology companies.

Generate a {platform} post about Widvid based on the provided documentation.

Platform Guidelines:
- Style: {guidelines['style']}
- Max length: {guidelines['max_length']} characters
- Format: {guidelines['format']}

Requirements:
- Make it engaging and shareable
- Include relevant information from the documentation
- Use appropriate tone for {platform}
- Include a call-to-action when appropriate
- Ensure accuracy based on the provided documentation"""

    user_message = f"""{post_prompt}

Here is the Widvid company documentation:

{doc_content[:8000]}  # Limit to avoid token limits

Generate a compelling {platform} post that will engage the audience and showcase Widvid's value proposition."""

    try:
        response = client.chat.completions.create(
            model="nvidia/nemotron-3-nano-30b-a3b:free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.8,
            max_tokens=1000
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"❌ Error generating post: {e}")
        return None

def generate_multiple_posts(client, doc_content, platforms=None, count=3):
    """Generate multiple social media posts"""
    if platforms is None:
        platforms = ["twitter", "linkedin", "instagram"]
    
    posts = {}
    
    for platform in platforms:
        print(f"\n📱 Generating {platform} post...")
        post = generate_social_post(client, doc_content, platform=platform)
        if post:
            posts[platform] = post
            print(f"✅ {platform.capitalize()} post generated!")
        else:
            print(f"❌ Failed to generate {platform} post")
    
    return posts

def save_posts(posts, filename="social_media_posts.txt"):
    """Save generated posts to a file"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("WIDVID SOCIAL MEDIA POSTS\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        for platform, post in posts.items():
            f.write(f"\n{'=' * 80}\n")
            f.write(f"PLATFORM: {platform.upper()}\n")
            f.write(f"{'=' * 80}\n\n")
            f.write(post)
            f.write("\n\n")
            f.write(f"Character count: {len(post)}\n")
            f.write(f"{'-' * 80}\n\n")
    
    print(f"\n💾 Posts saved to {filename}")

def main():
    print("🚀 Widvid Social Media Post Generator")
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
    print(f"✅ Loaded {len(doc_content)} characters of documentation")
    
    # Menu
    print("\n" + "=" * 60)
    print("Select an option:")
    print("1. Generate posts for all platforms (Twitter, LinkedIn, Instagram)")
    print("2. Generate Twitter post")
    print("3. Generate LinkedIn post")
    print("4. Generate Instagram post")
    print("5. Generate custom post (choose platform and type)")
    print("6. Generate multiple variations")
    
    choice = input("\nEnter choice (1-6): ").strip()
    
    posts = {}
    
    if choice == "1":
        print("\n📱 Generating posts for all platforms...")
        posts = generate_multiple_posts(client, doc_content)
    
    elif choice == "2":
        post = generate_social_post(client, doc_content, platform="twitter")
        if post:
            posts["twitter"] = post
    
    elif choice == "3":
        post = generate_social_post(client, doc_content, platform="linkedin")
        if post:
            posts["linkedin"] = post
    
    elif choice == "4":
        post = generate_social_post(client, doc_content, platform="instagram")
        if post:
            posts["instagram"] = post
    
    elif choice == "5":
        print("\nAvailable platforms: twitter, linkedin, instagram, facebook")
        platform = input("Enter platform: ").strip()
        print("\nAvailable types: general, product, technology, use_case, announcement, educational")
        post_type = input("Enter post type: ").strip()
        topic = input("Enter specific topic (optional, press Enter to skip): ").strip() or None
        
        post = generate_social_post(client, doc_content, platform=platform, post_type=post_type, topic=topic)
        if post:
            posts[f"{platform}_{post_type}"] = post
    
    elif choice == "6":
        count = int(input("How many variations? (default 3): ").strip() or "3")
        platform = input("Platform (twitter/linkedin/instagram, default: twitter): ").strip() or "twitter"
        
        print(f"\n📱 Generating {count} {platform} post variations...")
        for i in range(count):
            post = generate_social_post(client, doc_content, platform=platform)
            if post:
                posts[f"{platform}_variation_{i+1}"] = post
                print(f"✅ Variation {i+1} generated!")
    
    else:
        print("❌ Invalid choice")
        sys.exit(1)
    
    # Display and save posts
    if posts:
        print("\n" + "=" * 60)
        print("GENERATED POSTS:")
        print("=" * 60)
        
        for platform, post in posts.items():
            print(f"\n{'─' * 60}")
            print(f"📱 {platform.upper()}")
            print(f"{'─' * 60}")
            print(post)
            print(f"\nCharacter count: {len(post)}")
        
        # Save to file
        save_posts(posts)
        
        print("\n✅ Done! Posts saved to social_media_posts.txt")
    else:
        print("\n❌ No posts were generated")

if __name__ == "__main__":
    main()
