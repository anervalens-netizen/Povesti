from __future__ import annotations

import wave
from abc import ABC, abstractmethod
from pathlib import Path

import httpx

from .config import Settings


class TTSProvider(ABC):
    name = "base"

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


def build_tts_provider(settings: Settings) -> TTSProvider:
    if settings.tts_provider == "mock":
        return MockTTSProvider()
    if settings.tts_provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY lipsește")
        return OpenAITTSProvider(settings)
    if settings.tts_provider == "openai-compatible":
        return OpenAICompatibleTTSProvider(settings)
    raise ValueError(f"TTS_PROVIDER necunoscut: {settings.tts_provider}")
