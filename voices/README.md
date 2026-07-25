# Mostre vocale pentru Higgs TTS 3

Fișierele audio nu se urcă în Git. Adaugă local, în acest director, mostre curate de 6-15 secunde. Fără muzică, ecou, zgomot sau mai multe persoane. Citește exact textul asociat; transcriptul este trimis modelului împreună cu înregistrarea.

## Fișiere necesare

### `narator.wav`

> Bun venit în lumea poveștilor. Vom porni încet, cu răbdare, curiozitate și multă grijă.

Voce adultă caldă, clară, liniștitoare.

### `alexandru.wav`

> Bună! Eu sunt Alexandru. Îmi plac mașinuțele, cursele și aventurile în care descoperim lucruri noi.

Recomandare: folosește o voce sintetică sau o voce interpretată de un adult. O înregistrare reală a copilului trebuie făcută numai cu acordul părintelui și păstrată strict local, niciodată în repo-ul public.

### `tati.wav`

> Sunt aici și te ajut. Ne oprim, ne uităm cu atenție și găsim împreună soluția potrivită.

Voce joasă, calmă, afectuoasă.

### `masinuta-energica.wav`

> Motoarele sunt pregătite, pista este liberă și aventura poate începe chiar acum!

Voce luminoasă și energică.

### `masinuta-jucausa.wav`

> Ce idee grozavă! Putem încerca, putem râde și putem învăța ceva nou împreună.

Voce mică, prietenoasă și amuzantă.

### `masinuta-grava.wav`

> Un plan bun începe cu o oprire scurtă, o verificare atentă și instrumentul potrivit.

Voce robustă pentru mecanici și personaje protectoare.

### `masinuta-luminoasa.wav`

> Lumina ne arată drumul, iar răbdarea ne ajută să alegem pasul potrivit.

Voce clară și ușor magică.

## Format recomandat

- WAV mono;
- 24 kHz sau 48 kHz;
- fără clipping;
- volum constant;
- început și sfârșit curate;
- un singur vorbitor;
- transcript identic cu ce se aude.

După adăugare:

```bash
python scripts/validate_stories.py
```

Cu `HIGGS_REQUIRE_REFERENCES=true`, randarea se oprește explicit dacă lipsește o mostră.
