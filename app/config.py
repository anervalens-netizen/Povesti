from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()


def _path(name: str, default: str) -> Path:
    return Path(os.getenv(name, default)).expanduser().resolve()


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _optional_int(name: str) -> int | None:
    value = os.getenv(name, "").strip()
    return int(value) if value else None


def _optional_float(name: str) -> float | None:
    value = os.getenv(name, "").strip()
    return float(value) if value else None


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Povești pentru Alexandru")
    host: str = os.getenv("APP_HOST", "127.0.0.1")
    port: int = int(os.getenv("APP_PORT", "8090"))
    story_dir: Path = _path("STORY_DIR", "stories")
    media_dir: Path = _path("MEDIA_DIR", "media")
    voice_dir: Path = _path("VOICE_DIR", "voices")
    voice_manifest: Path = _path("VOICE_MANIFEST", "voices/voices.json")
    tts_provider: str = os.getenv("TTS_PROVIDER", "mock").lower()
    tts_timeout_seconds: int = int(os.getenv("TTS_TIMEOUT_SECONDS", "240"))

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_tts_model: str = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
    openai_tts_base_url: str = os.getenv("OPENAI_TTS_BASE_URL", "")

    local_tts_base_url: str = os.getenv("LOCAL_TTS_BASE_URL", "http://127.0.0.1:8000/v1")
    local_tts_api_key: str = os.getenv("LOCAL_TTS_API_KEY", "")
    local_tts_model: str = os.getenv("LOCAL_TTS_MODEL", "tts-local")

    higgs_base_url: str = os.getenv("HIGGS_BASE_URL", "http://127.0.0.1:8000/v1")
    higgs_api_key: str = os.getenv("HIGGS_API_KEY", "")
    higgs_model: str = os.getenv("HIGGS_MODEL", "bosonai/higgs-tts-3-4b")
    higgs_api_voice: str = os.getenv("HIGGS_API_VOICE", "default")
    higgs_response_format: str = os.getenv("HIGGS_RESPONSE_FORMAT", "wav").lower()
    higgs_temperature: float = float(os.getenv("HIGGS_TEMPERATURE", "0.8"))
    higgs_top_p: float | None = _optional_float("HIGGS_TOP_P")
    higgs_top_k: int = int(os.getenv("HIGGS_TOP_K", "50"))
    higgs_max_new_tokens: int = int(os.getenv("HIGGS_MAX_NEW_TOKENS", "2048"))
    higgs_seed: int | None = _optional_int("HIGGS_SEED")
    higgs_require_references: bool = _bool("HIGGS_REQUIRE_REFERENCES", False)

    llm_provider: str = os.getenv("LLM_PROVIDER", "disabled").lower()
    story_llm_model: str = os.getenv("STORY_LLM_MODEL", "gpt-5-mini")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "http://127.0.0.1:8000/v1")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_timeout_seconds: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "240"))


settings = Settings()
settings.story_dir.mkdir(parents=True, exist_ok=True)
settings.media_dir.mkdir(parents=True, exist_ok=True)
settings.voice_dir.mkdir(parents=True, exist_ok=True)
