from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import re
import wave
from dataclasses import dataclass
from pathlib import Path

EMOTIONS = {
    "elation", "amusement", "enthusiasm", "determination", "pride", "contentment",
    "affection", "relief", "contemplation", "confusion", "surprise", "awe", "longing",
    "arousal", "anger", "fear", "disgust", "bitterness", "sadness", "shame", "helplessness",
}
STYLES = {"singing", "shouting", "whispering"}
PROSODY_SPEED = {"speed_very_slow", "speed_slow", "speed_fast", "speed_very_fast"}
PROSODY_PITCH = {"pitch_low", "pitch_high"}
PROSODY_EXPRESSIVE = {"expressive_high", "expressive_low"}
PROSODY_SENTENCE = PROSODY_SPEED | PROSODY_PITCH | PROSODY_EXPRESSIVE
PROSODY_INLINE = {"pause", "long_pause"}
SFX = {"cough", "laughter", "crying", "screaming", "burping", "humming", "sigh", "sniff", "sneeze"}
SFX_CUES = {
    "cough": ("ahem",),
    "laughter": ("haha", "hehe", "ha-ha"),
    "crying": ("boohoo", "sob"),
    "screaming": ("ah", "ahh", "aaah"),
    "burping": ("burp",),
    "humming": ("hmm", "mmm"),
    "sigh": ("uh", "uf", "of", "ah", "ahh", "haah"),
    "sniff": ("sff", "snif"),
    "sneeze": ("achoo", "hapciu"),
}
TAG_RE = re.compile(r"<\|(emotion|style|prosody|sfx):([a-z_]+)\|>")
ANY_CONTROL_RE = re.compile(r"<\|[^|]+\|>")
WORD_AFTER_TAG_RE = re.compile(r"^[^\s<|>.,!?;:—–]+", re.UNICODE)
DELIVERY_GROUP_ORDER = ("emotion", "style", "speed", "pitch", "expressive")


def _delivery_group(category: str, tag: str) -> str | None:
    if category in {"emotion", "style"}:
        return category
    if category != "prosody":
        return None
    if tag in PROSODY_SPEED:
        return "speed"
    if tag in PROSODY_PITCH:
        return "pitch"
    if tag in PROSODY_EXPRESSIVE:
        return "expressive"
    return None


def _leading_delivery_tokens(value: str) -> tuple[dict[str, str], int]:
    controls: dict[str, str] = {}
    position = 0
    while True:
        match = TAG_RE.match(value, position)
        if not match:
            break
        group = _delivery_group(match.group(1), match.group(2))
        if group is None:
            break
        if group in controls:
            raise ValueError(f"Comenzi Higgs contradictorii pentru grupa {group}")
        controls[group] = match.group(0)
        position = match.end()
    return controls, position


def validate_higgs_text(value: str) -> str:
    """Validate the official Higgs TTS 3 control grammar and placement rules."""
    if not value or not value.strip():
        raise ValueError("Textul Higgs nu poate fi gol")

    matches = list(TAG_RE.finditer(value))
    recognized = {match.group(0) for match in matches}
    unknown = [token for token in ANY_CONTROL_RE.findall(value) if token not in recognized]
    if unknown:
        raise ValueError(f"Taguri Higgs necunoscute: {', '.join(sorted(set(unknown)))}")

    leading_controls, leading_end = _leading_delivery_tokens(value)

    for match in matches:
        category, tag = match.group(1), match.group(2)
        if category == "emotion" and tag not in EMOTIONS:
            raise ValueError(f"Emoție Higgs necunoscută: {tag}")
        if category == "style" and tag not in STYLES:
            raise ValueError(f"Stil Higgs necunoscut: {tag}")
        if category == "prosody" and tag not in PROSODY_SENTENCE | PROSODY_INLINE:
            raise ValueError(f"Prosodie Higgs necunoscută: {tag}")
        if category == "sfx" and tag not in SFX:
            raise ValueError(f"Efect Higgs necunoscut: {tag}")

        group = _delivery_group(category, tag)
        if group is not None:
            if match.start() >= leading_end:
                raise ValueError(
                    "Tagurile de emoție/stil/viteză/pitch/expresivitate trebuie să formeze "
                    "un prefix continuu la începutul replicii"
                )
            if group not in leading_controls or leading_controls[group] != match.group(0):
                raise ValueError(f"Comenzi Higgs contradictorii pentru grupa {group}")
            continue

        visible_before = ANY_CONTROL_RE.sub("", value[: match.start()]).strip()
        if category == "prosody" and tag in PROSODY_INLINE and not visible_before:
            raise ValueError("Pauzele Higgs sunt poziționale și nu pot preceda primul cuvânt")

        if category == "sfx":
            remainder = value[match.end() :]
            cue_match = WORD_AFTER_TAG_RE.match(remainder)
            if cue_match is None:
                raise ValueError("După un tag sfx trebuie să urmeze imediat onomatopeea")

    spoken = ANY_CONTROL_RE.sub("", value).strip()
    if not spoken:
        raise ValueError("Textul Higgs trebuie să conțină și cuvinte rostite")
    return value


