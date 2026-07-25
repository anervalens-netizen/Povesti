from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from .higgs import validate_higgs_text


class Character(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9_-]+$")
    name: str
    description: str = ""
    voice: str = "masinuta-jucausa"
    voice_instructions: str = ""


class Segment(BaseModel):
    role: str
    text: str = Field(min_length=1, max_length=4096)
    tts_text: str | None = Field(default=None, min_length=1, max_length=4096)
    delivery: str = ""
    pause_after_ms: int = Field(default=650, ge=0, le=10000)

    @field_validator("tts_text")
    @classmethod
    def validate_tts_text(cls, value: str | None) -> str | None:
        return validate_higgs_text(value) if value else value


class Choice(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9_-]+$")
    label: str
    prompt: str = ""
    next_scene: str


class Scene(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9_-]+$")
    title: str
    kind: Literal["story", "choice", "ending"] = "story"
    direction: str = ""
    segments: list[Segment] = Field(min_length=1)
    choices: list[Choice] = Field(default_factory=list)
    next_scene: str | None = None

    @model_validator(mode="after")
    def validate_routing(self):
        if self.kind == "choice" and len(self.choices) < 2:
            raise ValueError(f"Scena {self.id}: o alegere trebuie să aibă minimum două opțiuni")
        if self.kind == "ending" and (self.next_scene or self.choices):
            raise ValueError(f"Scena {self.id}: finalul nu poate continua")
        if self.kind == "story" and self.choices:
            raise ValueError(f"Scena {self.id}: alegerile necesită kind=choice")
        return self


class Story(BaseModel):
    schema_version: int = 2
    id: str = Field(pattern=r"^[a-z0-9_-]+$")
    episode: int = Field(ge=1)
    title: str
    subtitle: str = ""
    summary: str
    age_min: int = Field(default=2, ge=1, le=12)
    age_max: int = Field(default=6, ge=1, le=14)
    estimated_minutes: int = Field(default=7, ge=1, le=60)
    themes: list[str] = Field(default_factory=list)
    learning_goals: list[str] = Field(default_factory=list)
    narrator_instructions: str = ""
    narrator_voice: str = "narator"
    characters: list[Character]
    start_scene: str
    scenes: list[Scene] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_graph(self):
        if self.age_min > self.age_max:
            raise ValueError("age_min nu poate fi mai mare decât age_max")
        scene_ids = [scene.id for scene in self.scenes]
        if len(scene_ids) != len(set(scene_ids)):
            raise ValueError("ID-uri de scene duplicate")
        if self.start_scene not in scene_ids:
            raise ValueError("start_scene nu există")
        role_ids = {character.id for character in self.characters} | {"narrator"}
        for scene in self.scenes:
            for segment in scene.segments:
                if segment.role not in role_ids:
                    raise ValueError(f"Rol necunoscut {segment.role} în scena {scene.id}")
            refs = ([scene.next_scene] if scene.next_scene else []) + [
                choice.next_scene for choice in scene.choices
            ]
            for ref in refs:
                if ref not in scene_ids:
                    raise ValueError(f"Scena {scene.id} referă scena inexistentă {ref}")
        reachable: set[str] = set()
        stack = [self.start_scene]
        scene_map = {scene.id: scene for scene in self.scenes}
        while stack:
            scene_id = stack.pop()
            if scene_id in reachable:
                continue
            reachable.add(scene_id)
            current = scene_map[scene_id]
            if current.next_scene:
                stack.append(current.next_scene)
            stack.extend(choice.next_scene for choice in current.choices)
        unreachable = set(scene_ids) - reachable
        if unreachable:
            raise ValueError(f"Scene inaccesibile: {', '.join(sorted(unreachable))}")
        return self


class GenerationRequest(BaseModel):
    title_idea: str = Field(min_length=3, max_length=200)
    lesson: str = Field(min_length=3, max_length=300)
    favorite_elements: str = Field(default="mașinuțe, familie, aventură", max_length=500)
    age: int = Field(default=3, ge=2, le=10)
    estimated_minutes: int = Field(default=7, ge=3, le=15)
    choices: int = Field(default=2, ge=1, le=4)
