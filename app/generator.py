from __future__ import annotations

import json
import re

import httpx

from .config import Settings
from .schemas import GenerationRequest, Story

VOICE_PROFILES = (
    "alexandru, tati, masinuta-energica, masinuta-jucausa, "
    "masinuta-grava, masinuta-luminoasa"
)
HIGGS_TAGS = """
Reguli canonice Higgs TTS 3:
- Sintaxa este exact <|category:value|>; nu inventa taguri.
- Comenzile globale formează un prefix continuu, înaintea primului cuvânt, în ordinea:
  emotion, style, speed, pitch, expressive.
- Folosește maximum o comandă din fiecare grupă. Nu combina speed_slow cu speed_fast,
  pitch_low cu pitch_high sau expressive_low cu expressive_high.
- Emotion permise și potrivite poveștilor: elation, amusement, enthusiasm,
  determination, pride, contentment, affection, relief, contemplation, confusion,
  surprise, awe, longing, anger, fear, sadness.
- Style: singing, shouting, whispering. Folosește shouting foarte rar și fără a speria.
- Prosody globală: speed_very_slow, speed_slow, speed_fast, speed_very_fast,
  pitch_low, pitch_high, expressive_high, expressive_low.
- Prosody pozițională: pause și long_pause. Se pune numai după cuvinte rostite,
  exact unde se aude pauza, niciodată la începutul replicii.
- SFX: cough, laughter, crying, screaming, burping, humming, sigh, sniff, sneeze.
  Tagul se pune chiar înaintea sunetului, urmat imediat de onomatopee fără spațiu:
  <|sfx:laughter|>Hehe, <|sfx:sigh|>Ahh, <|sfx:humming|>Hmm.
- Maximum un SFX pe replică și numai când aduce valoare; nu transforma povestea
  într-o succesiune de efecte.
- Tagurile globale controlează întregul turn trimis modelului. Alege o singură
  intenție dominantă pentru fiecare segment.
"""

SYSTEM = f"""Ești autor și regizor de povești audio interactive pentru copii de 2-6 ani.
Scrii exclusiv în română naturală, blândă, clară și potrivită rostirii.
Copilul Alexandru este personajul principal. Lecția este transmisă prin
consecințe blânde, fără rușinare, amenințări sau moralizare apăsată. Include
dialog interesant, umor de familie, repetiții participative, alegeri reale și
un final liniștitor.

Unitatea de generare audio este segmentul: un singur vorbitor, un singur turn,
de regulă 1-3 propoziții și maximum aproximativ 80 de cuvinte. Împarte pasajele
lungi în mai multe segmente pentru stabilitate vocală și expresivitate.

Fiecare segment trebuie să aibă:
- text: varianta curată, afișată în interfață;
- tts_text: aceleași cuvinte rostite, pregătite pentru Higgs TTS 3; diferențele
  sunt doar tagurile și eventual onomatopeea vizibilă și în text;
- delivery: descriere umană scurtă, utilă ca fallback;
- pause_after_ms: pauza tehnică dintre fișiere, de obicei 650-1200 ms; după o
  întrebare interactivă poate fi 1500-2200 ms.

Nu pune taguri în fiecare replică. O referință vocală bună și punctuația duc
mare parte din interpretare; folosește comenzile numai când schimbă clar
emoția, stilul sau ritmul. Nu folosi emotion:arousal în povești pentru copii.

Folosește narrator_voice=narator. Pentru personaje folosește exclusiv aceste
profiluri vocale: {VOICE_PROFILES}. Nu include narrator în characters.
{HIGGS_TAGS}

Exemple corecte:
- <|emotion:awe|><|prosody:speed_slow|>Alexandru privi lumina <|prosody:pause|> și zâmbi.
- <|emotion:amusement|><|sfx:laughter|>Hehe, Tati, aproape m-ai prins!
- <|emotion:affection|><|prosody:expressive_low|>Sunt aici. Rezolvăm împreună.

Returnează NUMAI JSON valid conform structurii cerute."""


class StoryGenerator:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _prompt(self, req: GenerationRequest) -> str:
        schema = Story.model_json_schema()
        return f"""{SYSTEM}
Idee: {req.title_idea}
Lecție: {req.lesson}
Elemente preferate: {req.favorite_elements}
Vârstă: {req.age} ani
Durată: aproximativ {req.estimated_minutes} minute
Număr de momente interactive: {req.choices}
Setează schema_version la 2 și episode la 999 pentru draft.
Fiecare segment are maximum 700 caractere în tts_text și maximum aproximativ
80 de cuvinte. Toate scenele trebuie accesibile din start_scene. Păstrează
tagurile Higgs numai în tts_text, niciodată în text.
Schema: {json.dumps(schema, ensure_ascii=False)}"""

    def generate(self, req: GenerationRequest) -> Story:
        if self.settings.llm_provider == "disabled":
            raise RuntimeError("Generarea LLM este dezactivată. Configurează LLM_PROVIDER.")
        prompt = self._prompt(req)
        if self.settings.llm_provider == "openai":
            from openai import OpenAI

            client = OpenAI(
                api_key=self.settings.openai_api_key,
                timeout=self.settings.llm_timeout_seconds,
            )
            response = client.responses.create(
                model=self.settings.story_llm_model, input=prompt
            )
            text = response.output_text
        elif self.settings.llm_provider == "openai-compatible":
            headers = {"Content-Type": "application/json"}
            if self.settings.llm_api_key:
                headers["Authorization"] = f"Bearer {self.settings.llm_api_key}"
            payload = {
                "model": self.settings.story_llm_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8,
            }
            with httpx.Client(timeout=self.settings.llm_timeout_seconds) as client:
                response = client.post(
                    f"{self.settings.llm_base_url.rstrip('/')}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                text = response.json()["choices"][0]["message"]["content"]
        else:
            raise ValueError(f"LLM_PROVIDER necunoscut: {self.settings.llm_provider}")
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            raise ValueError("Modelul nu a returnat JSON")
        return Story.model_validate(json.loads(match.group(0)))
