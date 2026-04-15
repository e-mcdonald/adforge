import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from config.model_router import get_llm

logger = logging.getLogger(__name__)


def _fix_unescaped_quotes(raw: str) -> str:
    """
    Escape double quotes that appear inside JSON string values but are not
    already escaped.  LLMs routinely write copy like:

        "She said "I grip the wheel" every night"

    which breaks json.loads.  This state-machine walks the raw text and, while
    inside a JSON string, replaces any `"` that is NOT followed (after optional
    whitespace) by a JSON structural character ( , : } ] ) with \\".

    This is applied BEFORE json.loads so the output can be parsed without
    needing the json_repair dependency.
    """
    result: list = []
    i = 0
    n = len(raw)
    in_string = False

    while i < n:
        c = raw[i]

        if in_string:
            if c == "\\" and i + 1 < n:
                # Already-escaped sequence — pass both bytes through unchanged
                result.append(c)
                result.append(raw[i + 1])
                i += 2
                continue
            if c == '"':
                # Peek past trailing whitespace to find the next meaningful token
                j = i + 1
                while j < n and raw[j] in " \t\n\r":
                    j += 1
                if j >= n or raw[j] in ",:}]":
                    # Legitimate closing quote — end the string
                    result.append(c)
                    in_string = False
                else:
                    # Internal quote inside a string value — escape it
                    result.append('\\"')
            else:
                result.append(c)
        else:
            if c == '"':
                result.append(c)
                in_string = True
            else:
                result.append(c)

        i += 1

    return "".join(result)

COPY_SYSTEM_PROMPT = """You are a world-class direct response copywriter trained on Eugene Schwartz's Breakthrough Advertising, Gary Halbert's sales letters, and David Ogilvy's research-first principles. You write ads that enter the exact conversation already happening in the avatar's mind.

BANNED PATTERNS — never produce these under any circumstance:
1. False Contrast Stack: "It's not X. It's not Y. It's Z." — banned entirely.
2. Triple Short Sentence Stack: Three consecutive sentences of identical length and rhythm — banned.
3. Rhetorical Section Openers: "But what does that actually mean?" / "So how does it work?" — banned. Use declarative statements or hard line breaks instead.
4. Imagine If Openers: "Imagine waking up to…" — banned. Open with a hard fact, a direct challenge, or a specific number.
5. Parallel Repetition Stacks: "More leads. More calls. More revenue." — banned. Every consecutive line must add new information, raise stakes, deepen implication, or move the argument forward. Never echo.
6. Filler transitions: "Let's dive in", "Here's the thing", "At the end of the day" — banned.
7. Hedging qualifiers: might, could potentially, often, usually, tends to, generally — banned. State things as facts. Use specific proof points.
8. Double quote characters (") inside copy text — banned. In primary_text_variants, hook_sentences, headlines, ctas, and tiktok_slideshow_frames, never use the " character. Use single quotes (') for any quoted speech. Example: write She said 'I was terrified' — never She said "I was terrified". Unescaped double quotes break JSON.

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

    # Layer 1 — fast path: model output is already valid JSON
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Layer 2 — fix unescaped double quotes inside string values (most common failure)
    try:
        fixed = _fix_unescaped_quotes(raw)
        result = json.loads(fixed)
        logger.info("Copy JSON parsed after quote-escaping fix")
        return result
    except json.JSONDecodeError:
        pass

    # Layer 3 — json_repair (handles truncation, trailing commas, other oddities)
    try:
        from json_repair import repair_json
        result = json.loads(repair_json(raw))
        logger.info("Copy JSON parsed after json_repair")
        return result
    except Exception:
        pass

    # All layers failed — log the raw response for diagnostics and raise
    logger.error(f"All JSON parse attempts failed. Raw response (first 500 chars):\n{raw[:500]!r}")
    raise json.JSONDecodeError("All parse layers failed", raw, 0)


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
