import logging
import os
import time
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

from config.models import COPY_MODEL_OPTIONS, MODEL_CONFIG, OLLAMA_FALLBACK

logger = logging.getLogger(__name__)

# Simple module-level cache for Ollama availability
_ollama_cache: dict = {"available": None, "timestamp": 0.0}
_CACHE_TTL = 60  # seconds


def check_ollama_available() -> bool:
    """Check if Ollama is reachable. Cached for 60 seconds."""
    now = time.time()
    if _ollama_cache["available"] is not None and (now - _ollama_cache["timestamp"]) < _CACHE_TTL:
        return _ollama_cache["available"]

    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        resp = httpx.get(f"{base_url}/api/tags", timeout=2.0)
        available = resp.status_code == 200
    except Exception:
        available = False

    _ollama_cache["available"] = available
    _ollama_cache["timestamp"] = now
    return available


def _infer_provider(model: str) -> str:
    if model.startswith("claude-"):
        return "anthropic"
    if model.startswith("gpt-") or model.startswith("o1") or model.startswith("o3"):
        return "openai"
    return "ollama"


def get_llm(task: str, override_model: Optional[str] = None, use_local: bool = True):
    """
    Return an appropriate LangChain chat model for the given task.

    Priority:
    1. override_model — use that model, infer provider
    2. MODEL_CONFIG[task] — look up by task name
    3. OLLAMA_FALLBACK — if ollama unavailable and task uses local
    """
    if override_model:
        provider = _infer_provider(override_model)
        cfg = {"model": override_model, "temperature": 0.7, "max_tokens": 4096}
    else:
        if task not in MODEL_CONFIG:
            raise ValueError(f"Unknown task: {task}. Valid tasks: {list(MODEL_CONFIG.keys())}")
        task_cfg = MODEL_CONFIG[task]
        provider = task_cfg["provider"]
        cfg = {
            "model": task_cfg["model"],
            "temperature": task_cfg["temperature"],
            "max_tokens": task_cfg.get("max_tokens", 2048),
        }

        # Local model handling
        if provider == "ollama":
            if not use_local:
                logger.info(f"use_local=False — switching {task} to gpt-4o-mini fallback")
                provider = OLLAMA_FALLBACK["provider"]
                cfg["model"] = OLLAMA_FALLBACK["model"]
                if OLLAMA_FALLBACK["temperature"] is not None:
                    cfg["temperature"] = OLLAMA_FALLBACK["temperature"]
            elif not check_ollama_available():
                logger.warning(
                    f"⚠ Ollama not available — falling back to gpt-4o-mini for task '{task}'"
                )
                provider = OLLAMA_FALLBACK["provider"]
                cfg["model"] = OLLAMA_FALLBACK["model"]
                if OLLAMA_FALLBACK["temperature"] is not None:
                    cfg["temperature"] = OLLAMA_FALLBACK["temperature"]

    logger.info(f"Running {task} with {provider}/{cfg['model']}")

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=cfg["model"],
            temperature=cfg["temperature"],
            max_tokens=cfg["max_tokens"],
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=cfg["model"],
            temperature=cfg["temperature"],
            max_tokens=cfg["max_tokens"],
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )
    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=cfg["model"],
            temperature=cfg["temperature"],
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")


def estimate_campaign_cost(use_local: bool, copy_model: str) -> str:
    if use_local and copy_model == "claude-opus-4-5":
        return "~$0.25–0.40/campaign"
    if use_local and copy_model == "claude-sonnet-4-5":
        return "~$0.10–0.20/campaign"
    if not use_local and copy_model == "claude-opus-4-5":
        return "~$1.20–1.80/campaign"
    if not use_local and copy_model == "claude-sonnet-4-5":
        return "~$0.60–1.00/campaign"
    return "~$0.25–0.40/campaign"
