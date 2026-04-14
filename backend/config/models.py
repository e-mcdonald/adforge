MODEL_CONFIG = {
    "research_extract": {
        "provider": "ollama",
        "model": "llama3.1:8b",
        "temperature": 0.1,
        "description": "Fast local extraction — scraping, parsing, tagging",
    },
    "research_synthesis": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-5",
        "temperature": 0.3,
        "description": "VoC synthesis, insight generation, pattern recognition",
    },
    "strategy": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-5",
        "temperature": 0.5,
        "description": "Angle strategy, awareness mapping, hook direction",
    },
    "copy": {
        "provider": "anthropic",
        "model": "claude-opus-4-5",
        "temperature": 0.7,
        "description": "Ad copy — highest quality required, revenue-generating output",
    },
    "creative_brief": {
        "provider": "ollama",
        "model": "llama3.1:8b",
        "temperature": 0.3,
        "description": "Structured creative briefs and DALL-E prompt writing",
    },
    "qa": {
        "provider": "ollama",
        "model": "llama3.1:8b",
        "temperature": 0.1,
        "description": "Rule-based scoring, compliance checking, pattern detection",
    },
}

# Fallback when Ollama unavailable
OLLAMA_FALLBACK = {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "temperature": None,  # inherit from task config
}

# Model options exposed to frontend campaign builder
COPY_MODEL_OPTIONS = [
    {
        "value": "claude-opus-4-5",
        "label": "Claude Opus 4.5",
        "description": "Best quality — recommended for copy",
        "provider": "anthropic",
    },
    {
        "value": "claude-sonnet-4-5",
        "label": "Claude Sonnet 4.5",
        "description": "Faster, lower cost",
        "provider": "anthropic",
    },
    {
        "value": "gpt-4o",
        "label": "GPT-4o",
        "description": "OpenAI alternative",
        "provider": "openai",
    },
]
