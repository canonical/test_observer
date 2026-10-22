// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0
/* eslint-disable
  @typescript-eslint/no-unsafe-member-access,
  @typescript-eslint/no-unsafe-argument,
  @typescript-eslint/no-unsafe-call,
  @typescript-eslint/no-unsafe-return,
  @typescript-eslint/require-await,
  @typescript-eslint/no-unnecessary-condition
*/

import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { resolve } from "node:path";
import { build, createServer } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { Window } from "happy-dom";

/** @type {import("vite").ViteDevServer | undefined} */
let vite;
/** @type {typeof import("../src/routes/[family]/+page").load | undefined} */
let loadFamilyPage;
/** @type {typeof import("./family-page-entry") | undefined} */
let harness;
/** @type {Window | undefined} */
let browserWindow;
/** @type {Map<string, PropertyDescriptor | undefined>} */
const originalGlobals = new Map();

const family = {
  name: "snaps",
  api_name: "snap",
  stages: [],
  columns: [],
  filters: [],
};

before(async () => {
  vite = await createServer({
    configFile: "vite.config.ts",
    appType: "custom",
    logLevel: "silent",
    server: { middlewareMode: true },
  });
  ({ load: loadFamilyPage } = await vite.ssrLoadModule(
    "/src/routes/[family]/+page.ts",
  ));

  const buildResult =
    /** @type {{ output: { type: string; code: string }[] }[]} */ (
      /** @type {unknown} */ (
        await build({
          configFile: false,
          logLevel: "silent",
          plugins: [
            svelte({ compilerOptions: { runes: true } }),
            {
              name: "family-page-app-apis",
              resolveId(id) {
                if (id === "$app/paths") return "\0family-page-paths";
                if (id === "$app/env") return "\0family-page-env";
              },
              load(id) {
                if (id === "\0family-page-paths") {
                  return 'export const base = ""; export const resolve = (path) => path;';
                }
                if (id === "\0family-page-env")
                  return "export const browser = true;";
              },
            },
          ],
          resolve: {
            alias: [
              {
                find: "$lib/components/dashboard/DashboardHeader.svelte",
                replacement: resolve("tests/family-page-header.svelte"),
              },
              {
                find: "$lib/components/dashboard/ArtefactTable.svelte",
                replacement: resolve("tests/family-page-table.svelte"),
              },
              {
                find: "$app/state",
                replacement: resolve("tests/family-page-state.svelte.js"),
              },
              {
                find: "$app/navigation",
                replacement: resolve("tests/family-page-navigation.js"),
              },
              { find: "$lib", replacement: resolve("src/lib") },
            ],
          },
          build: {
            write: false,
            lib: {
              entry: "tests/family-page-entry.js",
              formats: ["es"],
            },
            rolldownOptions: { output: { codeSplitting: false } },
          },
        })
      )
    );
  const bundle = buildResult[0]?.output.find((item) => item.type === "chunk");
  assert.ok(bundle, "family page test bundle should be generated");

  browserWindow = new Window({ url: "http://localhost/snaps" });
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
    "FocusEvent",
    "getComputedStyle",
    "requestAnimationFrame",
    "ResizeObserver",
    "customElements",
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
  harness = /** @type {typeof import("./family-page-entry")} */ (
    importedModule
  );
});

after(async () => {
  await vite?.close();
  for (const [name, descriptor] of originalGlobals) {
    if (descriptor) Object.defineProperty(globalThis, name, descriptor);
    else Reflect.deleteProperty(globalThis, name);
  }
  await browserWindow?.happyDOM.abort();
});

function deferred() {
  /** @type {((value: Response) => void) | undefined} */
  let resolvePromise;
  /** @type {((reason?: unknown) => void) | undefined} */
  let rejectPromise;
  const promise = /** @type {Promise<Response>} */ (
    new Promise((resolve, reject) => {
      resolvePromise = resolve;
      rejectPromise = reject;
    })
  );
  return {
    promise,
    /** @param {Response} response */
    resolve(response) {
      if (!resolvePromise) throw new Error("Promise resolver is not set");
      resolvePromise(response);
    },
    /** @param {unknown} reason */
    reject(reason) {
      if (!rejectPromise) throw new Error("Promise rejecter is not set");
      rejectPromise(reason);
    },
  };
}

/** @param {unknown} body @param {number} [status] */
function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

/** @param {string | URL | Request} input */
function requestUrl(input) {
  return new URL(input instanceof Request ? input.url : input.toString());
}

const flush = () => new Promise((resolve) => setTimeout(resolve, 0));

