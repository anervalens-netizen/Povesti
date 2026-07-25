from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.audio import AudioRenderer
from app.catalog import StoryCatalog
from app.config import settings
from app.tts import build_tts_provider

parser = argparse.ArgumentParser()
parser.add_argument("story_id")
parser.add_argument("--force", action="store_true")
args = parser.parse_args()
story = StoryCatalog(settings.story_dir).get(args.story_id)
manifest = AudioRenderer(settings.media_dir, build_tts_provider(settings)).render(
    story, force=args.force
)
print(f"Audio pregătit: {len(manifest['scenes'])} scene")
