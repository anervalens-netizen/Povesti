from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.catalog import StoryCatalog
from app.config import settings

stories = StoryCatalog(settings.story_dir).list()
voice_manifest = json.loads(settings.voice_manifest.read_text(encoding="utf-8"))
voices = set(voice_manifest.get("profiles", {}))
scene_count = 0
segment_count = 0

for story in stories:
    used_voices = {story.narrator_voice} | {character.voice for character in story.characters}
    unknown = used_voices - voices
    if unknown:
        raise ValueError(f"{story.id}: profiluri vocale necunoscute: {sorted(unknown)}")
    for scene in story.scenes:
        scene_count += 1
        for segment in scene.segments:
            segment_count += 1
            if not segment.tts_text:
                raise ValueError(f"{story.id}/{scene.id}: lipsește tts_text")

print(
    f"OK: {len(stories)} povești, {scene_count} scene și "
    f"{segment_count} replici Higgs valide"
)
for story in stories:
    print(f"  {story.episode:02d}. {story.title} ({len(story.scenes)} scene)")
