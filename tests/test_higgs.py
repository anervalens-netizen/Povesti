import json
from dataclasses import replace
from pathlib import Path

import pytest

from app.catalog import StoryCatalog
from app.config import settings
from app.higgs import (
    VoiceRegistry,
    audit_higgs_text,
    compile_higgs_text,
    merge_voice_prefix,
    validate_higgs_text,
)
from app.tts import HiggsTTSProvider

ROOT = Path(__file__).resolve().parents[1]


def test_published_stories_are_higgs_ready():
    stories = StoryCatalog(ROOT / "stories").list()
    profiles = set(
        json.loads((ROOT / "voices" / "voices.json").read_text(encoding="utf-8"))[
            "profiles"
        ]
    )
    assert len(stories) == 28
    assert sum(len(story.scenes) for story in stories) == 229
    assert sum(len(scene.segments) for story in stories for scene in story.scenes) == 1435

    explorer_series = [
        story for story in stories if story.series == "Clubul Micilor Exploratori"
    ]
    inventor_series = [
        story for story in stories if story.series == "Atelierul Micilor Inventatori"
    ]
    assert len(explorer_series) == 10
    assert len(inventor_series) == 10
    assert [story.series_episode for story in explorer_series] == list(range(1, 11))
    assert [story.series_episode for story in inventor_series] == list(range(1, 11))

    for story in stories:
        assert story.schema_version == 2
        assert story.narrator_voice in profiles
        for character in story.characters:
            assert character.voice in profiles
        for scene in story.scenes:
            for segment in scene.segments:
                assert segment.tts_text
                validate_higgs_text(segment.tts_text)


def test_voice_prefix_is_merged_in_canonical_order():
    registry = VoiceRegistry(ROOT / "voices", ROOT / "voices" / "voices.json")
    value = registry.prepare_text(
        "tati", "<|emotion:affection|>Sunt aici.", "cald"
    )
    assert value.startswith(
        "<|emotion:affection|><|prosody:speed_slow|><|prosody:pitch_low|>"
    )
    assert value.endswith("Sunt aici.")


def test_explicit_segment_control_overrides_voice_default():
    value = merge_voice_prefix(
        "<|prosody:pitch_high|><|prosody:expressive_high|>",
        "<|emotion:contentment|><|prosody:pitch_low|><|prosody:expressive_low|>Salut.",
    )
    assert "pitch_low" in value
    assert "expressive_low" in value
    assert "pitch_high" not in value
    assert "expressive_high" not in value


def test_conflicting_or_misplaced_controls_are_rejected():
    with pytest.raises(ValueError, match="grupa speed"):
        validate_higgs_text(
            "<|prosody:speed_slow|><|prosody:speed_fast|>Salut"
        )
    with pytest.raises(ValueError, match="Pauzele Higgs"):
        validate_higgs_text("<|prosody:pause|>Salut")
    with pytest.raises(ValueError, match="prefix continuu"):
        validate_higgs_text("Salut. <|emotion:surprise|>Uau!")


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


def test_quality_audit_warns_about_oversized_turn():
    warnings = audit_higgs_text("<|emotion:contentment|>" + "cuvânt " * 110)
    assert any("100 de cuvinte" in warning for warning in warnings)


def _voice_fixture(tmp_path: Path, name: str = "narator") -> tuple[Path, Path]:
    voice_dir = tmp_path / "voices"
    voice_dir.mkdir()
    (voice_dir / f"{name}.wav").write_bytes(b"RIFF-test")
    manifest = voice_dir / "voices.json"
    manifest.write_text(
        json.dumps(
            {
                "profiles": {
                    name: {
                        "reference_audio": f"{name}.wav",
                        "reference_text": "Acesta este transcriptul exact.",
                        "prefix": "<|prosody:pitch_low|>",
                        "description": "test",
                    }
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return voice_dir, manifest


def test_higgs_payload_uses_named_api_voice_and_local_reference(tmp_path: Path):
    voice_dir, manifest = _voice_fixture(tmp_path, "tati")
    provider = HiggsTTSProvider(
        replace(
            settings,
            voice_dir=voice_dir,
            voice_manifest=manifest,
            higgs_api_voice="default",
            higgs_top_p=0.95,
            higgs_require_references=True,
            higgs_use_profile_voice=False,
        )
    )
    payload = provider.build_payload(
        text="<|emotion:affection|>Sunt aici.", profile_voice="tati"
    )
    assert payload["voice"] == "default"
    assert payload["top_p"] == 0.95
    assert payload["references"][0]["text"] == "Acesta este transcriptul exact."
    assert payload["references"][0]["audio_path"].startswith("data:audio/")
    assert ";base64," in payload["references"][0]["audio_path"]


def test_higgs_payload_omits_empty_api_voice(tmp_path: Path):
    voice_dir, manifest = _voice_fixture(tmp_path)
    provider = HiggsTTSProvider(
        replace(
            settings,
            voice_dir=voice_dir,
            voice_manifest=manifest,
            higgs_api_voice="",
            higgs_require_references=True,
            higgs_use_profile_voice=False,
        )
    )
    payload = provider.build_payload(text="Poveste.", profile_voice="narator")
    assert "voice" not in payload
    assert "references" in payload


def test_higgs_payload_uses_uploaded_profile_voice(tmp_path: Path):
    voice_dir, manifest = _voice_fixture(tmp_path)
    provider = HiggsTTSProvider(
        replace(
            settings,
            voice_dir=voice_dir,
            voice_manifest=manifest,
            higgs_use_profile_voice=True,
            higgs_require_references=True,
        )
    )
    payload = provider.build_payload(text="Poveste.", profile_voice="narator")
    assert payload["voice"] == "narator"
    assert "references" not in payload