def audit_higgs_text(value: str) -> list[str]:
    """Return non-blocking quality warnings after strict validation succeeds."""
    validate_higgs_text(value)
    warnings: list[str] = []
    plain = ANY_CONTROL_RE.sub("", value)
    word_count = len(plain.split())
    if len(value) > 700:
        warnings.append("replică foarte lungă; recomandat să fie împărțită în mai multe segmente")
    if word_count > 100:
        warnings.append("peste 100 de cuvinte într-un singur turn TTS")

    delivery, _ = _leading_delivery_tokens(value)
    if len(delivery) > 4:
        warnings.append("prea multe comenzi globale; păstrează doar controalele care schimbă clar rostirea")

    sfx_matches = [match for match in TAG_RE.finditer(value) if match.group(1) == "sfx"]
    if len(sfx_matches) > 2:
        warnings.append("mai mult de două efecte sonore într-o singură replică")
    for match in sfx_matches:
        cue_match = WORD_AFTER_TAG_RE.match(value[match.end() :])
        cue = cue_match.group(0).casefold() if cue_match else ""
        recommended = SFX_CUES.get(match.group(2), ())
        if recommended and not any(cue.startswith(item) for item in recommended):
            warnings.append(
                f"onomatopeea «{cue}» pentru {match.group(2)} diferă de indiciile testate oficial"
            )
    if re.search(r"(?:<\|prosody:(?:pause|long_pause)\|>\s*){2,}", value):
        warnings.append("pauze consecutive; folosește o singură pauză adecvată")
    return warnings


def _pick_delivery(
    delivery: str,
) -> tuple[str | None, str | None, str | None, str | None, str | None]:
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

    style = None
    if any(needle in normalized for needle in ("șopt", "soapta", "șoapt")):
        style = "whispering"
    elif any(needle in normalized for needle in ("strig", "proiectat")):
        style = "shouting"
    elif "cânt" in normalized:
        style = "singing"

    speed = None
    if any(needle in normalized for needle in ("foarte lent", "foarte rar", "foarte domol")):
        speed = "speed_very_slow"
    elif any(needle in normalized for needle in ("lent", "rar", "domol", "liniștit")):
        speed = "speed_slow"
    elif any(needle in normalized for needle in ("foarte rapid", "foarte repede")):
        speed = "speed_very_fast"
    elif any(needle in normalized for needle in ("rapid", "repede", "energic", "ritmat")):
        speed = "speed_fast"

    pitch = None
    if any(needle in normalized for needle in ("voce joasă", "ton jos", "grav")):
        pitch = "pitch_low"
    elif any(needle in normalized for needle in ("voce înaltă", "ton înalt", "subțire")):
        pitch = "pitch_high"

    expressive = None
    if any(needle in normalized for needle in ("expresiv", "dramatic", "entuziast", "uimire")):
        expressive = "expressive_high"
    elif any(needle in normalized for needle in ("neutru", "plat", "fără dramatism")):
        expressive = "expressive_low"
    return emotion, style, speed, pitch, expressive


