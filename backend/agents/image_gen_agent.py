import logging
import os
import re
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

FORMAT_MAP = {
    "meta_feed": {"size": "1024x1024", "dalle_key": "dalle_prompt_meta_feed"},
    "meta_story": {"size": "1024x1792", "dalle_key": "dalle_prompt_meta_story"},
    "tiktok": {"size": "1024x1792", "dalle_key": "dalle_prompt_tiktok"},
}


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text[:40].strip("_")


async def _generate_image(prompt: str, size: str) -> str:
    """Call DALL-E 3 and return the image URL."""
    import openai

    client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = await client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size=size,
        quality="standard",
        n=1,
    )
    return response.data[0].url


async def _download_image(url: str, dest_path: Path) -> None:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        dest_path.write_bytes(resp.content)


async def _upload_to_s3(file_path: Path, s3_key: str) -> str:
    import boto3

    bucket = os.getenv("S3_BUCKET", "adforge-images")
    s3 = boto3.client("s3")
    s3.upload_file(str(file_path), bucket, s3_key)
    region = os.getenv("AWS_REGION", "us-east-1")
    return f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"


async def run_image_gen(state: dict) -> dict:
    creative_brief_output = state.get("creative_brief_output", {})
    campaign_id = state.get("campaign_id", "unknown")
    briefs = creative_brief_output.get("briefs", [])
    is_production = os.getenv("ENV", "development") == "production"

    image_output = {}
    generated_count = 0

    for brief in briefs:
        angle_name = brief.get("angle_name", "angle")
        angle_slug = _slugify(angle_name)
        angle_images = {}

        for fmt, fmt_config in FORMAT_MAP.items():
            prompt = brief.get(fmt_config["dalle_key"], "")
            if not prompt:
                angle_images[fmt] = {"error": "No DALL-E prompt in brief"}
                continue

            logger.info(f"  Generating {fmt} image for '{angle_name}'…")
            try:
                image_url = await _generate_image(prompt, fmt_config["size"])

                # Determine save path
                local_path = Path(f"static/campaigns/{campaign_id}/{angle_slug}/{fmt}.png")
                await _download_image(image_url, local_path)
                generated_count += 1

                if is_production:
                    s3_key = f"campaigns/{campaign_id}/{angle_slug}/{fmt}.png"
                    public_url = await _upload_to_s3(local_path, s3_key)
                    angle_images[fmt] = public_url
                else:
                    angle_images[fmt] = f"/static/campaigns/{campaign_id}/{angle_slug}/{fmt}.png"

            except Exception as e:
                logger.error(f"  Image gen failed for {fmt}/{angle_name}: {e}")
                angle_images[fmt] = {"error": f"generation failed — {e}"}

        image_output[angle_slug] = {"angle_name": angle_name, **angle_images}

    cost = generated_count * 0.04
    logger.info(
        f"Image generation complete: {generated_count} images generated. "
        f"Estimated cost: ${cost:.2f}"
    )

    return image_output
