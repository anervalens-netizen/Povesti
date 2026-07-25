from __future__ import annotations

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

    def _read_directory(self, path: Path) -> dict:
        story_path = path / "story.json"
        if not story_path.exists():
            raise ValueError(f"Lipsește {story_path}")
        data = self._read(story_path)
        # Schema v2 stores the complete episode in one reviewable file.
        if data.get("scenes"):
            return data
        # Backward compatibility with the initial split-scene format.
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
