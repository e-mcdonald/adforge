import json
import logging
import os
import re
import urllib.parse
from typing import Any

import httpx
from bs4 import BeautifulSoup
from langchain_core.messages import HumanMessage, SystemMessage

from config.model_router import get_llm

logger = logging.getLogger(__name__)

PAIN_WORDS = [
    "hate", "frustrating", "annoying", "wish", "problem", "finally",
    "works", "doesn't work", "tried everything", "useless", "game changer",
    "wish I had", "can't believe", "waste", "awful", "terrible", "horrible",
    "love", "amazing", "incredible", "changed", "fixed",
]


async def _scrape_product(url: str) -> dict:
    if not url:
        return {"error": "no URL provided"}
    logger.info(f"Scraping product URL: {url}")
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; AdForge/1.0)"}
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
    except Exception as e:
        logger.warning(f"Product scrape failed: {e} — using fallback context")
        return {"error": str(e)}

    soup = BeautifulSoup(resp.text, "html.parser")

    title = soup.title.string.strip() if soup.title else ""
    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag:
        meta_desc = meta_tag.get("content", "")

    headlines = []
    for tag in soup.find_all(["h1", "h2"]):
        text = tag.get_text(strip=True)
        if text:
            headlines.append(text)
    headlines = headlines[:10]

    bullets = []
    for li in soup.find_all("li"):
        text = li.get_text(strip=True)
        if text and len(text) > 10:
            bullets.append(text)
    bullets = bullets[:15]

    price_pattern = re.compile(r"\$[\d,]+(?:\.\d{2})?")
    prices = price_pattern.findall(resp.text)
    price_mentions = list(set(prices))[:5]

    testimonial_keywords = ["review", "testimonial", "said", "wrote", "customer"]
    testimonials = []
    for tag in soup.find_all(["p", "blockquote", "div"]):
        text = tag.get_text(strip=True)
        if any(kw in tag.get("class", []) or kw in str(tag.get("id", "")).lower() for kw in testimonial_keywords):
            if len(text) > 30:
                testimonials.append(text[:300])
    testimonials = testimonials[:5]

    logger.info(f"Scraped: title='{title[:60]}', {len(headlines)} headlines, {len(bullets)} bullets")
    return {
        "title": title,
        "description": meta_desc,
        "headlines": headlines,
        "bullets": bullets,
        "price_mentions": price_mentions,
        "testimonials": testimonials,
    }


async def _pull_reddit_voc(keyword: str) -> list:
    logger.info(f"Pulling Reddit VoC for keyword: {keyword}")
    encoded = urllib.parse.quote(keyword)
    url = f"https://www.reddit.com/search.json?q={encoded}&sort=top&limit=25&type=comment"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; AdForge-Research/1.0)"}
            resp = await client.get(url, headers=headers)
            data = resp.json()
    except Exception as e:
        logger.warning(f"Reddit VoC pull failed: {e}")
        return []

    comments = []
    try:
        children = data.get("data", {}).get("children", [])
        for child in children:
            body = child.get("data", {}).get("body", "")
            if not body:
                continue
            lower = body.lower()
            if any(pw in lower for pw in PAIN_WORDS):
                comments.append(body[:500])
    except Exception as e:
        logger.warning(f"Reddit VoC parse error: {e}")

    result = comments[:10]
    logger.info(f"Found {len(result)} Reddit VoC quotes")
    return result


def _extract_keyword(product_name: str) -> str:
    stopwords = {"the", "a", "an", "by", "for", "of", "and", "with"}
    words = [w for w in product_name.lower().split() if w not in stopwords]
    return " ".join(words[:3])


async def run_research(state: dict) -> dict:
    product_url = state.get("product_url", "")
    product_name = state.get("product_name", "")
    avatar = state.get("avatar", {})
    angle = state.get("angle", "")
    use_local = state.get("use_local_models", True)

    # Step 1 — Product scrape
    product_data = await _scrape_product(product_url)

    # Step 2 — Reddit VoC
    keyword = _extract_keyword(product_name)
    raw_voc = await _pull_reddit_voc(keyword)

    # Step 3 — Facebook Ad Library signal (stub)
    ad_library_signal = {
        "ad_library_url": (
            f"https://www.facebook.com/ads/library/?q={urllib.parse.quote(product_name)}&country=US"
        ),
        "note": "Manual research recommended — check this URL for competitor ads",
    }

    # Step 4 — Synthesis with Claude Sonnet
    logger.info("Synthesizing research with claude-sonnet-4-5…")
    llm = get_llm("research_synthesis", use_local=use_local)

    system_prompt = (
        "You are a direct response research analyst trained on Eugene Schwartz's Breakthrough Advertising. "
        "Your job is to identify the exact mental state of the avatar at their current awareness stage and "
        "surface the specific language, fears, and desires that will make an ad feel like it was written "
        "specifically for them. Do not generalize. Every insight must be rooted in the specific avatar, "
        "the specific product, and the specific awareness stage provided. Respond only in valid JSON."
    )

    user_message = f"""
Product: {product_name}
Product Data: {json.dumps(product_data, indent=2)[:2000]}

Avatar:
- Name: {avatar.get('name', '')}
- Age/Demo: {avatar.get('age_demo', '')}
- Core Pain: {avatar.get('core_pain', '')}
- Dream Outcome: {avatar.get('dream_outcome', '')}
- Awareness Stage: {avatar.get('awareness_stage', 1)}
- Existing Beliefs: {avatar.get('existing_beliefs', '')}
- Raw Language: {avatar.get('raw_language', '')}

Angle/Mechanism: {angle}

Reddit VoC Quotes (raw):
{json.dumps(raw_voc, indent=2)[:2000]}

Based on the above, output valid JSON with these exact keys:
{{
  "top_pain_phrases": ["phrase1", "phrase2", "phrase3", "phrase4", "phrase5"],
  "awareness_gap": "one paragraph about what they believe now vs what they need to believe to buy",
  "saturated_angles": ["angle1", "angle2", "angle3"],
  "recommended_hook_territories": [
    {{"direction": "...", "rationale": "...", "awareness_tie": "..."}},
    {{"direction": "...", "rationale": "...", "awareness_tie": "..."}},
    {{"direction": "...", "rationale": "...", "awareness_tie": "..."}}
  ],
  "strongest_voc_quote": "the single most powerful raw quote"
}}
"""

    try:
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
        response = await llm.ainvoke(messages)
        raw = response.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        synthesis = json.loads(raw)
    except Exception as e:
        logger.error(f"Research synthesis failed: {e}")
        synthesis = {
            "top_pain_phrases": [],
            "awareness_gap": "Synthesis failed.",
            "saturated_angles": [],
            "recommended_hook_territories": [],
            "strongest_voc_quote": raw_voc[0] if raw_voc else "",
        }

    research_output = {
        "product_data": product_data,
        "raw_voice_of_customer": raw_voc,
        "ad_library_signal": ad_library_signal,
        "synthesis": synthesis,
    }

    logger.info("=== RESEARCH OUTPUT ===")
    logger.info(json.dumps(research_output, indent=2)[:3000])

    return research_output
