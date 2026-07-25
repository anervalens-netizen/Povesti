# Higgs TTS 3 — ghid de integrare și regie

Aplicația folosește modelul `bosonai/higgs-tts-3-4b` prin endpointul OpenAI-compatible `/v1/audio/speech`. Modelul generează audio la 24 kHz, suportă româna, clonare vocală zero-shot și comenzi inline pentru emoție, stil, prosodie, pauze și efecte.

## Arhitectură

```text
Povești server → Tailscale → PC gaming /v1/audio/speech → WAV → cache server
```

Fiecare segment reprezintă un singur vorbitor și un singur turn TTS. Este randat separat, cu propria mostră vocală, apoi playerul introduce pauza `pause_after_ms` și continuă povestea. Avantaje:

- identitate vocală stabilă pentru fiecare personaj;
- regenerare doar pentru replica modificată;
- ramificații interactive fără fișiere audio monolitice;
- control separat pentru pauzele din replică și cele dintre replici.

## Configurare

```env
TTS_PROVIDER=higgs
HIGGS_BASE_URL=http://IP-TAILSCALE-PC:8000/v1
HIGGS_MODEL=bosonai/higgs-tts-3-4b
HIGGS_API_VOICE=
HIGGS_USE_PROFILE_VOICE=false
HIGGS_RESPONSE_FORMAT=wav
HIGGS_TEMPERATURE=0.8
HIGGS_TOP_P=
HIGGS_TOP_K=50
HIGGS_MAX_NEW_TOKENS=2048
HIGGS_SEED=
HIGGS_REQUIRE_REFERENCES=true
```

`HIGGS_API_VOICE` rămâne gol pentru Higgs TTS 3, care nu are voci presetate.
Numele locale precum `tati` sau `masinuta-jucausa` aleg mostra din
`voices/voices.json`. Dacă un server compatibil expune explicit voci denumite,
variabila poate fi completată. Identitatea personajului vine din `references`.

Pe serverele cu registru de voci încărcate, `HIGGS_USE_PROFILE_VOICE=true`
trimite numele profilului local în câmpul `voice` și nu mai retransmite
referința la fiecare replică. Fișierele locale rămân sursa profilurilor și intră
în amprenta cache.

## Payloadul transmis

```json
{
  "model": "bosonai/higgs-tts-3-4b",
  "input": "<|emotion:affection|><|prosody:speed_slow|>Sunt aici și te ajut.",
  "response_format": "wav",
  "temperature": 0.8,
  "top_k": 50,
  "max_new_tokens": 2048,
  "references": [
    {
      "audio_path": "data:audio/wav;base64,...",
      "text": "Sunt aici și te ajut. Ne oprim, ne uităm cu atenție și găsim împreună soluția potrivită."
    }
  ]
}
```

SGLang-Omni acceptă în `audio_path` cale locală, URL de fișier, URL HTTP sau data URL. Aplicația folosește data URL, astfel încât PC-ul de gaming nu are nevoie de acces la discul serverului. Transcriptul trebuie să fie identic cu înregistrarea; documentația oficială precizează că acesta îmbunătățește fidelitatea clonării.

## Regula principală: două tipuri de comenzi

### 1. Comenzi globale — numai la început

Acestea controlează întregul turn și formează un prefix continuu înaintea primului cuvânt:

```text
emotion → style → speed → pitch → expressive
```

Exemplu:

```text
<|emotion:awe|><|style:whispering|><|prosody:speed_slow|><|prosody:pitch_high|><|prosody:expressive_high|>Uite lumina de sub ușă.
```

Se folosește maximum o valoare din fiecare grupă. Sunt invalide combinațiile contradictorii:

```text
<|prosody:speed_slow|><|prosody:speed_fast|>...
<|prosody:pitch_low|><|prosody:pitch_high|>...
<|emotion:fear|><|emotion:elation|>...
```

Comenzile explicite ale replicii au prioritate față de prefixul profilului vocal. Astfel, o replică ce cere `pitch_low` nu va primi simultan și `pitch_high` din vocea implicită.

### 2. Comenzi poziționale — exact unde se aud

Pauzele se pun după cuvinte rostite:

```text
Alexandru deschise ușa <|prosody:pause|> și privi înăuntru.
Pentru o clipă, totul rămase tăcut <|prosody:long_pause|> apoi apăru o lumină.
```

Nu se pune pauză la începutul replicii. Pauzele aproximative ale modelului sunt:

- `pause`: aproximativ 400–700 ms;
- `long_pause`: aproximativ 700–1500 ms.

Pauza dintre două fișiere este controlată separat prin `pause_after_ms`.

## Emoții

Catalogul oficial are 21 de emoții. Pentru poveștile copilului sunt recomandate în principal:

