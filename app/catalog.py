from __future__ import annotations

import base64
import gzip
import json
import shutil
from pathlib import Path

from .schemas import Story


class StoryCatalog:
    def __init__(self, story_dir: Path):
        self.story_dir = story_dir

    def _read(self, path: Path) -> dict:
        if path.suffix.lower() == ".json":
            return json.loads(path.read_text(encoding="utf-8"))
        if path.suffix.lower() in {".yaml", ".yml"}:
            try:
                import yaml
            except ImportError as exc:
                raise RuntimeError("Pentru YAML instalează PyYAML") from exc
            return yaml.safe_load(path.read_text(encoding="utf-8"))
        raise ValueError(f"Format nesuportat: {path}")

    def _parse_jsonl(self, content: str, source: Path) -> list[dict]:
        stories: list[dict] = []
        for line_number, line in enumerate(content.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                stories.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"JSON invalid în {source}, linia {line_number}: {exc}"
                ) from exc
        if not stories:
            raise ValueError(f"Fișierul de serie {source} nu conține povești")
        return stories

    def _read_jsonl(self, path: Path) -> list[dict]:
        return self._parse_jsonl(path.read_text(encoding="utf-8"), path)

    def _read_story_pack(self, path: Path) -> list[dict]:
        try:
            encoded = path.read_text(encoding="ascii").strip()
            compressed = base64.b64decode(encoded, validate=True)
            content = gzip.decompress(compressed).decode("utf-8")
        except (ValueError, OSError, UnicodeError) as exc:
            raise ValueError(f"Story pack invalid: {path}") from exc
        return self._parse_jsonl(content, path)

    def _read_directory(self, path: Path) -> dict:
        story_path = path / "story.json"
        if not story_path.exists():
            raise ValueError(f"Lipsește {story_path}")
        data = self._read(story_path)
        if data.get("scenes"):
            return data
        scene_dir = path / "scenes"
        scene_paths = sorted(scene_dir.glob("*.json")) + sorted(
            scene_dir.glob("*.yaml")
        )
        if not scene_paths:
            raise ValueError(f"Povestea {path.name} nu are scene")
        data["scenes"] = [self._read(scene_path) for scene_path in scene_paths]
        return data

    def list(self) -> list[Story]:
        stories: list[Story] = []
        for path in sorted(self.story_dir.iterdir()):
            if path.is_dir() and (path / "story.json").exists():
                stories.append(Story.model_validate(self._read_directory(path)))
            elif path.is_file() and path.suffix.lower() in {".json", ".yaml", ".yml"}:
                stories.append(Story.model_validate(self._read(path)))
            elif path.is_file() and path.suffix.lower() == ".jsonl":
                stories.extend(
                    Story.model_validate(data) for data in self._read_jsonl(path)
                )
            elif path.is_file() and path.name.endswith(".jsonl.gz.b64"):
                stories.extend(
                    Story.model_validate(data) for data in self._read_story_pack(path)
                )
        return sorted(stories, key=lambda story: (story.episode, story.title))

    def get(self, story_id: str) -> Story:
        for story in self.list():
            if story.id == story_id:
                return story
        raise KeyError(story_id)

    def save(self, story: Story, overwrite: bool = False) -> Path:
        story_path = self.story_dir / story.id
        if story_path.exists() and not overwrite:
            raise FileExistsError(story_path)
        if story_path.exists():
            shutil.rmtree(story_path)
        story_path.mkdir(parents=True)
        target = story_path / "story.json"
        target.write_text(
            json.dumps(story.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return story_path
