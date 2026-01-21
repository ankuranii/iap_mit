# Social Media Post Generator

Generate engaging social media posts for Widvid using AI, powered by OpenRouter.

## Features

- 🤖 **AI-Powered**: Uses OpenRouter with advanced language models
- 📱 **Multi-Platform**: Generate posts for Twitter, LinkedIn, Instagram, Facebook
- 🎯 **Customizable**: Choose post types (product, technology, use cases, etc.)
- 📄 **Document-Based**: Uses Widvid company documentation as source
- 💾 **Auto-Save**: Saves all generated posts to a file

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_social.txt
```

Or:
```bash
pip install openai
```

### 2. Run the Generator

```bash
python3 generate_social_posts.py
```

### 3. Follow the Interactive Menu

The script will guide you through:
- Selecting platforms (Twitter, LinkedIn, Instagram, Facebook)
- Choosing post types (general, product, technology, use cases, etc.)
- Generating multiple variations

## Usage Examples

### Generate All Platform Posts
```bash
python3 generate_social_posts.py
# Select option 1
```

### Generate Twitter Post
```bash
python3 generate_social_posts.py
# Select option 2
```

### Generate Custom Post
```bash
python3 generate_social_posts.py
# Select option 5
# Choose platform: linkedin
# Choose type: product
# Enter topic: API capabilities (optional)
```

### Generate Multiple Variations
```bash
python3 generate_social_posts.py
# Select option 6
# Enter count: 5
# Choose platform: twitter
```

## Post Types

- **general**: General company/product post
- **product**: Highlight product features
- **technology**: Focus on technical innovations
- **use_case**: Showcase specific applications
- **announcement**: Announcement-style posts
- **educational**: Educational content about AI video generation

## Platform Guidelines

### Twitter
- Max 280 characters
- Engaging, concise
- Use hashtags and emojis
- Thread-friendly format

### LinkedIn
- Up to 3000 characters
- Professional tone
- Thought leadership
- Call-to-action included

### Instagram
- Up to 2200 characters
- Visual storytelling
- Emojis and hashtags
- Engaging captions

### Facebook
- Up to 5000 characters
- Conversational tone
- Community-focused
- Engaging content

## Output

Generated posts are saved to `social_media_posts.txt` with:
- Platform name
- Full post content
- Character count
- Generation timestamp

## Configuration

The script uses:
- **API**: OpenRouter
- **Model**: `nvidia/nemotron-3-nano-30b-a3b:free`
- **Source**: `WIDVID_OVERVIEW.md`

To change the API key, edit `generate_social_posts.py`:
```python
OPENROUTER_API_KEY = "your_key_here"
```

## Testing

Test the OpenRouter connection:
```bash
python3 test_openrouter.py
```

## Example Output

```
📱 TWITTER
────────────────────────────────────────────────────────
🎬 Transform text into stunning videos in seconds! 

Widvid's AI-powered platform uses cutting-edge diffusion 
models to create professional video content. Perfect for 
creators, marketers, and businesses.

✨ 1080p quality
⚡ Under 10 seconds generation
🎨 Multiple styles supported

Try it today! #AIVideo #ContentCreation #Widvid

Character count: 245
```

## Troubleshooting

### "API key error"
- Verify your OpenRouter API key is correct
- Check that the key has sufficient credits

### "Model not available"
- The free model may have rate limits
- Try again in a few moments

### "Document not found"
- Ensure `WIDVID_OVERVIEW.md` exists in the same directory

## Next Steps

1. Generate posts for your content calendar
2. Review and customize as needed
3. Schedule posts using your social media management tool
4. Track engagement and iterate

---

**Ready to generate?** Run `python3 generate_social_posts.py` 🚀
