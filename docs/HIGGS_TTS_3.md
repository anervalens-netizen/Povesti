# Integrarea Higgs TTS 3

## Arhitectură

Aplicația rulează pe serverul casei. Higgs TTS 3 rulează separat pe PC-ul cu GPU și expune API-ul OpenAI-compatible:

```text
Povești server → Tailscale → PC gaming /v1/audio/speech → WAV → cache server
```

Fiecare replică este randată separat. Astfel:

- fiecare personaj primește propria referință vocală;
- o replică modificată se regenerează fără restul episodului;
- pauzele dintre replici sunt controlate de player;
- alegerile interactive nu necesită generarea unor piste audio monolitice.

## Pornirea oficială prin SGLang-Omni

Documentația modelului indică fluxul:

```bash
docker pull lmsysorg/sglang-omni:dev

docker run -it --gpus all --shm-size 32g --ipc host \
  --network host --privileged lmsysorg/sglang-omni:dev /bin/zsh

git clone https://github.com/sgl-project/sglang-omni.git
cd sglang-omni
uv venv .venv -p 3.12
source .venv/bin/activate
uv pip install -v -e .

export HF_TOKEN=hf_...
hf download bosonai/higgs-tts-3-4b

sgl-omni serve \
  --model-path bosonai/higgs-tts-3-4b \
  --port 8000
```

Alternativ, model cardul documentează și vLLM-Omni cu același endpoint.

### Atenție pentru AMD RX 9070 XT

Quickstart-ul oficial de mai sus este construit în jurul CUDA/NVIDIA. Compatibilitatea SGLang-Omni sau vLLM-Omni cu un GPU consumer AMD RDNA4 nu este garantată de această aplicație. Integrarea API este completă, dar pornirea modelului pe RX 9070 XT trebuie verificată separat într-un stack ROCm compatibil. Nu modifica poveștile pentru această verificare: orice server care respectă endpointul descris mai jos va funcționa cu aplicația.

## Configurarea aplicației

```env
TTS_PROVIDER=higgs
HIGGS_BASE_URL=http://IP-TAILSCALE-PC:8000/v1
HIGGS_MODEL=bosonai/higgs-tts-3-4b
HIGGS_TEMPERATURE=0.8
HIGGS_TOP_K=50
HIGGS_MAX_NEW_TOKENS=2048
HIGGS_REQUIRE_REFERENCES=true
```

`HIGGS_SEED` poate fi setat pentru rezultate mai reproductibile. Lăsat gol, modelul păstrează mai multă variație expresivă.

## Cererea transmisă

```json
{
  "model": "bosonai/higgs-tts-3-4b",
  "voice": "tati",
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

Transcriptul mostrei trebuie să corespundă exact înregistrării. Acesta îmbunătățește fidelitatea clonării.

## Tagurile folosite

Toate folosesc forma `<|category:value|>`.

- emoție: `affection`, `amusement`, `enthusiasm`, `determination`, `contentment`, `relief`, `contemplation`, `confusion`, `surprise`, `awe`, `fear`, `sadness`, `anger` etc.;
- stil: `whispering`, `shouting`, `singing`;
- prosodie la început: `speed_slow`, `speed_fast`, `pitch_low`, `pitch_high`, `expressive_high` etc.;
- prosodie inline: `pause`, `long_pause`;
- efecte inline: `laughter`, `sigh`, `humming` etc.

Reguli aplicate automat:

1. emoția, stilul, viteza, pitch-ul și expresivitatea apar la începutul replicii;
2. pauzele apar exact în locul în care trebuie produse;
3. un SFX este urmat imediat de onomatopee, de exemplu `<|sfx:laughter|>Hehe`;
4. tagurile necunoscute blochează validarea înainte de randare.

## Multiple voci

`voices/voices.json` definește șapte profiluri. Fiecare profil indică:

- numele fișierului de referință;
- transcriptul exact;
- tagurile de bază pentru pitch, viteză și expresivitate;
- rolul recomandat.

Nu este folosit un singur prompt cu mai mulți vorbitori. Aplicația face câte o cerere pentru fiecare replică și concatenează redarea în player. Aceasta păstrează identitatea vocală mai stabilă și permite cache independent.

## Licență

Higgs TTS 3 este publicat sub Boson Higgs TTS 3 Research and Non-Commercial License. Model cardul descrie și un Creator Use Grant pentru conținut precum audiobook-uri, cu atribuire vizibilă către Boson AI. Găzduirea modelului ca serviciu, integrarea lui într-un produs sau alte utilizări comerciale pot necesita o licență separată. Verifică termenii oficiali înainte de distribuție.

Credit sugerat de model card:

```text
This audio was created with Boson AI's Higgs Audio — https://www.boson.ai/higgs-audio
```
