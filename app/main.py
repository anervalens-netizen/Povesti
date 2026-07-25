from __future__ import annotations

import json
import re
import threading
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .audio import AudioRenderer
from .catalog import StoryCatalog
from .config import settings
from .generator import StoryGenerator
from .schemas import GenerationRequest
from .tts import build_tts_provider

BASE = Path(__file__).parent
app = FastAPI(title=settings.app_name, version="0.1.0")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
app.mount("/media", StaticFiles(directory=settings.media_dir), name="media")
templates = Jinja2Templates(directory=BASE / "templates")
catalog = StoryCatalog(settings.story_dir)
render_jobs: dict[str, dict] = {}
render_lock = threading.Lock()


def _set_job(story_id: str, **values) -> None:
    with render_lock:
        current = render_jobs.setdefault(story_id, {})
        current.update(values)


def _render_job(story_id: str, force: bool) -> None:
    try:
        story = catalog.get(story_id)
        total = sum(len(scene.segments) for scene in story.scenes)
        _set_job(story_id, state="running", completed=0, total=total, error=None)
        renderer = AudioRenderer(settings.media_dir, build_tts_provider(settings))
        renderer.render(
            story,
            force=force,
            progress=lambda completed, total: _set_job(
                story_id, completed=completed, total=total
            ),
        )
        _set_job(story_id, state="done", completed=total, total=total)
    except Exception as exc:  # status must survive provider failures
        _set_job(story_id, state="error", error=str(exc))


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request, "index.html", {"stories": catalog.list(), "settings": settings}
    )


@app.get("/stories/{story_id}", response_class=HTMLResponse)
def story_page(request: Request, story_id: str):
    try:
        story = catalog.get(story_id)
    except KeyError as exc:
        raise HTTPException(404, "Povestea nu există") from exc
    manifest_path = settings.media_dir / story.id / "manifest.json"
    return templates.TemplateResponse(
        request,
        "story.html",
        {"story": story, "has_audio": manifest_path.exists()},
    )


@app.get("/generate", response_class=HTMLResponse)
def generate_page(request: Request):
    return templates.TemplateResponse(
        request, "generate.html", {"settings": settings}
    )


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "stories": len(catalog.list()),
        "tts_provider": settings.tts_provider,
        "llm_provider": settings.llm_provider,
    }


@app.get("/api/stories")
def api_stories():
    return [story.model_dump(mode="json") for story in catalog.list()]


@app.get("/api/stories/{story_id}")
def api_story(story_id: str):
    try:
        return catalog.get(story_id).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(404, "Povestea nu există") from exc


@app.get("/api/stories/{story_id}/manifest")
def api_manifest(story_id: str):
    path = settings.media_dir / story_id / "manifest.json"
    if not path.exists():
        raise HTTPException(404, "Audio negenerat")
    return json.loads(path.read_text(encoding="utf-8"))


@app.post("/api/stories/{story_id}/render", status_code=status.HTTP_202_ACCEPTED)
def render_story(story_id: str, background_tasks: BackgroundTasks, force: bool = False):
    try:
        story = catalog.get(story_id)
    except KeyError as exc:
        raise HTTPException(404, "Povestea nu există") from exc

    with render_lock:
        existing = render_jobs.get(story_id, {})
        if existing.get("state") in {"queued", "running"}:
            return existing
        total = sum(len(scene.segments) for scene in story.scenes)
        render_jobs[story_id] = {
            "state": "queued",
            "completed": 0,
            "total": total,
            "error": None,
        }
    background_tasks.add_task(_render_job, story_id, force)
    return render_jobs[story_id]


@app.get("/api/stories/{story_id}/render-status")
def render_status(story_id: str):
    try:
        catalog.get(story_id)
    except KeyError as exc:
        raise HTTPException(404, "Povestea nu există") from exc
    with render_lock:
        return render_jobs.get(
            story_id,
            {"state": "idle", "completed": 0, "total": 0, "error": None},
        )


@app.post("/api/generate")
def generate_story(req: GenerationRequest):
    try:
        story = StoryGenerator(settings).generate(req)
        slug = re.sub(r"[^a-z0-9]+", "-", story.id.lower()).strip("-")
        story.id = slug or "draft-poveste"
        path = catalog.save(story)
        return {"saved": str(path), "story": story.model_dump(mode="json")}
    except FileExistsError as exc:
        raise HTTPException(409, "Există deja o poveste cu acest ID") from exc
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=False)
