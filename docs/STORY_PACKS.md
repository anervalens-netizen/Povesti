# Story packs

Catalogul acceptă și fișiere `*.jsonl.gz.b64` pentru serii mari.

Formatul conține:

1. câte un obiect `Story` complet pe fiecare linie JSONL;
2. compresie gzip;
3. codificare Base64 pentru stocare text în Git.

La pornire, catalogul decodează, decomprimă și validează individual fiecare poveste. Un pack invalid, gol sau cu o linie JSON invalidă blochează pornirea și validarea CI.

Acest format este folosit numai când mai multe episoade au structură similară și ar produce o cantitate mare de text repetitiv. API-ul, playerul și motorul TTS primesc aceleași obiecte `Story` ca în cazul fișierelor JSON individuale.