def compile_higgs_text(text: str, delivery: str = "") -> str:
    """Deterministic fallback for stories without an explicit canonical tts_text."""
    if ANY_CONTROL_RE.search(text):
        return validate_higgs_text(text)
    emotion, style, speed, pitch, expressive = _pick_delivery(delivery)
    prefix = "".join(
        token
        for token in (
            f"<|emotion:{emotion}|>" if emotion else "",
            f"<|style:{style}|>" if style else "",
            f"<|prosody:{speed}|>" if speed else "",
            f"<|prosody:{pitch}|>" if pitch else "",
            f"<|prosody:{expressive}|>" if expressive else "",
        )
        if token
    )
    body = re.sub(r"\s*\.{3,}\s*", " <|prosody:pause|> ", text).strip()
    for pattern, tag in (
        (r"^(Hehe|Haha|Ha-ha)", "laughter"),
        (r"^(Hmm|Mmm)", "humming"),
        (r"^(Of|Uf|Uh|Ahh|Haah)", "sigh"),
        (r"^(Ahem)", "cough"),
        (r"^(Hapciu|Achoo)", "sneeze"),
    ):
        if re.search(pattern, body, flags=re.I):
            body = f"<|sfx:{tag}|>" + body
            break
    return validate_higgs_text(prefix + body)


def merge_voice_prefix(prefix: str, text: str) -> str:
    """Merge defaults with explicit controls; explicit segment controls win by group."""
    if prefix:
        validate_higgs_text(prefix + "voce")
    validate_higgs_text(text)

    prefix_controls, prefix_end = _leading_delivery_tokens(prefix)
    if prefix and prefix_end != len(prefix):
        raise ValueError("Prefixul vocal poate conține numai comenzi globale Higgs")
    text_controls, text_end = _leading_delivery_tokens(text)

    merged = {
        group: text_controls.get(group) or prefix_controls.get(group)
        for group in DELIVERY_GROUP_ORDER
    }
    body = text[text_end:]
    result = "".join(merged[group] or "" for group in DELIVERY_GROUP_ORDER) + body
    return validate_higgs_text(result)


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
        for profile in self.profiles.values():
            if not profile.reference_text.strip():
                raise ValueError(f"Transcript vocal gol pentru profilul {profile.name}")
            if profile.prefix:
                merge_voice_prefix(profile.prefix, "test")

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

    def audit_reference(self, name: str, *, required: bool = False) -> list[str]:
        profile = self.get(name)
        if profile is None:
            raise ValueError(f"Profil vocal inexistent: {name}")
        path = self.voice_dir / profile.reference_audio
        if not path.is_file():
            if required:
                raise FileNotFoundError(f"Lipsește referința vocală {path}")
            return ["referință audio absentă; randarea strictă va fi blocată"]
        warnings: list[str] = []
        if path.suffix.casefold() == ".wav":
            try:
                with wave.open(str(path), "rb") as audio:
                    channels = audio.getnchannels()
                    sample_width = audio.getsampwidth()
                    sample_rate = audio.getframerate()
                    duration = audio.getnframes() / max(sample_rate, 1)
            except wave.Error as exc:
                raise ValueError(f"Fișier WAV invalid pentru {name}: {exc}") from exc
            if channels != 1:
                warnings.append(f"referința are {channels} canale; mono este recomandat")
            if sample_width != 2:
                warnings.append(f"referința nu este PCM 16-bit ({sample_width * 8}-bit)")
            if sample_rate not in {24000, 48000}:
                warnings.append(f"sample rate {sample_rate} Hz; recomandat 24000 sau 48000 Hz")
            if duration < 4:
                warnings.append(f"referință foarte scurtă ({duration:.1f}s); recomandat 6-15s")
            elif duration > 20:
                warnings.append(f"referință lungă ({duration:.1f}s); recomandat 6-15s")
        return warnings

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
