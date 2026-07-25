const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const storyNode = document.getElementById("story-data");
let playbackRunId = 0;
let cancelActiveAudio = null;
let cancelPendingChoice = null;

function isPlaybackActive(runId) {
  return runId === playbackRunId;
}

function cancelPlayback() {
  playbackRunId += 1;

  if (cancelActiveAudio) {
    const cancel = cancelActiveAudio;
    cancelActiveAudio = null;
    cancel();
  }

  if (cancelPendingChoice) {
    const cancel = cancelPendingChoice;
    cancelPendingChoice = null;
    cancel();
  }
}

async function fetchManifest(storyId) {
  const response = await fetch(`/api/stories/${storyId}/manifest`);
  return response.ok ? response.json() : null;
}

async function playAudio(url, runId) {
  return new Promise((resolve, reject) => {
    if (!isPlaybackActive(runId)) {
      resolve(false);
      return;
    }

    const audio = new Audio(url);
    let settled = false;

    const cleanup = () => {
      audio.onended = null;
      audio.onerror = null;
      if (cancelActiveAudio === cancel) cancelActiveAudio = null;
    };

    const finish = (played) => {
      if (settled) return;
      settled = true;
      cleanup();
      resolve(played);
    };

    const fail = (error) => {
      if (settled) return;
      settled = true;
      cleanup();
      reject(error);
    };

    const cancel = () => {
      audio.pause();
      finish(false);
    };

    cancelActiveAudio = cancel;
    audio.onended = () => finish(true);
    audio.onerror = () => fail(new Error(`Audio indisponibil: ${url}`));
    audio.play().catch(fail);
  });
}

function renderSceneTitle(title) {
  const container = document.getElementById("scene-title");
  const paragraph = document.createElement("p");
  paragraph.className = "eyebrow";
  paragraph.textContent = title;
  container.replaceChildren(paragraph);
}

function waitForChoice(scene, choicesElement, runId) {
  return new Promise((resolve) => {
    if (!isPlaybackActive(runId)) {
      resolve(null);
      return;
    }

    let settled = false;
    const finish = (nextScene) => {
      if (settled) return;
      settled = true;
      if (cancelPendingChoice === cancel) cancelPendingChoice = null;
      choicesElement.replaceChildren();
      resolve(nextScene);
    };
    const cancel = () => finish(null);
    cancelPendingChoice = cancel;

    scene.choices.forEach((choice) => {
      const button = document.createElement("button");
      button.className = "button";
      button.textContent = choice.label;
      button.onclick = () => {
        if (isPlaybackActive(runId)) finish(choice.next_scene);
      };
      choicesElement.appendChild(button);
    });
  });
}

async function runStory(story, manifest, runId) {
  const spoken = document.getElementById("spoken-text");
  const choices = document.getElementById("choices");
  let sceneId = story.start_scene;

  while (sceneId && isPlaybackActive(runId)) {
    const scene = story.scenes.find((item) => item.id === sceneId);
    if (!scene) throw new Error(`Scena nu există: ${sceneId}`);

    renderSceneTitle(scene.title);
    choices.replaceChildren();

    for (let index = 0; index < scene.segments.length; index += 1) {
      if (!isPlaybackActive(runId)) return false;

      const segment = scene.segments[index];
      spoken.textContent = segment.text;
      const audioSegment = manifest?.scenes?.[scene.id]?.[index];
      if (audioSegment) {
        try {
          await playAudio(audioSegment.audio_url, runId);
        } catch (error) {
          if (isPlaybackActive(runId)) {
            console.warn("Audio segment unavailable", error);
          }
        }
      }

      await sleep(segment.pause_after_ms ?? 500);
      if (!isPlaybackActive(runId)) return false;
    }

    if (scene.choices?.length) {
      sceneId = await waitForChoice(scene, choices, runId);
    } else {
      sceneId = scene.next_scene || null;
    }
  }

  if (isPlaybackActive(runId)) {
    spoken.textContent += "\n\nSfârșit.";
    return true;
  }
  return false;
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
  const startButton = document.getElementById("start-story");
  const stopButton = document.getElementById("stop-story");
  const choices = document.getElementById("choices");

  startButton.onclick = async () => {
    if (startButton.disabled) return;

    cancelPlayback();
    const runId = playbackRunId;
    startButton.disabled = true;
    status.textContent = "Povestea rulează…";

    try {
      const manifest = await fetchManifest(story.id);
      if (!isPlaybackActive(runId)) return;
      const completed = await runStory(story, manifest, runId);
      if (isPlaybackActive(runId)) {
        status.textContent = completed ? "Poveste încheiată." : "Oprit.";
      }
    } catch (error) {
      if (isPlaybackActive(runId)) {
        console.error(error);
        status.textContent = `Eroare la redare: ${error.message || error}`;
      }
    } finally {
      if (isPlaybackActive(runId)) startButton.disabled = false;
    }
  };

  stopButton.onclick = () => {
    cancelPlayback();
    choices.replaceChildren();
    startButton.disabled = false;
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
