from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.catalog import StoryCatalog
from app.config import settings
from app.higgs import TAG_RE, VoiceRegistry, audit_higgs_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validează poveștile și comenzile Higgs TTS 3")
    parser.add_argument(
        "--check-audio",
        action="store_true",
        help="verifică și formatul mostrelor vocale existente",
    )
    parser.add_argument(
        "--require-audio",
        action="store_true",
        help="consideră eroare orice mostră vocală lipsă",
    )
    parser.add_argument(
        "--strict-quality",
        action="store_true",
        help="transformă avertismentele editoriale în erori",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stories = StoryCatalog(settings.story_dir).list()
    voice_manifest = json.loads(settings.voice_manifest.read_text(encoding="utf-8"))
    voices = set(voice_manifest.get("profiles", {}))
    registry = VoiceRegistry(settings.voice_dir, settings.voice_manifest)
    scene_count = 0
    segment_count = 0
    warnings: list[str] = []
    tag_counts: Counter[str] = Counter()

    for story in stories:
        used_voices = {story.narrator_voice} | {
            character.voice for character in story.characters
        }
        unknown = used_voices - voices
        if unknown:
            raise ValueError(
                f"{story.id}: profiluri vocale necunoscute: {sorted(unknown)}"
            )
        for scene in story.scenes:
            scene_count += 1
            for index, segment in enumerate(scene.segments, start=1):
                segment_count += 1
                if not segment.tts_text:
                    raise ValueError(f"{story.id}/{scene.id}/{index}: lipsește tts_text")
                for warning in audit_higgs_text(segment.tts_text):
                    warnings.append(f"{story.id}/{scene.id}/{index}: {warning}")
                for match in TAG_RE.finditer(segment.tts_text):
                    tag_counts[f"{match.group(1)}:{match.group(2)}"] += 1

    if args.check_audio or args.require_audio:
        for voice in sorted(voices):
            for warning in registry.audit_reference(voice, required=args.require_audio):
                warnings.append(f"voice/{voice}: {warning}")

    if warnings:
        print(f"AVERTISMENTE: {len(warnings)}")
        for warning in warnings:
            print(f"  - {warning}")
        if args.strict_quality:
            raise SystemExit(1)

    print(
        f"OK: {len(stories)} povești, {scene_count} scene și "
        f"{segment_count} replici Higgs valide"
    )
    if tag_counts:
        print("Comenzi folosite:")
        for tag, count in tag_counts.most_common():
            print(f"  {tag}: {count}")
    for story in stories:
        print(f"  {story.episode:02d}. {story.title} ({len(story.scenes)} scene)")


if __name__ == "__main__":
    main()
