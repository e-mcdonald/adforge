import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from config.model_router import get_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a direct response strategist trained on Eugene Schwartz's Breakthrough Advertising and Gary Halbert's copywriting principles. Your job is to generate 3 distinct ad angles, each entering the conversation already happening in the avatar's mind at their exact awareness stage.

Rules you must follow:
- Stage 1-2 avatars: never lead with the product. Lead with the problem they haven't named yet.
- Stage 3-4 avatars: lead with mechanism differentiation. Why is this solution different from what they've already tried?
- Stage 5 avatars: lead with the offer. They know the product — close them.
- Each angle must be emotionally distinct. Fear, Desire, Curiosity, and Belonging are different entry points — not variations of each other.
- Avoid any angle already listed in saturated_angles from research.
- Respond only in valid JSON."""


async def run_strategy(state: dict) -> dict:
    research_output = state.get("research_output", {})
    avatar = state.get("avatar", {})
    angle = state.get("angle", "")
    awareness_stage = state.get("awareness_stage", 1)
    emotional_driver = state.get("emotional_driver", "Desire")
    platforms = state.get("platforms", [])
    use_local = state.get("use_local_models", True)
    product_name = state.get("product_name", "")

    synthesis = research_output.get("synthesis", {})
    saturated_angles = synthesis.get("saturated_angles", [])
    pain_phrases = synthesis.get("top_pain_phrases", [])
    hook_territories = synthesis.get("recommended_hook_territories", [])

    llm = get_llm("strategy", use_local=use_local)

    user_message = f"""
Product: {product_name}
Avatar: {avatar.get('name', '')} — {avatar.get('age_demo', '')}
Core Pain: {avatar.get('core_pain', '')}
Dream Outcome: {avatar.get('dream_outcome', '')}
Awareness Stage: {awareness_stage}
Primary Emotional Driver: {emotional_driver}
Target Platforms: {', '.join(platforms) if platforms else 'meta_feed'}

Angle/Mechanism from brief: {angle}

Research Insights:
- Top Pain Phrases: {json.dumps(pain_phrases)}
- Saturated Angles (avoid these): {json.dumps(saturated_angles)}
- Recommended Hook Territories: {json.dumps(hook_territories)}
- Strongest VoC Quote: {synthesis.get('strongest_voc_quote', '')}
- Awareness Gap: {synthesis.get('awareness_gap', '')}

Generate 3 emotionally distinct angles. Output valid JSON:
{{
  "angles": [
    {{
      "angle_name": "short memorable name",
      "hook_direction": "one sentence — the emotional entry point",
      "awareness_approach": "how this angle meets the avatar at their stage",
      "emotional_driver": "Fear | Desire | Curiosity | Belonging",
      "best_platforms": ["meta_feed", "tiktok"],
      "big_claim": "the single overarching promise — specific, not vague"
    }}
  ]
}}
"""

    try:
        messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_message)]
        response = await llm.ainvoke(messages)
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        strategy_output = json.loads(raw)
    except Exception as e:
        logger.error(f"Strategy agent failed: {e}")
        strategy_output = {
            "angles": [
                {
                    "angle_name": "Fallback Angle",
                    "hook_direction": "Direct pain-point entry",
                    "awareness_approach": "Meet avatar at current stage",
                    "emotional_driver": emotional_driver,
                    "best_platforms": platforms or ["meta_feed"],
                    "big_claim": "Specific outcome for your specific problem",
                }
            ]
        }

    angles = strategy_output.get("angles", [])
    logger.info("=== STRATEGY OUTPUT ===")
    for a in angles:
        logger.info(f"  Angle: {a.get('angle_name')} | Hook: {a.get('hook_direction')}")

    return strategy_output
