import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from config.model_router import get_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an art director writing creative briefs for direct response ads. Your job is to translate a copy angle and emotional driver into clear visual direction and a precise DALL-E 3 image generation prompt. Be specific and visual. No vague descriptions.

DALL-E prompt rules:
- Always specify: photorealistic, high resolution, no text in image, no logos, no watermarks
- Include: lighting direction, time of day, subject position, background detail, mood
- Match emotional driver: Fear = dark/high contrast/dramatic. Desire = warm/golden/aspirational. Curiosity = clean/clinical/product-focused. Belonging = social/candid/lifestyle.
- End every prompt with: "Commercial photography. Photorealistic. No text, logos, or watermarks."

Respond only in valid JSON."""


async def _brief_for_angle(angle_copy: dict, strategy_angle: dict, state: dict, llm) -> dict:
    avatar = state.get("avatar", {})
    product_name = state.get("product_name", "")

    user_message = f"""
Product: {product_name}
Angle: {angle_copy.get('angle_name', '')}
Emotional Driver: {strategy_angle.get('emotional_driver', 'Desire')}
Hook Direction: {strategy_angle.get('hook_direction', '')}
Big Claim: {strategy_angle.get('big_claim', '')}
Avatar: {avatar.get('name', '')} — {avatar.get('age_demo', '')}

Best Headline: {(angle_copy.get('headlines') or [''])[0]}
Primary Text (excerpt): {(angle_copy.get('primary_text_variants') or [''])[0][:400]}

Generate a creative brief. Output valid JSON:
{{
  "angle_name": "{angle_copy.get('angle_name', '')}",
  "visual_style": "UGC authentic | Product hero | Before/After split | Text-on-image editorial | Lifestyle scene | Testimonial screenshot",
  "color_mood": {{
    "primary": "#hex",
    "secondary": "#hex",
    "accent": "#hex",
    "rationale": "why these colors match the emotional driver"
  }},
  "layout_type": "describe exact layout — where headline sits, where product sits, where CTA sits",
  "reference_aesthetic": "describe a real-world ad style reference — be specific",
  "dalle_prompt_meta_feed": "complete DALL-E 3 prompt for 1:1 ratio",
  "dalle_prompt_meta_story": "complete DALL-E 3 prompt for 9:16 ratio",
  "dalle_prompt_tiktok": "complete DALL-E 3 prompt for 9:16 ratio TikTok background"
}}
"""

    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_message)]
    response = await llm.ainvoke(messages)
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        from json_repair import repair_json
        logger.warning("Creative brief JSON malformed — attempting repair")
        return json.loads(repair_json(raw))


async def run_creative_brief(state: dict) -> dict:
    copy_output = state.get("copy_output", {})
    strategy_output = state.get("strategy_output", {})
    use_local = state.get("use_local_models", True)

    copy_angles = copy_output.get("angles", [])
    strategy_angles = strategy_output.get("angles", [])

    llm = get_llm("creative_brief", use_local=use_local)
    logger.info(f"Generating creative briefs with local={'ollama/llama3.1:8b' if use_local else 'gpt-4o-mini'}…")

    briefs = []
    for i, copy_angle in enumerate(copy_angles):
        strategy_angle = strategy_angles[i] if i < len(strategy_angles) else {}
        logger.info(f"  Creative brief for Angle {i+1}: {copy_angle.get('angle_name', '')}")

        # Skip if copy generation already failed for this angle
        if copy_angle.get("error"):
            logger.warning(f"  Skipping brief for angle {i+1} — copy failed: {copy_angle['error']}")
            briefs.append({
                "angle_name": copy_angle.get("angle_name", f"Angle {i+1}"),
                "error": f"Skipped — copy generation failed: {copy_angle['error']}",
            })
            continue

        try:
            brief = await _brief_for_angle(copy_angle, strategy_angle, state, llm)
            briefs.append(brief)
        except Exception as e:
            logger.error(f"  Creative brief failed for angle {i+1}: {e}")
            briefs.append({
                "angle_name": copy_angle.get("angle_name", f"Angle {i+1}"),
                "error": str(e),
            })

    if briefs:
        logger.info("=== CREATIVE BRIEF — ANGLE 1 ===")
        b = briefs[0]
        logger.info(f"  Visual Style: {b.get('visual_style', '')}")
        colors = b.get("color_mood", {})
        logger.info(f"  Colors: primary={colors.get('primary')}, secondary={colors.get('secondary')}, accent={colors.get('accent')}")
        logger.info(f"  Layout: {b.get('layout_type', '')}")
        logger.info(f"  Reference: {b.get('reference_aesthetic', '')}")

    return {"briefs": briefs}
