# Formatul poveștilor

Fiecare poveste are propriul director:

```text
stories/<story-id>/
├── story.json
└── scenes/
    ├── 01-introducere.json
    ├── 02-alegere.json
    └── 03-final.json
```

`story.json` conține metadatele, personajele și profilurile vocale. Fiecare scenă este separată, ca să poată fi rescrisă, revizuită sau regenerată fără modificarea întregului episod.

- `characters`: profilurile de voce ale personajelor.
- `segments`: bucățile rostite separat. Fiecare are rol, indicație de interpretare și pauză.
- `choices`: alegeri care trimit către alte scene.
- `next_scene`: continuarea liniară.
- `kind: ending`: final fără continuare.

Separarea pe segmente permite mai multe voci și regenerarea unei singure replici fără refacerea întregii povești. Playerul redă segmentele în ordine și aplică `pause_after_ms` între ele.

## Reguli editoriale

1. Alexandru rezolvă probleme prin curiozitate, cooperare și grijă.
2. Lecțiile apar natural; nu folosim frică, rușinare sau pedepse.
3. Alegerile sunt sigure și duc la progres, inclusiv când alegerea inițială nu este optimă.
4. Frazele sunt scurte și clare pentru 2–6 ani.
5. Fiecare poveste se termină calm și reconfortant.
