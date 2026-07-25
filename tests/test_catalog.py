from pathlib import Path
from app.catalog import StoryCatalog

def test_bundled_stories_validate():
    stories = StoryCatalog(Path("stories")).list()
    assert len(stories) >= 8
    assert stories[0].id == "alexandru-marele-garaj-fermecat"
    assert all(s.start_scene for s in stories)

def test_all_stories_have_interaction():
    for story in StoryCatalog(Path("stories")).list():
        assert any(scene.choices for scene in story.scenes), story.id
