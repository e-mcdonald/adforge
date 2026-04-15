import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from config.model_router import get_llm

logger = logging.getLogger(__name__)

COPY_SYSTEM_PROMPT = """You are a world-class direct response copywriter trained on Eugene Schwartz's Breakthrough Advertising, Gary Halbert's sales letters, and David Ogilvy's research-first principles. You write ads that enter the exact conversation already happening in the avatar's mind.

BANNED PATTERNS — never produce these under any circumstance:
1. False Contrast Stack: "It's not X. It's not Y. It's Z." — banned entirely.
2. Triple Short Sentence Stack: Three consecutive sentences of identical length and rhythm — banned.
3. Rhetorical Section Openers: "But what does that actually mean?" / "So how does it work?" — banned. Use declarative statements or hard line breaks instead.
4. Imagine If Openers: "Imagine waking up to…" — banned. Open with a hard fact, a direct challenge, or a specific number.
5. Parallel Repetition Stacks: "More leads. More calls. More revenue." — banned. Every consecutive line must add new information, raise stakes, deepen implication, or move the argument forward. Never echo.
6. Filler transitions: "Let's dive in", "Here's the thing", "At the end of the day" — banned.
7. Hedging qualifiers: might, could potentially, often, usually, tends to, generally — banned. State things as facts. Use specific proof points.

REQUIRED PATTERNS:
- Open by entering the conversation already in the avatar's head at their awareness stage
- Use the exact pain phrases and VoC language from research — their words, not marketing words
- Every headline must be specific — a number, a name, a mechanism, or a vivid outcome
- Primary text structure: Hook → Problem Agitation (raise stakes) → Mechanism Reveal → Proof/Specificity → CTA
- TikTok frame 1 must be a pattern interrupt — the single most arresting sentence in the package
- CTAs must be specific: "See why 12,000 night drivers switched" not "Shop Now"
- Sentence rhythm must vary: long declarative followed by short punch, never mechanical

Respond only in valid JSON."""


async def _generate_copy_for_angle(angle: dict, state: dict, llm) -> dict:
    avatar = state.get("avatar", {})
    product_name = state.get("product_name", "")
    product_price = state.get("product_price", "")
    research = state.get("research_output", {})
    synthesis = research.get("synthesis", {})

    user_message = f"""
Product: {product_name} (Price: {product_price})
Avatar: {avatar.get('name', '')} — {avatar.get('age_demo', '')}
Core Pain: {avatar.get('core_pain', '')}
Dream Outcome: {avatar.get('dream_outcome', '')}
Awareness Stage: {avatar.get('awareness_stage', state.get('awareness_stage', 1))}

Angle to write for:
- Name: {angle.get('angle_name', '')}
- Hook Direction: {angle.get('hook_direction', '')}
- Awareness Approach: {angle.get('awareness_approach', '')}
- Emotional Driver: {angle.get('emotional_driver', '')}
- Big Claim: {angle.get('big_claim', '')}

Research language to draw from:
- Top Pain Phrases: {json.dumps(synthesis.get('top_pain_phrases', []))}
- Strongest VoC Quote: {synthesis.get('strongest_voc_quote', '')}
- Awareness Gap: {synthesis.get('awareness_gap', '')}

Generate a complete copy package. Output valid JSON with exactly this structure:
{{
  "angle_name": "{angle.get('angle_name', '')}",
  "headlines": ["h1", "h2", "h3", "h4", "h5"],
  "primary_text_variants": ["variant1 (150-300 words)", "variant2 (150-300 words)", "variant3 (150-300 words)"],
  "ctas": ["cta1", "cta2", "cta3"],
  "hook_sentences": ["hook1", "hook2", "hook3", "hook4", "hook5"],
  "tiktok_slideshow_frames": [
    "Frame 1: [pattern interrupt hook]",
    "Frame 2: [problem deepening]",
    "Frame 3: [agitation — raise stakes]",
    "Frame 4: [mechanism reveal]",
    "Frame 5: [proof/specificity]",
    "Frame 6: [objection handle or social proof]",
    "Frame 7: [CTA]"
  ]
}}
"""

    messages = [SystemMessage(content=COPY_SYSTEM_PROMPT), HumanMessage(content=user_message)]
    response = await llm.ainvoke(messages)
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        from json_repair import repair_json
        logger.warning("Copy JSON malformed — attempting repair")
        return json.loads(repair_json(raw))


async def run_copy(state: dict) -> dict:
    strategy_output = state.get("strategy_output", {})
    angles = strategy_output.get("angles", [])
    copy_model = state.get("copy_model", "claude-opus-4-5")
    use_local = state.get("use_local_models", True)

    logger.info(f"Generating copy with {copy_model}…")
    llm = get_llm("copy", override_model=copy_model, use_local=use_local)

    copy_packages = []
    for i, angle in enumerate(angles):
        logger.info(f"  Writing copy for Angle {i+1}: {angle.get('angle_name', '')}")
        try:
            pkg = await _generate_copy_for_angle(angle, state, llm)
            copy_packages.append(pkg)
        except Exception as e:
            logger.error(f"  Copy generation failed for angle {i+1}: {e}")
            copy_packages.append({
                "angle_name": angle.get("angle_name", f"Angle {i+1}"),
                "error": str(e),
                "headlines": [],
                "primary_text_variants": [],
                "ctas": [],
                "hook_sentences": [],
                "tiktok_slideshow_frames": [],
            })

    if copy_packages:
        logger.info("=== COPY OUTPUT — ANGLE 1 ===")
        logger.info(json.dumps(copy_packages[0], indent=2)[:3000])

    return {"angles": copy_packages, "model_used": copy_model}
