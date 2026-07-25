import json
from pathlib import Path

import pytest

from app.catalog import StoryCatalog
from app.higgs import VoiceRegistry, compile_higgs_text, validate_higgs_text

ROOT = Path(__file__).resolve().parents[1]


def test_published_stories_are_higgs_ready():
    stories = StoryCatalog(ROOT / "stories").list()
    profiles = set(
        json.loads((ROOT / "voices" / "voices.json").read_text(encoding="utf-8"))[
            "profiles"
        ]
    )
    assert len(stories) == 8
    assert sum(len(story.scenes) for story in stories) == 69
    assert sum(len(scene.segments) for story in stories for scene in story.scenes) == 415
    for story in stories:
        assert story.schema_version == 2
        assert story.narrator_voice in profiles
        for character in story.characters:
            assert character.voice in profiles
        for scene in story.scenes:
            for segment in scene.segments:
                assert segment.tts_text
                validate_higgs_text(segment.tts_text)


def test_voice_prefix_is_merged_with_segment_controls():
    registry = VoiceRegistry(ROOT / "voices", ROOT / "voices" / "voices.json")
    value = registry.prepare_text(
        "tati", "<|emotion:affection|>Sunt aici.", "cald"
    )
    assert value.startswith("<|prosody:pitch_low|><|prosody:speed_slow|>")
    assert "<|emotion:affection|>" in value
    assert value.endswith("Sunt aici.")


def test_invalid_tag_or_sfx_is_rejected():
    with pytest.raises(ValueError):
        validate_higgs_text("<|emotion:fericit|>Salut")
    with pytest.raises(ValueError):
        validate_higgs_text("<|sfx:laughter|> Hehe")


def test_fallback_compiler_keeps_clean_text_and_adds_controls():
    value = compile_higgs_text("Ce idee grozavă... continuăm!", "vesel și lent")
    assert "<|emotion:enthusiasm|>" in value
    assert "<|prosody:speed_slow|>" in value
    assert "<|prosody:pause|>" in value
