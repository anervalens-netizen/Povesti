from pathlib import Path

from app.catalog import StoryCatalog

ROOT = Path(__file__).resolve().parents[1]


def test_story_library_is_grouped_into_three_complete_series():
    stories = StoryCatalog(ROOT / "stories").list()
    groups: dict[str, list] = {}
    for story in stories:
        groups.setdefault(story.series, []).append(story)

    assert set(groups) == {
        "Marele Garaj Fermecat",
        "Clubul Micilor Exploratori",
        "Atelierul Micilor Inventatori",
    }
    assert len(groups["Marele Garaj Fermecat"]) == 8
    assert len(groups["Clubul Micilor Exploratori"]) == 10
    assert len(groups["Atelierul Micilor Inventatori"]) == 10
    assert [story.series_episode for story in groups["Clubul Micilor Exploratori"]] == list(range(1, 11))
    assert [story.series_episode for story in groups["Atelierul Micilor Inventatori"]] == list(range(1, 11))


def test_large_series_have_unique_ids_and_complete_routes():
    stories = StoryCatalog(ROOT / "stories").list()
    for series_name in ("Clubul Micilor Exploratori", "Atelierul Micilor Inventatori"):
        selected = [story for story in stories if story.series == series_name]
        assert len({story.id for story in selected}) == 10
        for story in selected:
            assert len(story.scenes) == 8
            assert any(scene.kind == "choice" for scene in story.scenes)
            assert any(scene.kind == "ending" for scene in story.scenes)
            assert all(segment.tts_text for scene in story.scenes for segment in scene.segments)
