from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.catalog import StoryCatalog
from app.config import settings
from app.tts import HiggsTTSProvider


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Arată textul final și payloadul Higgs fără a apela modelul"
    )
    parser.add_argument("story_id")
    parser.add_argument("--scene", help="ID-ul scenei; implicit prima scenă")
    parser.add_argument(
        "--segment", type=int, default=1, help="numărul segmentului, începând de la 1"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    story = StoryCatalog(settings.story_dir).get(args.story_id)
    scene = (
        next((item for item in story.scenes if item.id == args.scene), None)
        if args.scene
        else story.scenes[0]
    )
    if scene is None:
        raise SystemExit(f"Scena nu există: {args.scene}")
    if args.segment < 1 or args.segment > len(scene.segments):
        raise SystemExit(
            f"Segment invalid: {args.segment}; scena are {len(scene.segments)} segmente"
        )

    segment = scene.segments[args.segment - 1]
    characters = {character.id: character for character in story.characters}
    if segment.role == "narrator":
        profile_voice = story.narrator_voice
    else:
        character = characters.get(segment.role)
        if character is None:
            raise SystemExit(f"Rol necunoscut: {segment.role}")
        profile_voice = character.voice

    preview_settings = replace(settings, higgs_require_references=False)
    provider = HiggsTTSProvider(preview_settings)
    source = segment.tts_text or segment.text
    compiled = provider.prepare_text(
        text=source, voice=profile_voice, delivery=segment.delivery
    )
    payload = provider.build_payload(text=compiled, profile_voice=profile_voice)
    for reference in payload.get("references", []):
        audio_path = str(reference.get("audio_path", ""))
        reference["audio_path"] = f"<data-url ascuns: {len(audio_path)} caractere>"

    print(f"Poveste: {story.title}")
    print(f"Scenă: {scene.id} — {scene.title}")
    print(f"Segment: {args.segment}/{len(scene.segments)}")
    print(f"Rol: {segment.role}")
    print(f"Profil local: {profile_voice}")
    print(f"Text UI: {segment.text}")
    print(f"Input final Higgs: {compiled}")
    print("Payload:")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
