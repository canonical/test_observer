// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { resolve } from "node:path";
import { build } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { Window } from "happy-dom";

/** @type {typeof import("./layout-loading-entry") | undefined} */
let harness;
/** @type {Window} */
let browserWindow;
/** @type {Map<string, PropertyDescriptor | undefined>} */
const originalGlobals = new Map();

before(async () => {
  const buildResult =
    /** @type {{ output: { type: string; code: string }[] }[]} */ (
      /** @type {unknown} */ (
        await build({
          configFile: false,
          logLevel: "silent",
          plugins: [
            svelte({ compilerOptions: { runes: true } }),
            {
              name: "layout-test-app-paths",
              resolveId(id) {
                if (id === "$app/paths") return "\0layout-test-paths";
              },
              load(id) {
                if (id === "\0layout-test-paths") {
                  return 'export const resolve = (path) => "/" + path.replace(/^\\//, "");';
                }
              },
            },
          ],
          resolve: {
            alias: {
              $lib: resolve("src/lib"),
              "$app/state": resolve("tests/layout-loading-state.svelte.js"),
            },
          },
          build: {
            write: false,
            lib: { entry: "tests/layout-loading-entry.js", formats: ["es"] },
            rolldownOptions: { output: { codeSplitting: false } },
          },
        })
      )
    );
  const bundle = buildResult[0]?.output.find((item) => item.type === "chunk");
  assert.ok(bundle, "layout test bundle should be generated");
  browserWindow = new Window({ url: "http://localhost/alpha" });
  for (const name of [
    "window",
    "document",
    "navigator",
    "localStorage",
    "Comment",
    "Text",
    "Node",
    "Element",
    "HTMLElement",
    "HTMLMediaElement",
    "Event",
    "CustomEvent",
    "MouseEvent",
    "getComputedStyle",
    "requestAnimationFrame",
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
  harness = /** @type {typeof import("./layout-loading-entry")} */ (
    importedModule
  );
});

after(async () => {
  for (const [name, descriptor] of originalGlobals) {
    if (descriptor) Object.defineProperty(globalThis, name, descriptor);
    else Reflect.deleteProperty(globalThis, name);
  }
  await browserWindow.happyDOM.abort();
});

void test("navigation makes only the page inert and keeps status and shell controls available", async () => {
  assert.ok(harness);
  const { mountLayout, setDestination, unmountLayout, flushSync, showError } =
    harness;
  const target = browserWindow.document.createElement("div");
  browserWindow.document.body.append(target);
  // @ts-expect-error Happy DOM's element types differ from the DOM lib types.
  const component = mountLayout(target);
  try {
    const main = target.querySelector("main");
    const page = target.querySelector(".page-content");
    const action = target.querySelector("#page-action");
    const sidebar = target.querySelector(".side-navigation");
    assert.ok(main && page && action && sidebar);
    assert.equal(main.getAttribute("aria-busy"), "false");
    assert.equal(page.hasAttribute("inert"), false);
    assert.equal(target.querySelector(".loading-overlay"), null);

    setDestination("/beta");
    assert.equal(main.getAttribute("aria-busy"), "true");
    assert.equal(page.hasAttribute("inert"), true);
    assert.equal(action.closest("[inert]"), page);
    const status = target.querySelector('.loading-overlay[role="status"]');
    assert.ok(status);
    assert.match(status.textContent, /Loading…/);
    assert.equal(status.getAttribute("aria-live"), "polite");
    assert.equal(status.closest("[inert], [aria-busy=true]"), null);
    assert.equal(status.parentElement, main.parentElement);
    assert.equal(sidebar.closest("[inert], .content-region"), null);

    // The layout leaves ordinary href handling to SvelteKit rather than adding
    // a navigation lock or click interception while another request is pending.
    const link = sidebar.querySelector('a[href="/alpha"]');
    assert.ok(link);
    const click = new browserWindow.MouseEvent("click", {
      bubbles: true,
      cancelable: true,
    });
    link.dispatchEvent(click);
    assert.equal(click.defaultPrevented, false);

    const theme = Array.from(sidebar.querySelectorAll("button")).find(
      (button) => button.textContent.includes("Theme:"),
    );
    assert.ok(theme);
    const oldTheme = theme.textContent;
    theme.click();
    flushSync();
    assert.notEqual(theme.textContent, oldTheme);

    const collapse = sidebar.querySelector(
      '[aria-label="Collapse navigation"]',
    );
    assert.ok(collapse);
    collapse.dispatchEvent(
      new browserWindow.MouseEvent("click", { bubbles: true }),
    );
    flushSync();
    assert.ok(sidebar.classList.contains("collapsed"));
    const expand = sidebar.querySelector('[aria-label="Expand navigation"]');
    assert.ok(expand);
    expand.dispatchEvent(
      new browserWindow.MouseEvent("click", { bubbles: true }),
    );
    flushSync();
    assert.equal(sidebar.classList.contains("collapsed"), false);

    // A superseding destination must not temporarily unlock the old page or
    // remove the indicator. No independent promise/loading state is involved.
    setDestination("/issues");
    assert.equal(target.querySelector(".loading-overlay"), status);
    assert.equal(page.hasAttribute("inert"), true);
    assert.equal(target.querySelector("#page-action"), action);

    showError("Navigation failed");
    const dismiss = target.querySelector('[aria-label="Dismiss error"]');
    assert.ok(dismiss);
    assert.equal(dismiss.closest("[inert], .content-region"), null);
    dismiss.dispatchEvent(
      new browserWindow.MouseEvent("click", { bubbles: true }),
    );
    flushSync();
    assert.equal(target.querySelector('[aria-label="Dismiss error"]'), null);

    setDestination(null);
    assert.equal(main.getAttribute("aria-busy"), "false");
    assert.equal(page.hasAttribute("inert"), false);
    assert.equal(target.querySelector(".loading-overlay"), null);
    assert.equal(target.querySelector("#page-action"), action);

    // A later navigation can start and clear normally after success or failure.
    setDestination("/alpha");
    assert.ok(target.querySelector(".loading-overlay"));
    setDestination(null);
    assert.equal(page.hasAttribute("inert"), false);
    assert.equal(target.querySelector(".loading-overlay"), null);
  } finally {
    setDestination(null);
    await unmountLayout(component);
    target.remove();
  }
});
