from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, model_validator

class Character(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9_-]+$")
    name: str
    description: str = ""
    voice: str = "marin"
    voice_instructions: str = ""

class Segment(BaseModel):
    role: str
    text: str = Field(min_length=1, max_length=4096)
    delivery: str = ""
    pause_after_ms: int = Field(default=650, ge=0, le=10000)

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
    choices: list[Choice] = []
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
    schema_version: int = 1
    id: str = Field(pattern=r"^[a-z0-9_-]+$")
    episode: int = Field(ge=1)
    title: str
    subtitle: str = ""
    summary: str
    age_min: int = Field(default=2, ge=1, le=12)
    age_max: int = Field(default=6, ge=1, le=14)
    estimated_minutes: int = Field(default=7, ge=1, le=60)
    themes: list[str] = []
    learning_goals: list[str] = []
    narrator_instructions: str
    characters: list[Character]
    start_scene: str
    scenes: list[Scene] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_graph(self):
        if self.age_min > self.age_max:
            raise ValueError("age_min nu poate fi mai mare decât age_max")
        scene_ids = [s.id for s in self.scenes]
        if len(scene_ids) != len(set(scene_ids)):
            raise ValueError("ID-uri de scene duplicate")
        if self.start_scene not in scene_ids:
            raise ValueError("start_scene nu există")
        role_ids = {c.id for c in self.characters} | {"narrator"}
        for scene in self.scenes:
            for seg in scene.segments:
                if seg.role not in role_ids:
                    raise ValueError(f"Rol necunoscut {seg.role} în scena {scene.id}")
            refs = ([scene.next_scene] if scene.next_scene else []) + [c.next_scene for c in scene.choices]
            for ref in refs:
                if ref not in scene_ids:
                    raise ValueError(f"Scena {scene.id} referă scena inexistentă {ref}")
        reachable = set()
        stack = [self.start_scene]
        scene_map = {s.id: s for s in self.scenes}
        while stack:
            sid = stack.pop()
            if sid in reachable:
                continue
            reachable.add(sid)
            scene = scene_map[sid]
            if scene.next_scene:
                stack.append(scene.next_scene)
            stack.extend(c.next_scene for c in scene.choices)
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
