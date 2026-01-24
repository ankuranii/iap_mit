# Find & Reply to Mastodon Posts

Automatically find relevant Mastodon posts and generate AI-powered replies using structured outputs.

## Features

- 🔍 **Smart Search**: Searches multiple keywords related to your business
- 🤖 **AI Replies**: Generates contextual, engaging replies using OpenRouter
- 📊 **Structured Outputs**: Gets all replies at once in structured format
- 🎯 **Relevant**: Only finds posts related to AI video generation, diffusion models, etc.
- ✅ **Auto-Post**: Option to automatically post all replies

## Quick Start

### Interactive Mode
```bash
python3 find_and_reply.py
```

This will:
1. Search Mastodon for recent posts about AI video generation
2. Generate contextual replies for each post
3. Show you all replies
4. Ask for confirmation before posting

### Auto-Post Mode
```bash
python3 find_and_reply.py --auto-post
```

Automatically posts all generated replies without confirmation.

## How It Works

### 1. Keyword Search
Searches Mastodon for posts containing:
- "AI video generation"
- "text to video"
- "diffusion models"
- "video AI"
- "generative video"
- "AI content creation"

### 2. Structured Output Generation
Uses OpenRouter with structured JSON output to generate all replies at once:
```json
[
  {
    "post_number": 1,
    "reply": "Your reply text here",
    "tone": "friendly",
    "mentions_widvid": true
  },
  ...
]
```

### 3. Reply Posting
Posts each reply as a response to the original post on Mastodon.

## Customization

### Change Keywords
Edit the `KEYWORDS` list in `find_and_reply.py`:
```python
KEYWORDS = [
    "your keyword",
    "another keyword"
]
```

### Adjust Reply Style
Modify the `system_prompt` in the `generate_replies_structured()` function to change:
- Tone (friendly, professional, casual)
- Length
- Emoji usage
- Hashtag strategy

### Number of Posts
Change `total_limit` in `get_recent_posts()`:
```python
posts = get_recent_posts(KEYWORDS, total_limit=10)  # Get 10 posts
```

## Output

The script displays:
- Found posts with author and preview
- Generated replies with character counts
- Whether each reply mentions Widvid
- Post URLs after successful posting

## Example Output

```
✅ Found 5 recent posts:
1. @user1 - AI video generation is amazing...
2. @user2 - Just tried text-to-video...

✅ Generated 5 replies:
📝 Reply 1 for @user1:
Sounds awesome! 🎥 Being able to turn text into videos...
Character count: 248
Mentions Widvid: True
```

## Safety Features

- **Confirmation Required**: Asks before posting (unless `--auto-post`)
- **Character Limits**: Automatically truncates to 500 chars (Mastodon limit)
- **Error Handling**: Continues even if one reply fails
- **Preview First**: Shows all replies before posting

## Troubleshooting

### "No posts found"
- Try different keywords
- Check your internet connection
- Mastodon search may have rate limits

### "JSON parsing failed"
- The script has a fallback method
- Replies will still be generated
- May need to adjust the prompt

### "Failed to post"
- Check Mastodon API credentials
- Verify you have permission to post
- Check rate limits

## Integration

This script works with:
- `generate_social_posts.py` - Generate your own posts
- `post_to_mastodon.py` - Manual posting tool
- `generate_and_post.py` - Quick post generator

## Best Practices

1. **Review Before Posting**: Always review generated replies
2. **Customize Keywords**: Adjust keywords to match your audience
3. **Monitor Engagement**: Track which replies get responses
4. **Stay Authentic**: Edit replies if needed to match your voice
5. **Respect Rate Limits**: Don't run too frequently

---

**Ready to engage?** Run `python3 find_and_reply.py` 🚀