- `affection` — căldură și afecțiune;
- `amusement` — joacă și umor;
- `enthusiasm` — energie și aventură;
- `determination` — fermitate calmă;
- `pride` — încredere după o reușită;
- `contentment` — liniște și mulțumire;
- `relief` — ușurare;
- `contemplation` — gândire;
- `confusion` — nedumerire;
- `surprise` — surpriză;
- `awe` — uimire;
- `fear` și `sadness` — numai moderat, fără a speria;
- `anger` — scurt și controlat, fără agresivitate.

Nu se folosește `arousal` în conținut pentru copii. Emoția nu este obligatorie în fiecare replică; vocea de referință și punctuația trebuie lăsate să facă o parte din interpretare.

## Stil și prosodie

Stiluri:

```text
<|style:whispering|>
<|style:shouting|>
<|style:singing|>
```

`shouting` se folosește rar, de exemplu pentru un „Stop!” de siguranță, nu pentru dialog obișnuit.

Viteză:

```text
speed_very_slow ≈ 0.65×
speed_slow      ≈ 0.85×
speed_fast      ≈ 1.2×
speed_very_fast ≈ 1.4×
```

Pitch:

```text
pitch_low  ≈ −3 semitonuri
pitch_high ≈ +2,5 semitonuri
```

Expresivitate:

```text
expressive_high
expressive_low
```

Pentru o rostire foarte lentă, documentația recomandă și pauze între fraze; `speed_very_slow` singur nu prelungește nelimitat replica.

## Efecte sonore

Efectul este urmat imediat de indiciul fonetic, fără spațiu:

```text
<|sfx:laughter|>Hehe, aproape m-ai prins!
<|sfx:sigh|>Ahh, acum sunt mai liniștit.
<|sfx:humming|>Hmm, unde poate fi piesa?
<|sfx:sneeze|>Hapciu! Scuză-mă.
```

Sunt recunoscute numai:

```text
cough, laughter, crying, screaming, burping, humming, sigh, sniff, sneeze
```

Efectele se folosesc rar. Regula editorială a proiectului este maximum un SFX într-un segment obișnuit.

## Dimensiunea segmentelor

Pentru stabilitate și dialog natural:

- un singur vorbitor per segment;
- de regulă 1–3 propoziții;
- țintă sub aproximativ 80 de cuvinte;
- o intenție emoțională dominantă;
- pasajele lungi se împart în segmente consecutive.

Modelul are context de 8192 tokeni, dar segmentele scurte sunt mai ușor de regenerat, păstrează vocea stabilă și permit control mai precis.

## Mostre vocale

`voices/voices.json` definește profilurile locale. Fiecare profil conține:

- fișierul audio;
- transcriptul exact;
- prefixul vocal implicit;
- descrierea rolului.

Recomandările proiectului:

- WAV mono, PCM 16-bit;
- 24 kHz sau 48 kHz;
- 6–15 secunde;
- un singur vorbitor;
- fără muzică, ecou sau zgomot;
- volum constant și fără clipping.

## Comenzi de verificare

Validare structurală și auditarea tuturor replicilor:

```bash
python scripts/validate_stories.py
```

Transformarea avertismentelor editoriale în erori:

```bash
python scripts/validate_stories.py --strict-quality
```

Verificarea mostrelor existente:

```bash
python scripts/validate_stories.py --check-audio
```

Blocarea dacă lipsește vreo mostră:

```bash
python scripts/validate_stories.py --require-audio
```

Preview pentru inputul și payloadul exact, fără apelarea modelului:

```bash
python scripts/preview_higgs_payload.py \
  alexandru-marele-garaj-fermecat \
  --scene covorul \
  --segment 1
```

## Pornirea modelului

Fluxul oficial SGLang-Omni:

```bash
hf download bosonai/higgs-tts-3-4b

sgl-omni serve \
  --model-path bosonai/higgs-tts-3-4b \
  --port 8000
```

Modelul poate fi servit și prin vLLM-Omni, care expune același endpoint. Quickstart-urile oficiale sunt orientate spre CUDA/NVIDIA. Pentru AMD RX 9070 XT trebuie verificat separat un stack ROCm compatibil; formatul poveștilor și API-ul aplicației nu depind de backendul GPU.

## Licență

Modelul este publicat sub Boson Higgs TTS 3 Research and Non-Commercial License. Model cardul include un Creator Use Grant pentru conținut precum audiobook-uri, cu atribuire vizibilă. Găzduirea ca serviciu, integrarea într-un produs sau alte utilizări comerciale pot necesita licență separată.

Credit sugerat:

```text
This audio was created with Boson AI's Higgs Audio — https://www.boson.ai/higgs-audio
```
