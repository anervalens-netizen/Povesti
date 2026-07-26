from pathlib import Path

from app.catalog import StoryCatalog

ROOT = Path(__file__).resolve().parents[1]


def test_story_library_is_grouped_into_two_complete_series():
    stories = StoryCatalog(ROOT / "stories").list()
    groups: dict[str, list] = {}
    for story in stories:
        groups.setdefault(story.series, []).append(story)

    assert set(groups) == {"Marele Garaj Fermecat", "Clubul Micilor Exploratori"}
    assert len(groups["Marele Garaj Fermecat"]) == 8
    assert len(groups["Clubul Micilor Exploratori"]) == 10
    assert [story.series_episode for story in groups["Clubul Micilor Exploratori"]] == list(range(1, 11))


def test_explorer_series_has_unique_ids_and_complete_routes():
    stories = StoryCatalog(ROOT / "stories").list()
    explorers = [story for story in stories if story.series == "Clubul Micilor Exploratori"]
    assert len({story.id for story in explorers}) == 10
    for story in explorers:
        assert len(story.scenes) == 8
        assert any(scene.kind == "choice" for scene in story.scenes)
        assert any(scene.kind == "ending" for scene in story.scenes)
        assert all(segment.tts_text for scene in story.scenes for segment in scene.segments)
