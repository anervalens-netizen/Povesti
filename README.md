# Povești pentru Alexandru

Studio local-first pentru povești audio interactive în limba română. Alexandru este personajul principal, iar fiecare episod este pregătit pentru **Higgs TTS 3** cu dialog pe mai multe voci, emoții, pauze, ritm și alegeri interactive.

## Ce conține

- bibliotecă web grupată pe serii;
- **28 de episoade complete, 229 de scene și 1.435 de replici regizate**;
- trei serii: **Marele Garaj Fermecat**, **Clubul Micilor Exploratori** și **Atelierul Micilor Inventatori**;
- câmp separat `text` pentru interfață și `tts_text` gata de trimis la Higgs;
- gramatică Higgs strictă și eliminarea comenzilor contradictorii;
- referințe vocale reutilizate pentru narator, Alexandru, Tati și personaje;
- generare separată pe replică, cache și redare continuă;
- adaptor nativ pentru `/v1/audio/speech`;
- preview al payloadului și audit editorial;
- Docker, validare automată și teste.

## Instalare pe server

```bash
cp .env.example .env
docker compose up -d --build
```

Deschide `http://127.0.0.1:8090`.

Pe serverul principal:

```bash
docker compose -f docker-compose.yml -f deploy/docker-compose.primary.yml up -d --build
```

## Activare Higgs TTS 3

```env
TTS_PROVIDER=higgs
HIGGS_BASE_URL=http://IP-TAILSCALE-PC:8000/v1
HIGGS_MODEL=bosonai/higgs-tts-3-4b
HIGGS_API_VOICE=
HIGGS_USE_PROFILE_VOICE=false
HIGGS_REQUIRE_REFERENCES=true
```

Profilurile locale aleg mostra vocală. Aplicația transmite fiecare replică separat, cu `tts_text`, mostra personajului și transcriptul exact.

## Serii

### Marele Garaj Fermecat — 8 episoade

1. **Alexandru și Marele Garaj Fermecat** — grijă față de mașinuțe.
2. **Cursa Pieselor Pierdute** — ordine și căutare cu un plan.
3. **Podul Culorilor** — culori, semnale și răbdare.
4. **Mașinuța care nu voia să împartă** — rând și cooperare.
5. **Noaptea Farurilor Curajoase** — teamă și ajutor.
6. **Misiunea Pompierilor de Jucărie** — calm și siguranță.
7. **Cursa fără Grabă** — frustrare și perseverență.
8. **Atelierul Reparațiilor** — diagnostic și reparație atentă.

### Clubul Micilor Exploratori — 10 episoade

1. **Alexandru și Harta care se Schimbă** — observație și orientare.
2. **Alexandru și Podul Frunzelor** — construcție și cooperare.
3. **Alexandru și Puiul de Nor Rătăcit** — teamă și cererea de ajutor.
4. **Alexandru și Biblioteca Șoaptelor** — ascultare și autocontrol.
5. **Alexandru și Izvorul cu Trei Sunete** — memorie și secvențe.
6. **Alexandru și Grădina care Uitase Culorile** — natură și îngrijire.
7. **Alexandru și Steaua Coborâtă în Iarbă** — curaj și siguranță.
8. **Alexandru și Ceasul Anotimpurilor** — schimbare și rutină.
9. **Alexandru și Festivalul Prieteniei** — incluziune și negociere.
10. **Alexandru și Muntele Pașilor Mici** — perseverență și progres.

### Atelierul Micilor Inventatori — 10 episoade

1. **Alexandru și Robotul care Încurca Pașii** — secvențe și instrucțiuni clare.
2. **Alexandru și Turnul care Voia să Atingă Norii** — stabilitate și baze solide.
3. **Alexandru și Podul Formelor Potrivite** — forme și funcții.
4. **Alexandru și Cutia cu O Mie de Piese** — clasificare și organizare.
5. **Alexandru și Beculețul care se Temuse de Întuneric** — diagnostic și siguranță.
6. **Alexandru și Fabrica Sunetelor** — ascultare și controlul zgomotului.
7. **Alexandru și Ceasul care Voia Totul Acum** — răbdare și timp.
8. **Alexandru și Invenția care Nu Ieșea** — experiment și perseverență.
9. **Alexandru și Invenția lui Bip** — feedback blând și încredere.
10. **Alexandru și Marea Expoziție a Inventatorilor** — cooperare și resurse.

## Validare

```bash
python scripts/validate_stories.py --strict-quality
python scripts/validate_stories.py --check-audio
python scripts/preview_higgs_payload.py \
  atelierul-inventatorilor-robotul-pasilor \
  --scene start --segment 1
pytest -q
```

## Confidențialitate și licență

- Nu urca mostrele vocale în Git.
- Folosește numai voci proprii, sintetice sau înregistrate cu acord explicit.
- Modelul Higgs TTS 3 are propria licență Boson; repo-ul nu distribuie modelul sau greutățile.

Documentație: [Higgs TTS 3](docs/HIGGS_TTS_3.md), [format povești](docs/STORY_FORMAT.md), [story packs](docs/STORY_PACKS.md), [furnizori TTS](docs/TTS_PROVIDERS.md).
