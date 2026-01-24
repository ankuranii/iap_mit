# Mastodon Integration

Post your generated social media content directly to Mastodon!

## Quick Start

### Option 1: Generate and Post Automatically
```bash
python3 generate_and_post.py
```
This will:
1. Generate a social media post from Widvid docs
2. Show you the generated post
3. Ask for confirmation
4. Post to Mastodon

### Option 2: Post from Generated File
```bash
# First generate posts
python3 generate_social_posts.py

# Then post to Mastodon
python3 post_to_mastodon.py
```

### Option 3: Post Custom Text
```bash
python3 post_to_mastodon.py
# Select option 2
# Enter your custom text
```

## Configuration

### Mastodon Instance
By default, the script uses `https://mastodon.social`. To use a different instance:

```bash
export MASTODON_INSTANCE="https://your-instance.com"
```

### Credentials
Your Mastodon credentials are already configured:
- ✅ Access Token: Set
- ✅ Client Key: Set
- ✅ Client Secret: Set

## Features

- 🐘 **Direct Posting**: Post directly to your Mastodon account
- 📝 **Auto-Format**: Automatically formats posts for Mastodon (500 char limit)
- 🔗 **URL Return**: Get the URL of your posted status
- 📋 **Batch Posting**: Post multiple posts from generated file
- ✅ **Error Handling**: Clear error messages if posting fails

## Mastodon Post Limits

- **Character Limit**: 500 characters
- **Visibility Options**: public, unlisted, private, direct
- **Default**: public

## Example Workflow

```bash
# 1. Generate posts for all platforms
python3 generate_social_posts.py
# Select option 1

# 2. Review generated posts in social_media_posts.txt

# 3. Post to Mastodon
python3 post_to_mastodon.py
# Select option 1
# Choose which post to publish
```

## Troubleshooting

### "401 Unauthorized"
- Check that your access token is correct
- Verify the token hasn't expired
- Ensure the token has write permissions

### "Instance not found"
- Verify your Mastodon instance URL is correct
- Check that the instance is accessible

### "Post too long"
- Mastodon has a 500 character limit
- The script automatically truncates if needed
- Consider generating shorter posts

### "Rate limit exceeded"
- Mastodon has rate limits
- Wait a few minutes before posting again

## API Details

The script uses Mastodon's REST API:
- **Endpoint**: `/api/v1/statuses`
- **Method**: POST
- **Authentication**: Bearer token
- **Content-Type**: application/json

## Next Steps

1. Generate engaging posts
2. Review and customize
3. Post to Mastodon
4. Engage with your audience!

---

**Ready to post?** Run `python3 generate_and_post.py` 🚀
