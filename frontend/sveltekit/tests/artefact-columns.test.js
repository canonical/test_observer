// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { resolve } from "node:path";
import { build } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { Window } from "happy-dom";

/**
 * @typedef {object} ArtefactColumnsHarness
 * @property {(target: import("svelte").MountOptions["target"], family: string) => {shareUrl: () => string}} mountTable
 * @property {() => void} flushSync
 * @property {(component: object) => Promise<void>} unmount
 */
/** @type {ArtefactColumnsHarness | undefined} */
let harness;
/** @type {Window} */
let browserWindow;
/** @type {Map<string, PropertyDescriptor | undefined>} */
const originalGlobals = new Map();

before(async () => {
  const result = /** @type {{ output: { type: string; code: string }[] }[]} */ (
    /** @type {unknown} */ (
      await build({
        configFile: false,
        logLevel: "silent",
        plugins: [
          svelte({ compilerOptions: { runes: true } }),
          {
            name: "artefact-table-test-app",
            resolveId(id) {
              if (id.startsWith("$app/")) return `\0test:${id}`;
            },
            load(id) {
              if (id === "\0test:$app/env")
                return "export const browser = true;";
              if (id === "\0test:$app/paths")
                return 'export const resolve = (path) => "/" + path;';
              if (id === "\0test:$app/state")
                return "export const page = { state: {} };";
              if (id === "\0test:$app/navigation")
                return "export const goto = async (url) => window.history.replaceState({}, '', url);";
            },
          },
        ],
        resolve: { alias: { $lib: resolve("src/lib") } },
        build: {
          write: false,
          lib: { entry: "tests/artefact-columns-entry.js", formats: ["es"] },
          rolldownOptions: { output: { codeSplitting: false } },
        },
      })
    )
  );
  const bundle = result[0]?.output.find((item) => item.type === "chunk");
  assert.ok(bundle);
  browserWindow = new Window({ url: "http://localhost/family/alpha" });
  for (const name of [
    "window",
    "document",
    "location",
    "sessionStorage",
    "navigator",
    "customElements",
    "Comment",
    "Text",
    "Node",
    "Element",
    "HTMLElement",
    "HTMLMediaElement",
    "HTMLDialogElement",
    "Event",
    "CustomEvent",
    "MouseEvent",
    "ResizeObserver",
    "MutationObserver",
    "getComputedStyle",
    "requestAnimationFrame",
    "cancelAnimationFrame",
  ]) {
    originalGlobals.set(
      name,
      Object.getOwnPropertyDescriptor(globalThis, name),
    );
    Object.defineProperty(globalThis, name, {
      configurable: true,
      value:
        name === "window" ? browserWindow : Reflect.get(browserWindow, name),
    });
  }
  const importedModule = /** @type {unknown} */ (
    await import(
      `data:text/javascript;base64,${Buffer.from(bundle.code).toString("base64")}`
    )
  );
  harness = /** @type {ArtefactColumnsHarness} */ (importedModule);
});

after(async () => {
  for (const [name, descriptor] of originalGlobals) {
    if (descriptor) Object.defineProperty(globalThis, name, descriptor);
    else Reflect.deleteProperty(globalThis, name);
  }
  await browserWindow.happyDOM.abort();
});

void test("default-hidden columns can be shown and restored in shared views", async () => {
  assert.ok(harness);
  for (const family of ["alpha", "beta"]) {
    browserWindow.sessionStorage.clear();
    browserWindow.location.href = `http://localhost/family/${family}`;
    const target = browserWindow.document.createElement("div");
    browserWindow.document.body.append(target);
    // @ts-expect-error Happy DOM elements differ from DOM lib types.
    const table = harness.mountTable(target, family);
    try {
      const menu = await openChooser(target);
      assert.equal(
        findOption(menu, "Risk").getAttribute("aria-selected"),
        "true",
      );
      assert.equal(
        findOption(menu, "Comment").getAttribute("aria-selected"),
        "false",
      );
      for (const label of ["Store", "SHA256", "Image URL"]) {
        const option = findOption(menu, label);
        assert.equal(
          option.getAttribute("aria-selected"),
          "false",
          `${family}: ${label} hidden by default`,
        );
        option.dispatchEvent(
          new browserWindow.MouseEvent("click", { bubbles: true }),
        );
        harness.flushSync();
        assert.equal(
          option.getAttribute("aria-selected"),
          "true",
          `${label} can be shown`,
        );
      }
      const track = findOption(menu, "Track");
      track.dispatchEvent(
        new browserWindow.MouseEvent("click", { bubbles: true }),
      );
      harness.flushSync();
      assert.equal(track.getAttribute("aria-selected"), "false");
      table.shareUrl();
      await new Promise((resolve) => setTimeout(resolve, 900));
    } finally {
      await harness.unmount(table);
      target.remove();
    }

    const sharedUrl = browserWindow.location.href;
    assert.ok(new URL(sharedUrl).searchParams.has("view"));
    for (const mode of ["saved", "shared"]) {
      if (mode === "shared") browserWindow.sessionStorage.clear();
      browserWindow.location.href =
        mode === "shared" ? sharedUrl : `http://localhost/family/${family}`;
      const restoredTarget = browserWindow.document.createElement("div");
      browserWindow.document.body.append(restoredTarget);
      // @ts-expect-error Happy DOM elements differ from DOM lib types.
      const restored = harness.mountTable(restoredTarget, family);
      try {
        const menu = await openChooser(restoredTarget);
        for (const label of ["Store", "SHA256", "Image URL"]) {
          assert.equal(
            findOption(menu, label).getAttribute("aria-selected"),
            "true",
            `${family}: ${mode} view shows ${label}`,
          );
        }
        assert.equal(
          findOption(menu, "Track").getAttribute("aria-selected"),
          "false",
        );
        assert.equal(
          findOption(menu, "Comment").getAttribute("aria-selected"),
          "false",
        );
      } finally {
        await harness.unmount(restored);
        restoredTarget.remove();
      }
    }
  }
});

/** @param {import("happy-dom").HTMLElement} target */
async function openChooser(target) {
  assert.ok(harness);
  const menuButton = target.querySelector('[aria-label="Name column menu"]');
  assert.ok(menuButton);
  menuButton.dispatchEvent(
    new browserWindow.MouseEvent("click", { bubbles: true }),
  );
  for (let attempt = 0; attempt < 20; attempt++) {
    await new Promise((resolve) => setTimeout(resolve, 10));
    harness.flushSync();
    if (browserWindow.document.querySelector(".sv-grid-column-menu")) break;
  }
  const choose = Array.from(
    browserWindow.document.querySelectorAll("button"),
  ).find((button) => button.textContent.includes("Choose columns"));
  assert.ok(choose);
  choose.click();
  harness.flushSync();
  const menu = browserWindow.document.querySelector(
    ".sv-grid-choose-columns-menu",
  );
  assert.ok(menu);
  return menu;
}

/** @param {import("happy-dom").Element} menu
 * @param {string} label
 */
function findOption(menu, label) {
  /** @type {import("happy-dom").Element | undefined} */
  const option = Array.from(menu.querySelectorAll('[role="option"]')).find(
    (item) => item.textContent.trim() === label,
  );
  assert.ok(option, `${label} is available in Choose columns`);
  return option;
}
