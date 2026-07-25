from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.catalog import StoryCatalog
from app.config import settings

stories = StoryCatalog(settings.story_dir).list()
print(f"OK: {len(stories)} povești valide")
for story in stories:
    print(f"  {story.episode:02d}. {story.title} ({len(story.scenes)} scene)")
