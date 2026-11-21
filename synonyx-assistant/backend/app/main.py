from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import exports, sessions
from app.config import settings
from app.llm.client import TrackedLLMClient
from app.rag.retriever import KBRetriever
from app.storage.db import SessionStorage


@asynccontextmanager
async def lifespan(app: FastAPI):
    sessions.storage = SessionStorage(settings.db_path)
    sessions.llm_client = TrackedLLMClient()
    sessions.kb_retriever = KBRetriever(settings.kb_dir)
    yield


app = FastAPI(title="Synonyx AI Architect", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(exports.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
