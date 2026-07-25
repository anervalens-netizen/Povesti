import json
import re
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import ValidationError

from app.audio import AudioRenderer
from app.schemas import Choice, Scene, Segment, Story
from app.tts import TTSProvider

ROOT = Path(__file__).resolve().parents[1]


def make_story(title: str = "Poveste de test") -> Story:
    return Story(
        id="poveste-test",
        episode=1,
        title=title,
        summary="Test",
        characters=[],
        start_scene="final",
        scenes=[
            Scene(
                id="final",
                title="Final",
                kind="ending",
                segments=[Segment(role="narrator", text="Sfârșit.")],
            )
        ],
    )


def test_story_json_is_html_safe_and_still_decodes():
    payload = '</script><script>window.pwned = true</script>'
    story = make_story(title=payload)
    environment = Environment(
        loader=FileSystemLoader(ROOT / "app" / "templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )
    html = environment.get_template("story.html").render(
        story=story, has_audio=False
    )

    match = re.search(
        r'<script id="story-data" type="application/json">(.*?)</script>',
        html,
        flags=re.S,
    )
    assert match
    embedded_json = match.group(1)
    assert "</script>" not in embedded_json.lower()
    assert json.loads(embedded_json)["title"] == payload


def test_choice_scene_rejects_linear_successor():
    with pytest.raises(ValidationError, match="nu poate avea și next_scene"):
        Scene(
            id="alegere",
            title="Alegere",
            kind="choice",
            segments=[Segment(role="narrator", text="Alege.")],
            choices=[
                Choice(id="a", label="A", next_scene="final-a"),
                Choice(id="b", label="B", next_scene="final-b"),
            ],
            next_scene="scena-invizibila",
        )


class RecordingProvider(TTSProvider):
    name = "recording"

    def __init__(self, identity: str):
        self.identity = identity
        self.calls = 0

    def cache_identity(self) -> str:
        return self.identity

    def synthesize(
        self, *, text: str, voice: str, instructions: str, output: Path
    ) -> None:
        self.calls += 1
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(self.identity.encode("utf-8"))


def test_audio_cache_changes_with_provider_configuration(tmp_path: Path):
    story = make_story()
    first_provider = RecordingProvider("endpoint-a|model-a|temperature=0.3")
    second_provider = RecordingProvider("endpoint-b|model-b|temperature=0.7")

    first_manifest = AudioRenderer(tmp_path, first_provider).render(story)
    second_manifest = AudioRenderer(tmp_path, second_provider).render(story)

    first_url = first_manifest["scenes"]["final"][0]["audio_url"]
    second_url = second_manifest["scenes"]["final"][0]["audio_url"]
    assert first_url != second_url
    assert first_provider.calls == 1
    assert second_provider.calls == 1
    assert len(list((tmp_path / story.id / "final").glob("*.wav"))) == 2
