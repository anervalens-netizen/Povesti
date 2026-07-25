from __future__ import annotations
import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()
from dataclasses import dataclass
from pathlib import Path


def _path(name: str, default: str) -> Path:
    return Path(os.getenv(name, default)).expanduser().resolve()

@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Povești pentru Alexandru")
    host: str = os.getenv("APP_HOST", "127.0.0.1")
    port: int = int(os.getenv("APP_PORT", "8090"))
    story_dir: Path = _path("STORY_DIR", "stories")
    media_dir: Path = _path("MEDIA_DIR", "media")
    tts_provider: str = os.getenv("TTS_PROVIDER", "mock").lower()
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_tts_model: str = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
    openai_tts_base_url: str = os.getenv("OPENAI_TTS_BASE_URL", "")
    local_tts_base_url: str = os.getenv("LOCAL_TTS_BASE_URL", "http://127.0.0.1:8000/v1")
    local_tts_api_key: str = os.getenv("LOCAL_TTS_API_KEY", "")
    local_tts_model: str = os.getenv("LOCAL_TTS_MODEL", "tts-local")
    tts_timeout_seconds: int = int(os.getenv("TTS_TIMEOUT_SECONDS", "180"))
    llm_provider: str = os.getenv("LLM_PROVIDER", "disabled").lower()
    story_llm_model: str = os.getenv("STORY_LLM_MODEL", "gpt-5-mini")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "http://127.0.0.1:8000/v1")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_timeout_seconds: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "240"))

settings = Settings()
settings.story_dir.mkdir(parents=True, exist_ok=True)
settings.media_dir.mkdir(parents=True, exist_ok=True)
