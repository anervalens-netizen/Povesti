from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path

from .schemas import Story
from .tts import TTSProvider

ProgressCallback = Callable[[int, int], None]


class AudioRenderer:
    def __init__(self, media_dir: Path, provider: TTSProvider):
        self.media_dir = media_dir
        self.provider = provider

    def render(
        self,
        story: Story,
        force: bool = False,
        progress: ProgressCallback | None = None,
    ) -> dict:
        story_dir = self.media_dir / story.id
        story_dir.mkdir(parents=True, exist_ok=True)
        roles = {character.id: character for character in story.characters}
        total = sum(len(scene.segments) for scene in story.scenes)
        completed = 0
        manifest = {
            "story_id": story.id,
            "provider": self.provider.name,
            "scenes": {},
        }

        for scene in story.scenes:
            items = []
            for index, segment in enumerate(scene.segments, start=1):
                character = roles.get(segment.role)
                if segment.role == "narrator":
                    voice = story.narrator_voice
                    role_instructions = story.narrator_instructions
                else:
                    voice = character.voice if character else "masinuta-jucausa"
                    role_instructions = character.voice_instructions if character else ""

                source_text = (
                    segment.tts_text
                    if self.provider.prefers_tts_text and segment.tts_text
                    else segment.text
                )
                tts_input = self.provider.prepare_text(
                    text=source_text,
                    voice=voice,
                    delivery=segment.delivery,
                )
                instructions = "\n".join(
                    value
                    for value in (
                        story.narrator_instructions,
                        scene.direction,
                        role_instructions,
                        segment.delivery,
                    )
                    if value
                )
                digest_source = "|".join(
                    (
                        self.provider.name,
                        self.provider.voice_fingerprint(voice),
                        instructions,
                        tts_input,
                    )
                )
                digest = hashlib.sha256(digest_source.encode("utf-8")).hexdigest()[:16]
                relative_path = Path(story.id) / scene.id / f"{index:02d}-{digest}.wav"
                target = self.media_dir / relative_path
                if force or not target.exists():
                    self.provider.synthesize(
                        text=tts_input,
                        voice=voice,
                        instructions=instructions,
                        output=target,
                    )
                items.append(
                    {
                        "role": segment.role,
                        "text": segment.text,
                        "tts_input": tts_input,
                        "audio_url": f"/media/{relative_path.as_posix()}",
                        "pause_after_ms": segment.pause_after_ms,
                        "voice": voice,
                    }
                )
                completed += 1
                if progress:
                    progress(completed, total)
            manifest["scenes"][scene.id] = items

        manifest_path = story_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return manifest

    def read_manifest(self, story_id: str) -> dict | None:
        path = self.media_dir / story_id / "manifest.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
