# Povești pentru Alexandru

Studio local-first pentru scrierea, validarea, generarea audio și redarea poveștilor interactive. Alexandru este personajul principal, iar seria inițială folosește mașinuțe, dialog, alegeri și lecții blânde.

## Ce conține

- bibliotecă web și player interactiv cu ramificații;
- format solid de poveste: scene, segmente, roluri, pauze și alegeri;
- voci diferite pe personaje;
- TTS OpenAI (`gpt-4o-mini-tts`), TTS local OpenAI-compatible sau mod mock;
- generator de povești prin OpenAI ori LLM local compatibil;
- cache audio pe segment: regenerezi doar replica modificată;
- 8 episoade complete și un backlog cu 20 de idei;
- Docker, validare automată și teste.

## Instalare rapidă

```bash
cp .env.example .env
docker compose up -d --build
```

Deschide `http://127.0.0.1:8090`. Pentru acces din rețea modifică bindingul Docker sau publică aplicația prin Tailscale/Authentik. Implicit nu este expusă extern.

### Instalare fără Docker

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
.venv/bin/python -m app.main
```

## Test fără cost

Configurația implicită folosește `TTS_PROVIDER=mock`. Apasă „Generează audio”: aplicația creează fișiere WAV silențioase și verifică întregul player, scenele și alegerile.

## OpenAI TTS

```env
TTS_PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_TTS_MODEL=gpt-4o-mini-tts
```

Cheia rămâne pe server. Aplicația trimite separat fiecare replică, împreună cu vocea personajului, indicațiile scenei și pauzele. Modelul OpenAI acceptă maximum 4096 de caractere per cerere; schema validează această limită.

## TTS local pe PC-ul de gaming

```env
TTS_PROVIDER=openai-compatible
LOCAL_TTS_BASE_URL=http://IP-TAILSCALE-PC:8000/v1
LOCAL_TTS_MODEL=modelul-tau
```

Motorul local trebuie să expună `POST /audio/speech` și să returneze WAV. Poate folosi XTTS, Piper, Kokoro sau alt motor; aplicația rămâne neschimbată. Fiecare rol poate avea altă voce.

## Generare de povești noi

Generatorul este dezactivat implicit. Pentru OpenAI:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=...
STORY_LLM_MODEL=gpt-5-mini
```

Pentru un server local OpenAI-compatible:

```env
LLM_PROVIDER=openai-compatible
LLM_BASE_URL=http://IP-TAILSCALE-PC:8000/v1
LLM_API_KEY=
STORY_LLM_MODEL=model-local
```

Drafturile sunt validate înainte de salvare. Un adult trebuie să le citească înainte de redare.

## Comenzi

```bash
python scripts/validate_stories.py
python scripts/render_story.py alexandru-marele-garaj-fermecat
pytest -q
```

Documentație: [formatul poveștilor](docs/STORY_FORMAT.md), [furnizori TTS](docs/TTS_PROVIDERS.md), [episoade viitoare](docs/EPISODE_BACKLOG.md).
