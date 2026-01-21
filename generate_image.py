#!/usr/bin/env python3
"""
Generate images using Replicate fine-tuned model
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Replicate API token
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

if not REPLICATE_API_TOKEN:
    print("❌ Error: REPLICATE_API_TOKEN not found in .env file")
    sys.exit(1)

# Set Replicate API token before importing replicate
os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

# Import replicate after setting the token
import replicate

def generate_image(prompt, output_path=None, model_version="dev"):
    """
    Generate an image using the fine-tuned Replicate model
    
    Args:
        prompt: Text prompt for image generation
        output_path: Optional path to save the image (if None, returns URL only)
        model_version: Model version to use (default: "dev")
    
    Returns:
        dict with 'url' and optionally 'path' if saved
    """
    try:
        print(f"🎨 Generating image with prompt: '{prompt[:50]}...'")
        
        output = replicate.run(
            "sundai-club/anku_with_dog:73a730956d3ea74770fefec5150636c053e3e050801c5b6d4d5a138431ffb898",
            input={
                "prompt": prompt,
                "model": model_version,
                "go_fast": False,
                "lora_scale": 1,
                "megapixels": "1",
                "num_outputs": 1,
                "aspect_ratio": "1:1",
                "output_format": "webp",
                "guidance_scale": 3,
                "output_quality": 80,
                "prompt_strength": 0.8,
                "extra_lora_scale": 1,
                "num_inference_steps": 28
            }
        )
        
        # Get the image URL
        # Replicate returns a list, and each item can be a URL string or object
        if isinstance(output, list) and len(output) > 0:
            image_url = output[0] if isinstance(output[0], str) else (output[0].url if hasattr(output[0], 'url') else str(output[0]))
        else:
            image_url = str(output)
        
        result = {
            "url": image_url,
            "success": True
        }
        
        # Save to disk if output_path provided
        if output_path:
            try:
                import requests
                response = requests.get(image_url, timeout=30)
                response.raise_for_status()
                
                with open(output_path, "wb") as file:
                    file.write(response.content)
                
                result["path"] = output_path
                print(f"✅ Image saved to: {output_path}")
            except Exception as e:
                print(f"⚠️  Warning: Could not save image to disk: {e}")
        
        print(f"✅ Image generated: {image_url}")
        return result
        
    except Exception as e:
        print(f"❌ Error generating image: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }

def generate_image_for_post(post_text, context="social media", output_path=None):
    """
    Generate an image that complements a social media post
    
    Args:
        post_text: The social media post text
        context: Context for image generation (default: "social media")
        output_path: Optional path to save the image
    
    Returns:
        dict with image URL and path
    """
    # Create a prompt based on the post
    # Extract key themes from the post
    prompt = f"Create an engaging {context} image related to: {post_text[:200]}"
    
    return generate_image(prompt, output_path)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        result = generate_image(prompt, output_path="generated_image.webp")
        if result["success"]:
            print(f"\n✅ Image URL: {result['url']}")
            if "path" in result:
                print(f"✅ Saved to: {result['path']}")
    else:
        print("Usage: python3 generate_image.py 'your prompt here'")
        print("\nExample:")
        print("python3 generate_image.py 'AI video generation technology'")
