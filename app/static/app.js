const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const storyNode = document.getElementById("story-data");
let stopped = false;

async function fetchManifest(storyId) {
  const response = await fetch(`/api/stories/${storyId}/manifest`);
  return response.ok ? response.json() : null;
}

async function playAudio(url) {
  return new Promise((resolve, reject) => {
    const audio = new Audio(url);
    window.__storyAudio = audio;
    audio.onended = resolve;
    audio.onerror = reject;
    audio.play().catch(reject);
  });
}

async function runScene(story, sceneId, manifest) {
  if (stopped) return;
  const scene = story.scenes.find((item) => item.id === sceneId);
  if (!scene) return;

  document.getElementById("scene-title").innerHTML =
    `<p class="eyebrow">${scene.title}</p>`;
  const spoken = document.getElementById("spoken-text");
  const choices = document.getElementById("choices");
  choices.innerHTML = "";

  for (let index = 0; index < scene.segments.length; index += 1) {
    if (stopped) return;
    const segment = scene.segments[index];
    spoken.textContent = segment.text;
    const audioSegment = manifest?.scenes?.[scene.id]?.[index];
    if (audioSegment) {
      try {
        await playAudio(audioSegment.audio_url);
      } catch (error) {
        console.warn("Audio segment unavailable", error);
      }
    }
    await sleep(segment.pause_after_ms || 500);
  }

  if (stopped) return;
  if (scene.choices?.length) {
    const nextScene = await new Promise((resolve) => {
      scene.choices.forEach((choice) => {
        const button = document.createElement("button");
        button.className = "button";
        button.textContent = choice.label;
        button.onclick = () => {
          choices.innerHTML = "";
          resolve(choice.next_scene);
        };
        choices.appendChild(button);
      });
    });
    await runScene(story, nextScene, manifest);
  } else if (scene.next_scene) {
    await runScene(story, scene.next_scene, manifest);
  } else {
    spoken.textContent += "\n\nSfârșit.";
  }
}

async function waitForRender(storyId, statusElement) {
  for (;;) {
    await sleep(1200);
    const response = await fetch(`/api/stories/${storyId}/render-status`);
    if (!response.ok) {
      statusElement.textContent = "Nu am putut citi starea generării.";
      return;
    }
    const job = await response.json();
    if (job.state === "done") {
      statusElement.textContent = "Audio pregătit.";
      return;
    }
    if (job.state === "error") {
      statusElement.textContent = `Eroare TTS: ${job.error}`;
      return;
    }
    statusElement.textContent =
      `Generez audio: ${job.completed || 0}/${job.total || "?"} segmente…`;
  }
}

if (storyNode) {
  const story = JSON.parse(storyNode.textContent);
  const status = document.getElementById("status");

  document.getElementById("start-story").onclick = async () => {
    stopped = false;
    status.textContent = "Povestea rulează…";
    const manifest = await fetchManifest(story.id);
    await runScene(story, story.start_scene, manifest);
    status.textContent = stopped ? "Oprit." : "Poveste încheiată.";
  };

  document.getElementById("stop-story").onclick = () => {
    stopped = true;
    if (window.__storyAudio) window.__storyAudio.pause();
    status.textContent = "Oprit.";
  };

  document.getElementById("render-story").onclick = async () => {
    status.textContent = "Pornesc generarea audio…";
    const response = await fetch(`/api/stories/${story.id}/render`, {
      method: "POST",
    });
    if (!response.ok) {
      status.textContent = `Eroare: ${await response.text()}`;
      return;
    }
    await waitForRender(story.id, status);
  };
}

const form = document.getElementById("generate-form");
if (form) {
  form.onsubmit = async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(form));
    ["age", "estimated_minutes", "choices"].forEach((key) => {
      data[key] = Number(data[key]);
    });
    const output = document.getElementById("generate-result");
    output.textContent = "Se generează…";
    const response = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    output.textContent = JSON.stringify(await response.json(), null, 2);
  };
}
