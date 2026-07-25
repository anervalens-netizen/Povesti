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

    @abstractmethod
    def synthesize(
        self, *, text: str, voice: str, instructions: str, output: Path
    ) -> None:
        raise NotImplementedError


class MockTTSProvider(TTSProvider):
    name = "mock"

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


class OpenAITTSProvider(TTSProvider):
    name = "openai"

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

    def synthesize(
        self, *, text: str, voice: str, instructions: str, output: Path
    ) -> None:
        output.parent.mkdir(parents=True, exist_ok=True)
        with self.client.audio.speech.with_streaming_response.create(
            model=self.model,
            voice=voice,
            input=text,
            instructions=instructions,
            response_format="wav",
            speed=0.92,
        ) as response:
            response.stream_to_file(output)


class OpenAICompatibleTTSProvider(TTSProvider):
    name = "openai-compatible"

    def __init__(self, settings: Settings):
        self.base_url = settings.local_tts_base_url.rstrip("/")
        self.api_key = settings.local_tts_api_key
        self.model = settings.local_tts_model
        self.timeout = settings.tts_timeout_seconds

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
            "response_format": "wav",
            "speed": 0.92,
        }
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/audio/speech", headers=headers, json=payload
            )
            response.raise_for_status()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(response.content)


class HiggsTTSProvider(TTSProvider):
    """Native adapter for Higgs TTS 3 served through SGLang-Omni."""

    name = "higgs"
    prefers_tts_text = True

    def __init__(self, settings: Settings):
        self.base_url = settings.higgs_base_url.rstrip("/")
        self.api_key = settings.higgs_api_key
        self.model = settings.higgs_model
        self.temperature = settings.higgs_temperature
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

    def synthesize(
        self, *, text: str, voice: str, instructions: str, output: Path
    ) -> None:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload: dict[str, object] = {
            "model": self.model,
            "voice": voice,
            "input": text,
            "response_format": "wav",
            "temperature": self.temperature,
            "top_k": self.top_k,
            "max_new_tokens": self.max_new_tokens,
        }
        references = self.voices.reference_payload(
            voice, required=self.require_references
        )
        if references:
            payload["references"] = references
        if self.seed is not None:
            payload["seed"] = self.seed

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
