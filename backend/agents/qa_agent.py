import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from config.model_router import get_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a direct response copy auditor and Meta Ads policy expert. Score each ad angle against the following criteria. Be specific in your reasoning. Do not give generic feedback. Respond only in valid JSON.

SCORING CRITERIA:
1. Hook Score (1-10): Does frame 1 / headline 1 enter the conversation already in the avatar's mind? Is it specific to their awareness stage? Would they stop scrolling?
2. Awareness Match Score (1-10): Does the copy lead at the right level — not too advanced, not too basic for where this avatar is?
3. Specificity Score (1-10): Are claims backed by numbers, mechanisms, or named outcomes? Or are they vague?

BANNED PATTERN CHECK — flag if any of these appear:
- Parallel repetition stacks (same sentence structure repeated 2+ times)
- False contrast structure (It's not X. It's not Y. It's Z.)
- Rhetorical openers (But what does that mean? / So how does it work?)
- Imagine If openers
- Hedging qualifiers (might, could potentially, often, usually)
- Filler transitions (Let's dive in, Here's the thing)

META POLICY FLAGS — flag if any of these appear:
- Guaranteed results language
- Before/after comparison claims
- Medical or health claims without qualification
- Income or financial result claims
- Superlatives without substantiation (best, #1, fastest)

Respond only in valid JSON."""


async def _qa_angle(copy_angle: dict, avatar: dict, awareness_stage: int, llm) -> dict:
    user_message = f"""
Avatar Awareness Stage: {awareness_stage}
Avatar Core Pain: {avatar.get('core_pain', '')}

Angle to audit: {copy_angle.get('angle_name', '')}

Headline 1: {(copy_angle.get('headlines') or [''])[0]}
Primary Text (Variant 1): {(copy_angle.get('primary_text_variants') or [''])[0][:800]}
TikTok Frame 1: {(copy_angle.get('tiktok_slideshow_frames') or [''])[0]}
CTA 1: {(copy_angle.get('ctas') or [''])[0]}

Audit this copy package. Output valid JSON:
{{
  "angle_name": "{copy_angle.get('angle_name', '')}",
  "hook_score": {{"score": 8, "reasoning": "specific reasoning here"}},
  "awareness_match_score": {{"score": 7, "reasoning": "specific reasoning here"}},
  "specificity_score": {{"score": 9, "reasoning": "specific reasoning here"}},
  "overall_score": 8.0,
  "copy_violations": ["list of detected banned patterns, empty if none"],
  "compliance_flags": ["list of Meta policy concerns, empty if none"],
  "recommended_headline": {{"headline": "improved headline", "reasoning": "why this is better"}},
  "launch_recommendation": "Ready to test | Revise before launch | Do not run"
}}
"""

    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_message)]
    response = await llm.ainvoke(messages)
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


async def run_qa(state: dict) -> dict:
    copy_output = state.get("copy_output", {})
    avatar = state.get("avatar", {})
    awareness_stage = state.get("awareness_stage", 1)
    use_local = state.get("use_local_models", True)

    copy_angles = copy_output.get("angles", [])

    llm = get_llm("qa", use_local=use_local)
    logger.info("Running QA audit…")

    qa_results = []
    for i, copy_angle in enumerate(copy_angles):
        if copy_angle.get("error"):
            qa_results.append({"angle_name": copy_angle.get("angle_name", f"Angle {i+1}"), "error": copy_angle["error"]})
            continue
        logger.info(f"  QA for Angle {i+1}: {copy_angle.get('angle_name', '')}")
        try:
            result = await _qa_angle(copy_angle, avatar, awareness_stage, llm)
            qa_results.append(result)
            logger.info(
                f"  Score: hook={result.get('hook_score', {}).get('score')} "
                f"awareness={result.get('awareness_match_score', {}).get('score')} "
                f"specificity={result.get('specificity_score', {}).get('score')} "
                f"overall={result.get('overall_score')} "
                f"→ {result.get('launch_recommendation')}"
            )
        except Exception as e:
            logger.error(f"  QA failed for angle {i+1}: {e}")
            qa_results.append({
                "angle_name": copy_angle.get("angle_name", f"Angle {i+1}"),
                "error": str(e),
            })

    return {"angles": qa_results}
