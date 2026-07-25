from __future__ import annotations

import wave
from abc import ABC, abstractmethod
from pathlib import Path

import httpx

from .config import Settings
from .higgs import VoiceRegistry


class TTSProvider(ABC):
    name = "base"
    prefers_tts_text = False

    def prepare_text(self, *, text: str, voice: str, delivery: str = "") -> str:
        return text

    def voice_fingerprint(self, voice: str) -> str:
        return voice

    def cache_identity(self) -> str:
        """Stable, secret-free identity for every setting that changes audio output."""
        return self.name

    @abstractmethod
    def synthesize(
        self, *, text: str, voice: str, instructions: str, output: Path
    ) -> None:
        raise NotImplementedError


class MockTTSProvider(TTSProvider):
    name = "mock"

    def cache_identity(self) -> str:
        return "mock|wav|sample_rate=16000|algorithm=v1"

    def synthesize(
        self, *, text: str, voice: str, instructions: str, output: Path
    ) -> None:
        output.parent.mkdir(parents=True, exist_ok=True)
        duration = max(0.7, min(12.0, len(text.split()) / 2.3))
        sample_rate = 16000
        frames = int(duration * sample_rate)
        with wave.open(str(output), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(bytes(frames * 2))


OPENAI_VOICE_MAP = {
    "narator": "marin",
    "alexandru": "coral",
    "tati": "cedar",
    "masinuta-energica": "coral",
    "masinuta-jucausa": "nova",
    "masinuta-grava": "echo",
    "masinuta-luminoasa": "shimmer",
}


class OpenAITTSProvider(TTSProvider):
    name = "openai"
    speed = 0.92
    response_format = "wav"

    def __init__(self, settings: Settings):
        from openai import OpenAI

        kwargs = {
            "api_key": settings.openai_api_key,
            "timeout": settings.tts_timeout_seconds,
        }
        if settings.openai_tts_base_url:
            kwargs["base_url"] = settings.openai_tts_base_url
        self.client = OpenAI(**kwargs)
        self.model = settings.openai_tts_model
        self.base_url = (
            settings.openai_tts_base_url.rstrip("/")
            if settings.openai_tts_base_url
            else "https://api.openai.com/v1"
        )

    def cache_identity(self) -> str:
        return "|".join(
            (
                self.name,
                self.base_url,
                self.model,
                self.response_format,
                f"speed={self.speed}",
            )
        )

    def synthesize(
        self, *, text: str, voice: str, instructions: str, output: Path
    ) -> None:
        output.parent.mkdir(parents=True, exist_ok=True)
        with self.client.audio.speech.with_streaming_response.create(
            model=self.model,
            voice=OPENAI_VOICE_MAP.get(voice, voice),
            input=text,
            instructions=instructions,
            response_format=self.response_format,
            speed=self.speed,
        ) as response:
            response.stream_to_file(output)


class OpenAICompatibleTTSProvider(TTSProvider):
    name = "openai-compatible"
    speed = 0.92
    response_format = "wav"

    def __init__(self, settings: Settings):
        self.base_url = settings.local_tts_base_url.rstrip("/")
        self.api_key = settings.local_tts_api_key
        self.model = settings.local_tts_model
        self.timeout = settings.tts_timeout_seconds

    def cache_identity(self) -> str:
        return "|".join(
            (
                self.name,
                self.base_url,
                self.model,
                self.response_format,
                f"speed={self.speed}",
            )
        )

    def synthesize(
        self, *, text: str, voice: str, instructions: str, output: Path
    ) -> None:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "model": self.model,
            "voice": voice,
            "input": text,
            "instructions": instructions,
            "response_format": self.response_format,
            "speed": self.speed,
        }
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/audio/speech", headers=headers, json=payload
            )
            response.raise_for_status()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(response.content)


class HiggsTTSProvider(TTSProvider):
    """Native adapter for Higgs TTS 3 served through SGLang-Omni/vLLM-Omni."""

    name = "higgs"
    prefers_tts_text = True

    def __init__(self, settings: Settings):
        self.base_url = settings.higgs_base_url.rstrip("/")
        self.api_key = settings.higgs_api_key
        self.model = settings.higgs_model
        self.api_voice = settings.higgs_api_voice
        self.use_profile_voice = settings.higgs_use_profile_voice
        self.response_format = settings.higgs_response_format
        if self.response_format != "wav":
            raise ValueError("Aplicația salvează segmente WAV; HIGGS_RESPONSE_FORMAT trebuie să fie wav")
        self.temperature = settings.higgs_temperature
        self.top_p = settings.higgs_top_p
        self.top_k = settings.higgs_top_k
        self.max_new_tokens = settings.higgs_max_new_tokens
        self.seed = settings.higgs_seed
        self.timeout = settings.tts_timeout_seconds
        self.require_references = settings.higgs_require_references
        self.voices = VoiceRegistry(settings.voice_dir, settings.voice_manifest)

    def prepare_text(self, *, text: str, voice: str, delivery: str = "") -> str:
        return self.voices.prepare_text(voice, text, delivery)

    def voice_fingerprint(self, voice: str) -> str:
        return self.voices.fingerprint(voice)

    def cache_identity(self) -> str:
        return "|".join(
            (
                self.name,
                self.base_url,
                self.model,
                f"api_voice={self.api_voice}",
                f"use_profile_voice={self.use_profile_voice}",
                self.response_format,
                f"temperature={self.temperature}",
                f"top_p={self.top_p}",
                f"top_k={self.top_k}",
                f"max_new_tokens={self.max_new_tokens}",
                f"seed={self.seed}",
                f"require_references={self.require_references}",
            )
        )

    def build_payload(self, *, text: str, profile_voice: str) -> dict[str, object]:
        """Build the exact official /v1/audio/speech request without sending it."""
        payload: dict[str, object] = {
            "model": self.model,
            "input": text,
            "response_format": self.response_format,
            "temperature": self.temperature,
            "top_k": self.top_k,
            "max_new_tokens": self.max_new_tokens,
        }
        # Higgs TTS 3 has no built-in speaker. Some compatible servers expose
        # named voices, but voice cloning must be allowed to omit this field.
        if self.use_profile_voice:
            payload["voice"] = profile_voice
        elif self.api_voice:
            payload["voice"] = self.api_voice
        if not self.use_profile_voice:
            references = self.voices.reference_payload(
                profile_voice, required=self.require_references
            )
            if references:
                payload["references"] = references
        if self.top_p is not None:
            payload["top_p"] = self.top_p
        if self.seed is not None:
            payload["seed"] = self.seed
        return payload

    def synthesize(
        self, *, text: str, voice: str, instructions: str, output: Path
    ) -> None:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = self.build_payload(text=text, profile_voice=voice)

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/audio/speech", headers=headers, json=payload
            )
            response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "json" in content_type:
            raise RuntimeError(
                "Serverul Higgs a returnat JSON în loc de audio: "
                f"{response.text[:500]}"
            )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(response.content)


def build_tts_provider(settings: Settings) -> TTSProvider:
    if settings.tts_provider == "mock":
        return MockTTSProvider()
    if settings.tts_provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY lipsește")
        return OpenAITTSProvider(settings)
    if settings.tts_provider == "openai-compatible":
        return OpenAICompatibleTTSProvider(settings)
    if settings.tts_provider == "higgs":
        return HiggsTTSProvider(settings)
    raise ValueError(f"TTS_PROVIDER necunoscut: {settings.tts_provider}")
