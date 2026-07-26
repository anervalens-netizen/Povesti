# Clubul Micilor Exploratori

A doua serie din aplicație conține 10 aventuri interactive despre natură, observație, emoții, cooperare și perseverență.

## Echipa

- Alexandru — personaj principal și liderul misiunilor;
- Tati — ghid calm și afectuos;
- Luna — bufniță atentă și înțeleaptă;
- Puf — arici curios și glumeț;
- Bruno — urs protector și metodic;
- Zizi — veveriță energică și inventivă.

Personajele reutilizează profilurile vocale Higgs deja existente. Nu sunt necesare mostre vocale suplimentare.

## Episoade

1. Harta care se Schimbă — observație și orientare;
2. Podul Frunzelor — construcție și cooperare;
3. Puiul de Nor Rătăcit — teamă și cererea de ajutor;
4. Biblioteca Șoaptelor — ascultare și autocontrol;
5. Izvorul cu Trei Sunete — memorie și secvențe;
6. Grădina care Uitase Culorile — natură și îngrijire;
7. Steaua Coborâtă în Iarbă — curaj și siguranță;
8. Ceasul Anotimpurilor — schimbare și rutină;
9. Festivalul Prieteniei — incluziune și negociere;
10. Muntele Pașilor Mici — perseverență și progres.

Fiecare episod are opt scene, o alegere cu două ramificații, un final liniștitor și câmpuri `tts_text` validate pentru Higgs TTS 3.

## Stocare

Primele două episoade sunt fișiere JSON individuale. Celelalte opt sunt păstrate într-un story pack JSONL comprimat pentru a reduce duplicarea structurală. Catalogul îl încarcă transparent și validează fiecare episod ca obiect `Story` independent.
