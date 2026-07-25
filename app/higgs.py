from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import re
from dataclasses import dataclass
from pathlib import Path

EMOTIONS = {
    "elation", "amusement", "enthusiasm", "determination", "pride", "contentment",
    "affection", "relief", "contemplation", "confusion", "surprise", "awe", "longing",
    "arousal", "anger", "fear", "disgust", "bitterness", "sadness", "shame", "helplessness",
}
STYLES = {"singing", "shouting", "whispering"}
PROSODY_SENTENCE = {
    "speed_very_slow", "speed_slow", "speed_fast", "speed_very_fast",
    "pitch_low", "pitch_high", "expressive_high", "expressive_low",
}
PROSODY_INLINE = {"pause", "long_pause"}
SFX = {"cough", "laughter", "crying", "screaming", "burping", "humming", "sigh", "sniff", "sneeze"}
TAG_RE = re.compile(r"<\|(emotion|style|prosody|sfx):([a-z_]+)\|>")
ANY_CONTROL_RE = re.compile(r"<\|[^|]+\|>")


def validate_higgs_text(value: str) -> str:
    """Validate only the control grammar published for Higgs TTS 3."""
    matches = list(TAG_RE.finditer(value))
    recognized = {match.group(0) for match in matches}
    unknown = [token for token in ANY_CONTROL_RE.findall(value) if token not in recognized]
    if unknown:
        raise ValueError(f"Taguri Higgs necunoscute: {', '.join(sorted(set(unknown)))}")

    for match in matches:
        category, tag = match.group(1), match.group(2)
        if category == "emotion" and tag not in EMOTIONS:
            raise ValueError(f"Emoție Higgs necunoscută: {tag}")
        if category == "style" and tag not in STYLES:
            raise ValueError(f"Stil Higgs necunoscut: {tag}")
        if category == "prosody" and tag not in PROSODY_SENTENCE | PROSODY_INLINE:
            raise ValueError(f"Prosodie Higgs necunoscută: {tag}")
        if category == "sfx":
            if tag not in SFX:
                raise ValueError(f"Efect Higgs necunoscut: {tag}")
            if match.end() >= len(value) or value[match.end()].isspace():
                raise ValueError("După un tag sfx trebuie să urmeze imediat onomatopeea")

    prefix_end = 0
    while True:
        match = TAG_RE.match(value, prefix_end)
        if not match:
            break
        category, tag = match.group(1), match.group(2)
        if category == "sfx" or (category == "prosody" and tag in PROSODY_INLINE):
            break
        prefix_end = match.end()
    for match in matches:
        category, tag = match.group(1), match.group(2)
        sentence_level = category in {"emotion", "style"} or (
            category == "prosody" and tag in PROSODY_SENTENCE
        )
        if sentence_level and match.start() >= prefix_end and match.start() != 0:
            raise ValueError(
                "Tagurile de emoție/stil/viteză/pitch/expresivitate trebuie să fie la început"
            )
    return value


def _pick_delivery(delivery: str) -> tuple[str | None, str | None, str | None, str | None]:
    normalized = delivery.casefold()
    emotion = None
    for needles, result in (
        (("afectuos", "cald", "blând"), "affection"),
        (("amuz", "jucăuș", "glumeț"), "amusement"),
        (("entuzi", "vesel", "bucur", "încânt"), "enthusiasm"),
        (("hotărât", "ferm", "clar", "protector"), "determination"),
        (("mândru", "sigur"), "pride"),
        (("liniștit", "calm", "mulțumit", "domol"), "contentment"),
        (("ușurat", "ușurată"), "relief"),
        (("gânditor", "reflect", "contempl"), "contemplation"),
        (("nedumer", "confuz"), "confusion"),
        (("surpr", "mirat"), "surprise"),
        (("uimire", "mister"), "awe"),
        (("îngrij", "teamă", "speriat"), "fear"),
        (("trist",), "sadness"),
        (("supărat", "furios"), "anger"),
    ):
        if any(needle in normalized for needle in needles):
            emotion = result
            break

    style = "whispering" if any(
        needle in normalized for needle in ("șopt", "soapta", "șoapt")
    ) else None
    if any(needle in normalized for needle in ("strig", "proiectat")):
        style = "shouting"

    speed = None
    if any(needle in normalized for needle in ("foarte lent", "foarte rar", "foarte domol")):
        speed = "speed_very_slow"
    elif any(needle in normalized for needle in ("lent", "rar", "domol", "liniștit")):
        speed = "speed_slow"
    elif any(needle in normalized for needle in ("rapid", "energic", "ritmat")):
        speed = "speed_fast"

    expressive = "expressive_high" if any(
        needle in normalized for needle in ("expresiv", "dramatic", "entuziast", "uimire")
    ) else None
    return emotion, style, speed, expressive


