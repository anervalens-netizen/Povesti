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
Taguri Higgs TTS 3 permise:
- emotion: elation, amusement, enthusiasm, determination, pride, contentment,
  affection, relief, contemplation, confusion, surprise, awe, longing, arousal,
  anger, fear, disgust, bitterness, sadness, shame, helplessness
- style: singing, shouting, whispering
- prosody la început: speed_very_slow, speed_slow, speed_fast, speed_very_fast,
  pitch_low, pitch_high, expressive_high, expressive_low
- prosody inline: pause, long_pause
- sfx inline: cough, laughter, crying, screaming, burping, humming, sigh, sniff,
  sneeze. După sfx pune imediat onomatopeea, fără spațiu, de exemplu
  <|sfx:laughter|>Hehe.
Sintaxa este exact <|category:value|>. Emoția, stilul, viteza, pitch-ul și
expresivitatea se pun numai la începutul replicii. Pauzele și efectele se pun
exact în locul în care trebuie auzite.
"""

SYSTEM = f"""Ești autor și regizor de povești audio interactive pentru copii de 2-6 ani.
Scrii exclusiv în română naturală, blândă, clară și potrivită rostirii.
Copilul Alexandru este personajul principal. Lecția este transmisă prin
consecințe blânde, fără rușinare, amenințări sau moralizare apăsată. Include
dialog interesant, umor de familie, repetiții participative, alegeri reale și
un final liniștitor.

Fiecare segment trebuie să aibă:
- text: varianta curată, afișată în interfață;
- tts_text: aceeași replică, pregătită integral pentru Higgs TTS 3, cu taguri
  folosite rar și intenționat;
- pause_after_ms: pauza tehnică după fișierul audio.

Folosește narrator_voice=narator. Pentru personaje folosește exclusiv aceste
profiluri vocale: {VOICE_PROFILES}. Nu include narrator în characters.
{HIGGS_TAGS}
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
Fiecare segment are maximum 4096 caractere. Toate scenele trebuie accesibile
din start_scene. Păstrează tagurile Higgs numai în tts_text, niciodată în text.
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
