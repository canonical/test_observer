// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-argument */
import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { resolve } from "node:path";
import { build } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { Window } from "happy-dom";

let app;
let browser;
const descriptors = new Map();
const frames = new Map();
let frameId = 0;
let scrolls = 0;
function renderFrame() {
  const pending = [...frames.values()];
  frames.clear();
  for (const callback of pending) callback();
}

before(async () => {
  browser = new Window({ url: "http://localhost" });
  const globals = Object.fromEntries(
    [
      "window",
      "document",
      "navigator",
      "HTMLElement",
      "Element",
      "Node",
      "Text",
      "Comment",
      "Event",
      "MouseEvent",
      "CustomEvent",
    ].map((key) => [key, browser[key]]),
  );
  Object.assign(globals, {
    requestAnimationFrame: (callback) => {
      const id = ++frameId;
      frames.set(id, callback);
      return id;
    },
    cancelAnimationFrame: (id) => frames.delete(id),
  });
  for (const [key, value] of Object.entries(globals)) {
    descriptors.set(key, Object.getOwnPropertyDescriptor(globalThis, key));
    Object.defineProperty(globalThis, key, { configurable: true, value });
  }
  browser.HTMLElement.prototype.scrollIntoView = () => ++scrolls;
  const built = await build({
    configFile: false,
    logLevel: "silent",
    plugins: [svelte({ configFile: false })],
    resolve: { alias: { $lib: resolve("src/lib") }, conditions: ["browser"] },
    build: {
      write: false,
      lib: {
        entry: "tests/attachment-rule-attention-entry.svelte.js",
        formats: ["es"],
      },
      rolldownOptions: { output: { codeSplitting: false } },
    },
  });
  const bundle = built[0].output.find((item) => item.type === "chunk");
  app = await import(
    `data:text/javascript;base64,${Buffer.from(bundle.code).toString("base64")}`
  );
});

after(() => {
  for (const [key, descriptor] of descriptors) {
    if (descriptor) Object.defineProperty(globalThis, key, descriptor);
    else Reflect.deleteProperty(globalThis, key);
  }
  void browser.happyDOM.abort();
});

function fixture(attention) {
  const element = document.createElement("div");
  document.body.append(element);
  const ui = app.mountDisclosure(element, attention);
  return {
    element,
    ui,
    details: element.querySelector("details"),
    summary: element.querySelector("summary"),
    async destroy() {
      await ui.destroy();
      element.remove();
    },
  };
}

void test("mounted disclosure waits for readiness and the DOM frame, then attends once without overriding manual collapse", async () => {
  const event = {};
  const view = fixture({ target: event, ready: false });
  try {
    renderFrame();
    assert.equal(view.details.open, false);
    view.ui.update({ target: event, ready: true });
    assert.equal(view.details.open, false);
    renderFrame();
    assert.equal(view.details.open, true);
    assert.ok(
      document.activeElement === view.summary,
      "summary receives focus",
    );
    const scrollCount = scrolls;
    view.details.open = false;
    view.ui.update({ target: event, ready: false });
    view.ui.update({ target: event, ready: true });
    renderFrame();
    assert.equal(view.details.open, false);
    assert.equal(scrolls, scrollCount);
    view.ui.update({ target: {}, ready: true });
    renderFrame();
    assert.equal(
      view.details.open,
      true,
      "a deliberate new target event acts again",
    );
  } finally {
    await view.destroy();
  }
});

void test("mounted pending attention cancels on target, navigation readiness and unmount changes", async () => {
  const view = fixture({ target: {}, ready: true });
  try {
    view.ui.update({ target: null, ready: true });
    renderFrame();
    assert.equal(view.details.open, false);
    view.ui.update({ target: {}, ready: true });
    view.ui.update({ target: {}, ready: false });
    renderFrame();
    assert.equal(view.details.open, false);
    view.ui.update({ target: {}, ready: true });
    const scrollCount = scrolls;
    await view.destroy();
    renderFrame();
    assert.equal(scrolls, scrollCount);
    assert.equal(view.details.open, false);
  } finally {
    view.element.remove();
  }
});

void test("mounted attention never steals dialog focus or queues attention after close", async () => {
  const dialog = document.createElement("dialog");
  dialog.open = true;
  dialog.innerHTML = "<button>Dialog action</button>";
  document.body.append(dialog);
  const button = dialog.querySelector("button");
  button.focus();
  const event = {};
  const view = fixture({ target: event, ready: true });
  try {
    const scrollCount = scrolls;
    renderFrame();
    assert.equal(view.details.open, true);
    assert.ok(document.activeElement === button, "dialog retains focus");
    assert.equal(scrolls, scrollCount);
    dialog.open = false;
    view.ui.update({ target: event, ready: true });
    renderFrame();
    assert.ok(
      document.activeElement === button,
      "no deferred focus after close",
    );
    assert.equal(scrolls, scrollCount);
  } finally {
    await view.destroy();
    dialog.remove();
  }
});
