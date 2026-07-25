const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

function makeElement(id) {
  return {
    id,
    className: "",
    textContent: "",
    disabled: false,
    children: [],
    onclick: null,
    replaceChildren(...children) {
      this.children = children;
    },
    appendChild(child) {
      this.children.push(child);
    },
  };
}

async function main() {
  const maliciousTitle = '<img src=x onerror="globalThis.pwned=true">';
  const story = {
    id: "player-test",
    start_scene: "alegere",
    scenes: [
      {
        id: "alegere",
        title: maliciousTitle,
        segments: [{ text: "Alege un drum.", pause_after_ms: 1 }],
        choices: [
          { label: "Stânga", next_scene: "final-stanga" },
          { label: "Dreapta", next_scene: "final-dreapta" },
        ],
      },
      {
        id: "final-stanga",
        title: "Final stânga",
        segments: [{ text: "Gata.", pause_after_ms: 1 }],
      },
      {
        id: "final-dreapta",
        title: "Final dreapta",
        segments: [{ text: "Gata.", pause_after_ms: 1 }],
      },
    ],
  };

  const elements = {
    "story-data": makeElement("story-data"),
    "scene-title": makeElement("scene-title"),
    "spoken-text": makeElement("spoken-text"),
    choices: makeElement("choices"),
    status: makeElement("status"),
    "start-story": makeElement("start-story"),
    "stop-story": makeElement("stop-story"),
    "render-story": makeElement("render-story"),
  };
  elements["story-data"].textContent = JSON.stringify(story);

  let manifestFetches = 0;
  const document = {
    getElementById(id) {
      return elements[id] || null;
    },
    createElement(tagName) {
      return makeElement(tagName);
    },
  };

  const context = {
    document,
    console,
    Promise,
    setTimeout,
    clearTimeout,
    fetch: async (url) => {
      if (url.endsWith("/manifest")) manifestFetches += 1;
      return {
        ok: false,
        async json() {
          return null;
        },
        async text() {
          return "";
        },
      };
    },
    Audio: class {
      play() {
        return Promise.resolve();
      }
      pause() {}
    },
    FormData: class {},
  };

  vm.createContext(context);
  const source = fs.readFileSync(
    path.join(__dirname, "..", "app", "static", "app.js"),
    "utf8",
  );
  vm.runInContext(source, context, { filename: "app.js" });

  const firstRun = elements["start-story"].onclick();
  await new Promise((resolve) => setTimeout(resolve, 20));

  assert.equal(manifestFetches, 1);
  assert.equal(elements["start-story"].disabled, true);
  assert.equal(elements["scene-title"].children.length, 1);
  assert.equal(elements["scene-title"].children[0].textContent, maliciousTitle);
  assert.equal(elements["scene-title"].children[0].className, "eyebrow");
  assert.equal(context.pwned, undefined);

  await elements["start-story"].onclick();
  assert.equal(manifestFetches, 1, "a second playback must not start concurrently");

  elements["stop-story"].onclick();
  await firstRun;
  assert.equal(elements.status.textContent, "Oprit.");
  assert.equal(elements["start-story"].disabled, false);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
