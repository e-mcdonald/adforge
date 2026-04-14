from fastapi import APIRouter
from config.model_router import check_ollama_available, estimate_campaign_cost
from config.models import COPY_MODEL_OPTIONS, MODEL_CONFIG

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("/status")
def models_status():
    ollama_available = check_ollama_available()
    model_summary = {
        task: {"provider": cfg["provider"], "model": cfg["model"]}
        for task, cfg in MODEL_CONFIG.items()
    }
    return {
        "ollama_available": ollama_available,
        "ollama_model": "llama3.1:8b",
        "copy_model_options": COPY_MODEL_OPTIONS,
        "model_config": model_summary,
    }


@router.get("/cost-estimate")
def cost_estimate(use_local: bool = True, copy_model: str = "claude-opus-4-5"):
    return {"estimate": estimate_campaign_cost(use_local, copy_model)}
