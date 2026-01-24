# Image Generation Integration

Generate AI images using your fine-tuned Replicate model and post them with social media content.

## Setup

### 1. Get Replicate API Token

1. Go to [replicate.com](https://replicate.com)
2. Sign in and go to your account settings
3. Copy your API token
4. Add it to your `.env` file:

```bash
REPLICATE_API_TOKEN=your_token_here
```

### 2. Install Dependencies

```bash
pip install -r requirements_social.txt
```

## Usage

### Generate Image Only

```bash
python3 generate_image.py "your prompt here"
```

Example:
```bash
python3 generate_image.py "AI video generation technology, futuristic, digital art"
```

### Generate Post with Image and Post to Mastodon

```bash
python3 generate_and_post_with_image.py
```

This will:
1. Generate a social media post from Widvid docs
2. Generate a complementary image using your fine-tuned model
3. Upload both to Mastodon

## Image Generation Function

The `generate_image.py` script uses your fine-tuned model:
- **Model**: `sundai-club/anku_with_dog:73a730956d3ea74770fefec5150636c053e3e050801c5b6d4d5a138431ffb898`
- **Default Settings**:
  - Aspect Ratio: 1:1 (square)
  - Format: WebP
  - Quality: 80
  - Inference Steps: 28

### Customize Image Generation

Edit `generate_image.py` to adjust:
- `aspect_ratio`: "1:1", "16:9", "9:16", etc.
- `output_format`: "webp", "png", "jpg"
- `guidance_scale`: 1-20 (higher = more adherence to prompt)
- `num_inference_steps`: 20-50 (more = higher quality, slower)

## Integration with Posting

The `post_to_mastodon()` function now supports images:

```python
from post_to_mastodon import post_to_mastodon

# Post with image (local file)
post_to_mastodon(
    "Your post text",
    image_path_or_url="path/to/image.webp"
)

# Post with image (URL)
post_to_mastodon(
    "Your post text",
    image_path_or_url="https://example.com/image.webp"
)
```

## Workflow

### Complete Workflow: Generate + Image + Post

```bash
# All-in-one
python3 generate_and_post_with_image.py
```

### Step-by-Step

```bash
# 1. Generate post
python3 generate_social_posts.py

# 2. Generate image for the post
python3 generate_image.py "AI video generation, futuristic technology"

# 3. Post with image
python3 post_to_mastodon.py
# Select option 2 (custom text)
# Then manually specify image path
```

## Image Prompts

The script automatically creates prompts based on your post content. You can also:

1. **Use post text directly**: The script extracts key themes
2. **Custom prompts**: Edit `generate_image_for_post()` function
3. **Manual prompts**: Use `generate_image.py` directly

## Tips

- **Image Size**: Mastodon supports up to 10MB images
- **Format**: WebP is recommended for smaller file sizes
- **Aspect Ratio**: 1:1 works best for social media
- **Quality**: 80% is a good balance between quality and file size

## Troubleshooting

### "REPLICATE_API_TOKEN not found"
- Add your token to `.env` file
- Make sure `.env` is in the project root

### "Image generation failed"
- Check your Replicate API token is valid
- Verify you have credits on Replicate
- Check the model is accessible

### "Image upload failed"
- Check image file size (must be < 10MB)
- Verify image format is supported (WebP, PNG, JPG)
- Check your internet connection

### "Model not found"
- Verify the model path is correct
- Check you have access to the model
- Ensure the model version exists

---

**Ready to create visual posts?** Run `python3 generate_and_post_with_image.py` 🎨
