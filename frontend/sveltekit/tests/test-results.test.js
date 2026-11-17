// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { resolve } from "node:path";
import { build } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { Window } from "happy-dom";

const endpoint = "test-results/search-page?limit=50&offset=0";
/** @type {typeof import("./test-results-entry") | undefined} */
let harness;
/** @type {Window} */
let browserWindow;
/** @type {Map<string, PropertyDescriptor | undefined>} */
const originalGlobals = new Map();

before(async () => {
  const apiModule = `
    export const requests = [];
    let handler = () => Promise.resolve(null);
    export function setHandler(next) { handler = next; }
    export function resetApi() {
      requests.length = 0;
      handler = () => Promise.resolve(null);
    }
    export function silentApi(path, options = {}) {
      requests.push({ path, options });
      return handler(path, options);
    }
  `;
  const buildResult =
    /** @type {{ output: { type: string; code: string }[] }[]} */ (
      /** @type {unknown} */ (
        await build({
          configFile: false,
          logLevel: "silent",
          plugins: [
            svelte({ compilerOptions: { runes: true } }),
            {
              name: "test-results-api-stub",
              resolveId(id) {
                if (id === "$lib/api/client") return "\0test-results-api";
              },
              load(id) {
                if (id === "\0test-results-api") return apiModule;
              },
            },
          ],
          resolve: {
            alias: [
              { find: "$lib/api/client", replacement: "\0test-results-api" },
              { find: "$lib", replacement: resolve("src/lib") },
            ],
          },
          build: {
            write: false,
            lib: { entry: "tests/test-results-entry.js", formats: ["es"] },
            rolldownOptions: { output: { codeSplitting: false } },
          },
        })
      )
    );
  const bundle = buildResult[0]?.output.find((item) => item.type === "chunk");
  assert.ok(bundle, "test results page bundle should be generated");

  browserWindow = new Window({ url: "http://localhost/test-results" });
  for (const name of [
    "window",
    "document",
    "navigator",
    "customElements",
    "Comment",
    "Text",
    "Node",
    "Element",
    "HTMLElement",
    "HTMLMediaElement",
    "Event",
    "MouseEvent",
    "ResizeObserver",
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

  harness = /** @type {typeof import("./test-results-entry")} */ (
    await import(
      `data:text/javascript;base64,${Buffer.from(bundle.code).toString("base64")}`
    )
  );
});

after(async () => {
  for (const [name, descriptor] of originalGlobals) {
    if (descriptor) Object.defineProperty(globalThis, name, descriptor);
    else Reflect.deleteProperty(globalThis, name);
  }
  if (browserWindow) await browserWindow.happyDOM.abort();
});

function makeRow(id, name) {
  return {
    test_result: {
      id,
      created_at: "2026-01-02T03:04:05Z",
      name,
      category: `category-${id}`,
      status: "PASSED",
    },
    test_execution: {
      id: id + 100,
      environment: { name: `lab-${id}` },
      test_plan: `smoke-${id}`,
    },
    artefact: {
      id: id + 200,
      name: `artefact-${id}`,
      version: `1.${id}`,
      track: `stable-${id}`,
      family: "snap",
    },
    artefact_build: { architecture: `amd64-${id}` },
  };
}

function makePage(rows) {
  return { limit: 50, offset: 0, test_results: rows };
}

async function settlePromises() {
  for (let index = 0; index < 6; index += 1) await Promise.resolve();
  harness?.flushSync();
}

function mountInDocument() {
  assert.ok(harness);
  const target = browserWindow.document.createElement("div");
  browserWindow.document.body.append(target);
  const component = harness.mountPage(target);
  return { component, target };
}

async function unmountFromDocument(component, target) {
  assert.ok(harness);
  await harness.unmountPage(component);
  target.remove();
}

function assertFirstPageRequest() {
  assert.ok(harness);
  assert.ok(harness.requests.length > 0);
  assert.deepEqual(
    harness.requests.map((request) => request.path),
    Array(harness.requests.length).fill(endpoint),
  );
  assert.ok(harness.requests.every((request) => request.options.signal));
}

void test("shows accessible loading state and aborts its request on teardown", async () => {
  assert.ok(harness);
  harness.resetApi();
  harness.setHandler(() => new Promise(() => {}));
  const { component, target } = mountInDocument();

  const region = target.querySelector(".results-page");
  const loading = target.querySelector('[role="status"]');
  assert.ok(region);
  assert.equal(region.getAttribute("aria-busy"), "true");
  assert.ok(loading);
  assert.equal(loading.getAttribute("aria-live"), "polite");
  assert.match(loading.textContent, /Loading test results/);
  assertFirstPageRequest();
  const { signal } = harness.requests[0].options;

  await unmountFromDocument(component, target);
  assert.equal(signal.aborted, true);
});

void test("renders rows in the order received from the server using only the first page", async () => {
  assert.ok(harness);
  harness.resetApi();
  harness.setHandler(() =>
    Promise.resolve(
      makePage([makeRow(5, "server-newest"), makeRow(2, "server-next")]),
    ),
  );
  const { component, target } = mountInDocument();
  await settlePromises();

  assert.ok(target.querySelector(".sv-grid-root"), target.innerHTML);
  const resultRows = [...target.querySelectorAll("tbody tr.sv-grid-row")];
  assert.equal(resultRows.length, 2);
  assert.match(
    resultRows[0].textContent,
    new RegExp(
      [
        new Date("2026-01-02T03:04:05Z").toLocaleString(),
        "artefact-5",
        "server-newest",
        "category-5",
        "105",
        "PASSED",
        "stable-5",
        "1.5",
        "lab-5 / amd64-5",
        "smoke-5",
      ].join("[\\s\\S]*"),
    ),
  );
  assert.match(
    resultRows[1].textContent,
    new RegExp(
      [
        new Date("2026-01-02T03:04:05Z").toLocaleString(),
        "artefact-2",
        "server-next",
        "category-2",
        "102",
        "PASSED",
        "stable-2",
        "1.2",
        "lab-2 / amd64-2",
        "smoke-2",
      ].join("[\\s\\S]*"),
    ),
  );
  assert.deepEqual(
    [...target.querySelectorAll("thead th")].map((cell) =>
      cell.textContent.trim(),
    ),
    [
      "Created",
      "Artefact",
      "Test Case",
      "Category",
      "Test Execution ID",
      "Status",
      "Track",
      "Version",
      "Environment / Architecture",
      "Test Plan",
    ],
  );
  assert.equal(target.querySelectorAll('[aria-label^="Filter "]').length, 0);
  assert.equal(target.querySelectorAll('[role="checkbox"]').length, 0);
  assert.equal(resultRows[0].querySelectorAll("button").length, 0);

  resultRows[0].dispatchEvent(
    new browserWindow.MouseEvent("contextmenu", { bubbles: true }),
  );
  await settlePromises();
  assert.equal(target.querySelector('[role="menu"]'), null);
  assertFirstPageRequest();

  await unmountFromDocument(component, target);
});

void test("renders a clear empty state for an empty first page", async () => {
  assert.ok(harness);
  harness.resetApi();
  harness.setHandler(() => Promise.resolve(makePage([])));
  const { component, target } = mountInDocument();
  await settlePromises();

  assert.match(target.textContent, /No test results found/);
  assert.equal(target.querySelector(".sv-grid-root"), null);
  assertFirstPageRequest();

  await unmountFromDocument(component, target);
});

void test("shows a local failure and retries the same first-page endpoint", async () => {
  assert.ok(harness);
  harness.resetApi();
  let attempts = 0;
  harness.setHandler(() => {
    attempts += 1;
    return attempts === 1
      ? Promise.reject(new Error("backend unavailable"))
      : Promise.resolve(makePage([makeRow(4, "after-retry")]));
  });
  const { component, target } = mountInDocument();
  await settlePromises();

  assert.ok(target.querySelector('[role="alert"]'));
  assert.match(target.textContent, /could not be loaded/i);
  const retry = target.querySelector("button");
  assert.ok(retry);
  retry.click();
  assert.equal(harness.requests[0].options.signal.aborted, true);
  await settlePromises();

  assert.match(
    target.querySelector("tbody tr.sv-grid-row")?.textContent ?? "",
    /after-retry/,
  );
  assertFirstPageRequest();
  assert.equal(harness.requests.length, 2);
  assert.deepEqual(
    harness.requests.map((request) => request.path),
    [endpoint, endpoint],
  );

  await unmountFromDocument(component, target);
});
