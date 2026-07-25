# Povești pentru Alexandru

Studio local-first pentru povești audio interactive în limba română. Alexandru este personajul principal, iar fiecare episod este pregătit pentru **Higgs TTS 3** cu dialog pe mai multe voci, emoții, șoapte, pauze, ritm și efecte discrete.

## Ce conține

- bibliotecă web și player cu alegeri și ramificații;
- 8 episoade complete, 69 de scene și 415 replici regizate;
- câmp separat `text` pentru interfață și `tts_text` gata de trimis la Higgs;
- gramatică Higgs strictă: comenzi globale canonice, pauze/SFX poziționale și eliminarea comenzilor contradictorii;
- câte o referință vocală pentru narator, Alexandru, Tati și patru tipuri de mașinuțe;
- generare separată pe replică, cache și redare continuă cu pauze exacte;
- adaptor nativ pentru SGLang-Omni/vLLM-Omni `/v1/audio/speech`;
- preview al payloadului și audit editorial fără apelarea modelului;
- OpenAI TTS și alte servere OpenAI-compatible păstrate ca alternative;
- Docker, validare automată și teste.

## Instalare pe server

```bash
cp .env.example .env
docker compose up -d --build
```

Deschide `http://127.0.0.1:8090`. Pentru acces prin Tailscale sau proxy, modifică bindingul portului după arhitectura ta.

## Test fără model sau cost

Implicit aplicația folosește:

```env
TTS_PROVIDER=mock
```

Aceasta creează WAV-uri silențioase și verifică integral playerul, ramificațiile, cache-ul și pauzele.

## Activare Higgs TTS 3

1. Pornește modelul pe PC-ul de gaming și expune endpointul `/v1/audio/speech` prin Tailscale.
2. Înregistrează sau generează cele 7 mostre vocale descrise în [`voices/README.md`](voices/README.md).
3. Configurează serverul aplicației:

```env
TTS_PROVIDER=higgs
HIGGS_BASE_URL=http://IP-TAILSCALE-PC:8000/v1
HIGGS_MODEL=bosonai/higgs-tts-3-4b
HIGGS_API_VOICE=default
HIGGS_REQUIRE_REFERENCES=true
```

Profilurile locale aleg mostra vocală, iar requestul oficial este trimis cu `voice=default`. Aplicația transmite fiecare replică separat, împreună cu `tts_text`, mostra personajului și transcriptul exact. Mostra este transmisă ca data URL, deci PC-ul de gaming nu are nevoie de acces la discul serverului.

## Episoade

1. **Alexandru și Marele Garaj Fermecat** — grijă față de mașinuțe.
2. **Cursa Pieselor Pierdute** — ordine și căutare cu un plan.
3. **Podul Culorilor** — culori, semnale și răbdare.
4. **Mașinuța care nu voia să împartă** — rând, limite și cooperare.
5. **Noaptea Farurilor Curajoase** — teamă, respirație și ajutor.
6. **Misiunea Pompierilor de Jucărie** — calm și siguranță.
7. **Cursa fără Grabă** — frustrare, verificare și perseverență.
8. **Atelierul Reparațiilor** — diagnostic, sortare și reparație atentă.

## Generare de povești noi

Generatorul LLM produce direct schema v2: text curat, `tts_text` Higgs, roluri vocale, pauze și ramificații. Promptul impune maximum o comandă din fiecare grupă, segmente scurte și folosirea rară a efectelor. Drafturile sunt validate înainte de salvare, dar trebuie revizuite de un adult înainte de redare.

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=...
STORY_LLM_MODEL=gpt-5-mini
```

Poți folosi și un LLM local OpenAI-compatible.

## Validare și preview

```bash
# Toate poveștile și comenzile Higgs
python scripts/validate_stories.py

# Avertismentele editoriale devin erori
python scripts/validate_stories.py --strict-quality

# Verifică mostrele vocale locale
python scripts/validate_stories.py --check-audio

# Arată requestul exact fără a genera audio
python scripts/preview_higgs_payload.py \
  alexandru-marele-garaj-fermecat \
  --scene covorul --segment 1

pytest -q
```

## Confidențialitate și licență

- Nu urca mostrele vocale în Git; repo-ul este public, iar fișierele audio din `voices/` sunt ignorate.
- Folosește numai voci proprii, sintetice sau înregistrate cu acord explicit. Pentru vocea unui copil, păstrează fișierul exclusiv local.
- Modelul Higgs TTS 3 are propria licență Boson. Acest repo nu distribuie modelul sau greutățile. Verifică [`docs/HIGGS_TTS_3.md`](docs/HIGGS_TTS_3.md) înainte de publicare ori utilizare comercială.

Documentație: [Higgs TTS 3](docs/HIGGS_TTS_3.md), [format povești](docs/STORY_FORMAT.md), [furnizori TTS](docs/TTS_PROVIDERS.md).
