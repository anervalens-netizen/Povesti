# Furnizori TTS

## Mock
`TTS_PROVIDER=mock` produce fișiere WAV silențioase. Verifică fluxul fără cost.

## OpenAI
Setează `TTS_PROVIDER=openai` și `OPENAI_API_KEY`. Model implicit: `gpt-4o-mini-tts`. Fiecare segment este trimis separat, cu vocea și instrucțiunile rolului. Cheia rămâne doar pe server.

## Local / OpenAI-compatible
Setează `TTS_PROVIDER=openai-compatible` și `LOCAL_TTS_BASE_URL`, de exemplu un endpoint de pe PC-ul de gaming accesibil prin Tailscale. Endpointul trebuie să accepte `POST /audio/speech` și să returneze WAV.

Pentru XTTS, Piper, Kokoro sau alt motor fără API compatibil, recomandarea este un adaptor mic pe PC-ul de gaming care expune acest contract. Aplicația nu depinde astfel de un motor anume.

## Mai multe voci
Fiecare personaj are `voice`. Motorul audio generează separat fiecare segment, deci poate folosi voci complet diferite. Schimbarea furnizorului nu modifică poveștile.
