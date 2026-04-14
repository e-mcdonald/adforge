import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

from database import Base, engine
from routers.avatars import router as avatars_router
from routers.campaigns import router as campaigns_router
from routers.models_router import router as models_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("✓ Database tables created / verified")

    # Check Ollama availability
    try:
        from config.model_router import check_ollama_available
        ollama_ok = check_ollama_available()
        if ollama_ok:
            logger.info("✓ Ollama available — local models active (llama3.1:8b)")
        else:
            logger.warning(
                "⚠ Ollama not found — local tasks will fall back to gpt-4o-mini. "
                "To enable local models: ollama pull llama3.1:8b"
            )
    except Exception as e:
        logger.warning(f"⚠ Could not check Ollama status: {e}")

    # Ensure static directory exists
    os.makedirs("static/campaigns", exist_ok=True)

    yield


app = FastAPI(title="AdForge API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(avatars_router)
app.include_router(campaigns_router)
app.include_router(models_router)


@app.get("/health")
def health():
    return {"status": "ok"}
