from __future__ import annotations
import json, re
import httpx
from .config import Settings
from .schemas import GenerationRequest, Story

SYSTEM = """Ești autor de povești audio interactive pentru copii de 2-6 ani.
Scrii exclusiv în română naturală, blândă, clară și potrivită citirii cu voce tare.
Copilul Alexandru este personajul principal. Lecția este transmisă prin consecințe blânde,
fără rușinare, amenințări sau moralizare apăsată. Include dialog, umor de familie,
repetiții participative, 1-4 alegeri reale și un final liniștitor.
Returnează NUMAI JSON valid conform structurii cerute."""

class StoryGenerator:
    def __init__(self, settings: Settings): self.settings = settings

    def _prompt(self, req: GenerationRequest) -> str:
        schema = Story.model_json_schema()
        return f"""{SYSTEM}
Idee: {req.title_idea}
Lecție: {req.lesson}
Elemente preferate: {req.favorite_elements}
Vârstă: {req.age} ani
Durată: aproximativ {req.estimated_minutes} minute
Număr de momente interactive: {req.choices}
Folosește schema JSON următoare. Setează episode la 999 pentru draft.
Rolurile trebuie să includă narrator și personaje cu id-uri simple; narrator nu apare în characters.
Fiecare segment are maximum 4096 caractere. Toate scenele trebuie accesibile din start_scene.
Schema: {json.dumps(schema, ensure_ascii=False)}"""

    def generate(self, req: GenerationRequest) -> Story:
        if self.settings.llm_provider == "disabled":
            raise RuntimeError("Generarea LLM este dezactivată. Configurează LLM_PROVIDER.")
        prompt = self._prompt(req)
        if self.settings.llm_provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=self.settings.openai_api_key, timeout=self.settings.llm_timeout_seconds)
            response = client.responses.create(model=self.settings.story_llm_model, input=prompt)
            text = response.output_text
        elif self.settings.llm_provider == "openai-compatible":
            headers = {"Content-Type": "application/json"}
            if self.settings.llm_api_key: headers["Authorization"] = f"Bearer {self.settings.llm_api_key}"
            payload = {"model": self.settings.story_llm_model,
                       "messages": [{"role":"user","content":prompt}], "temperature":0.8}
            with httpx.Client(timeout=self.settings.llm_timeout_seconds) as client:
                r = client.post(f"{self.settings.llm_base_url.rstrip('/')}/chat/completions", headers=headers, json=payload)
                r.raise_for_status(); text = r.json()["choices"][0]["message"]["content"]
        else:
            raise ValueError(f"LLM_PROVIDER necunoscut: {self.settings.llm_provider}")
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match: raise ValueError("Modelul nu a returnat JSON")
        return Story.model_validate(json.loads(match.group(0)))