def compile_higgs_text(text: str, delivery: str = "") -> str:
    """Deterministic fallback for newly generated stories without explicit tts_text."""
    if ANY_CONTROL_RE.search(text):
        return validate_higgs_text(text)
    emotion, style, speed, expressive = _pick_delivery(delivery)
    prefix = "".join(
        token
        for token in (
            f"<|emotion:{emotion}|>" if emotion else "",
            f"<|style:{style}|>" if style else "",
            f"<|prosody:{speed}|>" if speed else "",
            f"<|prosody:{expressive}|>" if expressive else "",
        )
        if token
    )
    body = re.sub(r"\.{3,}", " <|prosody:pause|> ", text)
    for pattern, tag in (
        (r"^(Hehe|Haha|Ha-ha)", "laughter"),
        (r"^(Hmm|Mmm)", "humming"),
        (r"^(Of|Uf|Ahh)", "sigh"),
        (r"^(Ahem)", "cough"),
    ):
        if re.search(pattern, body, flags=re.I):
            body = f"<|sfx:{tag}|>" + body
            break
    return validate_higgs_text(prefix + body)


def merge_voice_prefix(prefix: str, text: str) -> str:
    if prefix:
        validate_higgs_text(prefix)
    validate_higgs_text(text)
    tags: list[str] = []
    body = text
    for source_name, source in (("prefix", prefix), ("text", text)):
        pos = 0
        while True:
            match = TAG_RE.match(source, pos)
            if not match:
                break
            category, tag = match.group(1), match.group(2)
            if category == "sfx" or (category == "prosody" and tag in PROSODY_INLINE):
                break
            token = match.group(0)
            if token not in tags:
                tags.append(token)
            pos = match.end()
        if source_name == "text":
            body = source[pos:]
    return validate_higgs_text("".join(tags) + body)


@dataclass(frozen=True)
class VoiceProfile:
    name: str
    reference_audio: str
    reference_text: str
    prefix: str = ""
    description: str = ""


class VoiceRegistry:
    def __init__(self, voice_dir: Path, manifest_path: Path):
        self.voice_dir = voice_dir
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.profiles = {
            name: VoiceProfile(name=name, **profile)
            for name, profile in raw.get("profiles", {}).items()
        }

    def get(self, name: str) -> VoiceProfile | None:
        return self.profiles.get(name)

    def prepare_text(self, name: str, text: str, delivery: str = "") -> str:
        profile = self.get(name)
        compiled = compile_higgs_text(text, delivery)
        return merge_voice_prefix(profile.prefix if profile else "", compiled)

    def reference_payload(self, name: str, *, required: bool) -> list[dict[str, str]] | None:
        profile = self.get(name)
        if not profile:
            if required:
                raise FileNotFoundError(f"Profil vocal inexistent: {name}")
            return None
        audio_path = (self.voice_dir / profile.reference_audio).resolve()
        if not audio_path.is_file():
            if required:
                raise FileNotFoundError(
                    f"Lipsește referința vocală {audio_path}. Vezi voices/README.md"
                )
            return None
        mime = mimetypes.guess_type(audio_path.name)[0] or "audio/wav"
        encoded = base64.b64encode(audio_path.read_bytes()).decode("ascii")
        return [{
            "audio_path": f"data:{mime};base64,{encoded}",
            "text": profile.reference_text,
        }]

    def fingerprint(self, name: str) -> str:
        profile = self.get(name)
        if not profile:
            return name
        path = self.voice_dir / profile.reference_audio
        digest = hashlib.sha256()
        digest.update(json.dumps(profile.__dict__, ensure_ascii=False, sort_keys=True).encode())
        if path.is_file():
            digest.update(path.read_bytes())
        return digest.hexdigest()[:20]
