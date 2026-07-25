# Furnizori TTS

## `higgs` — recomandat

Adaptor nativ pentru Higgs TTS 3 prin SGLang-Omni sau vLLM-Omni. Folosește `tts_text`, tagurile oficiale și mostre vocale multiple.

```env
TTS_PROVIDER=higgs
HIGGS_BASE_URL=http://IP-TAILSCALE-PC:8000/v1
HIGGS_REQUIRE_REFERENCES=true
```

Dacă cele șapte mostre au fost încărcate în registrul serverului
cu aceleași nume ca profilurile locale, setează
`HIGGS_USE_PROFILE_VOICE=true`. Requestul trimite atunci direct numele
profilului și evită retransmiterea mostrei la fiecare replică.

## `mock`

Generează WAV silențios pentru testarea playerului fără GPU sau cost.

## `openai`

Folosește `gpt-4o-mini-tts`. Citește câmpul curat `text`; instrucțiunile sunt compuse din metadatele scenei și personajului.

## `openai-compatible`

Adaptor generic pentru un motor care implementează `/v1/audio/speech`. Nu presupune suport pentru tagurile Higgs.

## Cache

Cheia cache include furnizorul, textul efectiv trimis, instrucțiunile și amprenta mostrei vocale. Schimbarea unei înregistrări din `voices/` regenerează automat numai replicile rolurilor afectate.
