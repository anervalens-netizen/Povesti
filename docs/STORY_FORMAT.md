# Formatul poveștilor — schema v2

Fiecare episod este păstrat într-un singur fișier ușor de revizuit:

```text
stories/<id>/story.json
```

Fișierul conține metadatele, personajele și toate scenele. Catalogul păstrează compatibilitate cu vechiul format împărțit în `scenes/`, dar poveștile v2 noi sunt salvate într-un singur fișier pentru copiere, audit și versionare mai simple.

## Metadatele episodului

`story.json` conține titlul, vârsta, obiectivele, personajele, `narrator_voice`, scena de început și lista `scenes`. Câmpul `voice` al fiecărui personaj indică un profil din `voices/voices.json`, nu un nume de voce OpenAI.

## Segment audio

```json
{
  "role": "tati",
  "text": "Sunt aici și te ajut.",
  "tts_text": "<|emotion:affection|><|prosody:speed_slow|>Sunt aici și te ajut.",
  "delivery": "cald și liniștitor",
  "pause_after_ms": 900
}
```

- `text`: text curat pentru interfață și subtitrare;
- `tts_text`: input complet pentru Higgs TTS 3;
- `delivery`: fallback semantic pentru alți furnizori și pentru drafturi;
- `pause_after_ms`: pauza tehnică după fișierul WAV.

`tts_text` este opțional în schemă pentru compatibilitate, dar validatorul proiectului îl cere tuturor episoadelor publicate.

## Scene și ramificații

- `story`: continuă prin `next_scene`;
- `choice`: minimum două opțiuni, fiecare cu `next_scene`;
- `ending`: nu poate continua.

Validatorul verifică rolurile, referințele, unicitatea ID-urilor și faptul că toate scenele sunt accesibile din `start_scene`.
