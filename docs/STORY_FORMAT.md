# Formatul poveștilor — schema v2

Fiecare episod este păstrat într-un fișier ușor de revizuit:

```text
stories/<id>/story.json
```

Catalogul păstrează compatibilitate cu formatul mai vechi împărțit în `scenes/`.

## Metadate și voci

`story.json` conține titlul, vârsta, obiectivele, personajele, `narrator_voice`, scena de început și lista `scenes`. Câmpul `voice` indică un profil local din `voices/voices.json`, folosit pentru selectarea mostrei vocale. Requestul SGLang este trimis implicit cu `voice=default`.

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
- `tts_text`: input canonic trimis către Higgs TTS 3;
- `delivery`: fallback semantic pentru drafturi și alți furnizori;
- `pause_after_ms`: pauza tehnică după fișierul WAV.

`tts_text` este opțional în schema generală, dar validatorul proiectului îl cere tuturor episoadelor publicate.

## Reguli de regie Higgs

Un segment este un singur turn și un singur vorbitor. Ținta editorială este 1–3 propoziții și sub aproximativ 80 de cuvinte.

Comenzile globale formează un prefix continuu la început, în ordinea:

```text
emotion → style → speed → pitch → expressive
```

Se acceptă maximum o valoare din fiecare grupă. Comenzile explicite din `tts_text` înlocuiesc valoarea implicită din profilul vocal pentru aceeași grupă.

Pauzele sunt poziționale:

```text
Privi înăuntru <|prosody:pause|> și zâmbi.
```

SFX-ul este urmat imediat de onomatopee:

```text
<|sfx:laughter|>Hehe, aproape m-ai prins!
```

Detaliile și catalogul complet sunt în [`HIGGS_TTS_3.md`](HIGGS_TTS_3.md).

## Scene și ramificații

- `story`: continuă prin `next_scene`;
- `choice`: minimum două opțiuni și fără `next_scene` liniar;
- `ending`: nu poate continua.

Validatorul verifică rolurile, comenzile Higgs, referințele, unicitatea ID-urilor și accesibilitatea tuturor scenelor.

## Verificare

```bash
python scripts/validate_stories.py
python scripts/validate_stories.py --strict-quality
python scripts/preview_higgs_payload.py <story-id> --scene <scene-id> --segment 1
```