void test("family navigation returns before artefacts and renders a content wait state", async () => {
  if (!loadFamilyPage || !harness || !browserWindow) {
    throw new Error("Family page test modules were not loaded");
  }
  const delayedResponse = deferred();
  let requestOptions;
  let requestStarted = false;
  const loading = loadFamilyPage({
    parent: async () => ({ artefactFamilies: [family] }),
    params: { family: "snaps" },
    fetch: (input, options) => {
      requestStarted = true;
      requestOptions = { url: requestUrl(input), options };
      return delayedResponse.promise;
    },
  });
  const data = await loading;

  assert.equal(requestStarted, true);
  assert.equal(
    requestOptions?.url.href,
    "http://localhost:30000/v1/artefacts?family=snap",
  );
  assert.equal(requestOptions?.options?.credentials, "include");
  assert.equal(requestOptions?.options?.headers?.["X-CSRF-Token"], "1");
  assert.equal(data.family, family);
  assert.equal(typeof data.artefacts?.then, "function");

  const target = browserWindow.document.createElement("div");
  browserWindow.document.body.append(target);
  const component = harness.mountFamilyPage(target, data);
  try {
    // The route's synchronous data is ready for SvelteKit to update the public
    // URL while the returned artefact promise is intentionally unresolved.
    harness.setPageUrl("/snaps");
    assert.equal(harness.page.url.pathname, "/snaps");
    assert.match(target.querySelector("h1")?.textContent ?? "", /snaps/i);
    assert.match(target.textContent, /Loading test results/);
    assert.ok(target.querySelector('[role="status"][aria-live="polite"]'));
    assert.equal(
      target.querySelector(".count"),
      null,
      "pending count is unknown, not zero",
    );
    assert.equal(target.querySelector(".artefact-table"), null);

    const artefact = { id: 1, name: "One", reviewers: null };
    delayedResponse.resolve(jsonResponse([artefact]));
    await data.artefacts;
    await flush();
    harness.flushSync();

    assert.equal(target.querySelector('[role="status"]'), null);
    assert.equal(target.querySelector(".count")?.textContent, "1 artifacts");
    assert.equal(
      target.querySelector(".artefact-table")?.getAttribute("data-count"),
      "1",
    );
    assert.deepEqual(await data.artefacts, {
      kind: "loaded",
      artefacts: [{ ...artefact, reviewers: [] }],
    });
  } finally {
    await harness.unmountFamilyPage(component);
    target.remove();
  }
});

void test("family route preserves login, forbidden and session-check states", async () => {
  if (!loadFamilyPage || !harness || !browserWindow) {
    throw new Error("Family page test modules were not loaded");
  }
  const cases = [
    { pageStatus: 401, sessionStatus: 401, expected: "requiresLogin" },
    { pageStatus: 403, sessionStatus: 200, expected: "forbidden" },
    { pageStatus: 401, sessionStatus: 503, expected: "sessionCheckFailed" },
  ];
  for (const testCase of cases) {
    const data = await loadFamilyPage({
      parent: async () => ({ artefactFamilies: [family] }),
      params: { family: "snaps" },
      fetch: (input) => {
        const url = requestUrl(input);
        if (url.pathname.endsWith("/users/me")) {
          return Promise.resolve(
            testCase.sessionStatus === 200
              ? jsonResponse({ id: 5, teams: [], is_admin: false })
              : new Response("{}", { status: testCase.sessionStatus }),
          );
        }
        return Promise.resolve(
          new Response("{}", { status: testCase.pageStatus }),
        );
      },
    });
    assert.deepEqual(await data.artefacts, { kind: testCase.expected });

    const target = browserWindow.document.createElement("div");
    browserWindow.document.body.append(target);
    const component = harness.mountFamilyPage(target, data);
    try {
      await flush();
      harness.flushSync();
      if (testCase.expected === "requiresLogin") {
        assert.match(target.textContent, /You need to be logged in/);
        assert.ok(target.querySelector('a.login-button[href*="saml/login"]'));
      } else if (testCase.expected === "forbidden") {
        assert.match(target.textContent, /don't have permission/);
        assert.ok(target.querySelector('[role="alert"]'));
      } else {
        assert.match(target.textContent, /couldn't verify your session/);
        assert.ok(target.querySelector(".session-check-failed button"));
        harness.resetRetries();
        target.querySelector(".session-check-failed button")?.click();
        assert.equal(
          harness.retryCount,
          1,
          "session retry invalidates route data",
        );
      }
      assert.equal(
        target.querySelector(".count"),
        null,
        "auth states do not imply zero artefacts",
      );
    } finally {
      await harness.unmountFamilyPage(component);
      target.remove();
    }
  }
});

void test("failed artefact request is visible and retryable; unknown families remain 404s", async () => {
  if (!loadFamilyPage || !harness || !browserWindow) {
    throw new Error("Family page test modules were not loaded");
  }
  let requested = false;
  await assert.rejects(
    loadFamilyPage({
      parent: async () => ({ artefactFamilies: [family] }),
      params: { family: "snaps" },
      fetch: () => {
        requested = true;
        return Promise.resolve(new Response("{}", { status: 500 }));
      },
    }).then(async (data) => data.artefacts),
    /Failed to load artefacts \(500\)/,
  );
  assert.equal(requested, true);

  requested = false;
  await assert.rejects(
    loadFamilyPage({
      parent: async () => ({ artefactFamilies: [family] }),
      params: { family: "unknown" },
      fetch: () => {
        requested = true;
        return Promise.resolve(jsonResponse([]));
      },
    }),
    (failure) => failure?.status === 404,
  );
  assert.equal(
    requested,
    false,
    "family validation happens before artefact fetch",
  );

  const pending = deferred();
  const target = browserWindow.document.createElement("div");
  browserWindow.document.body.append(target);
  const component = harness.mountFamilyPage(target, {
    family,
    artefacts: pending.promise,
  });
  try {
    pending.reject(new Error("network unavailable"));
    await flush();
    harness.flushSync();
    assert.match(target.textContent, /couldn't load these test results/i);
    assert.ok(target.querySelector(".request-failed[role='alert']"));
    assert.equal(target.querySelector(".count"), null);
    harness.resetRetries();
    target.querySelector(".request-failed button")?.click();
    assert.equal(harness.retryCount, 1, "request retry invalidates route data");
  } finally {
    await harness.unmountFamilyPage(component);
    target.remove();
  }
});
