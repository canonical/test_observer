// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0
import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { resolve } from "node:path";
import { build } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { Window } from "happy-dom";

/** @type {typeof import("./changelog-runtime-entry")} */
let harness;
/** @type {Window} */
let browserWindow;
/** @type {Map<string, PropertyDescriptor | undefined>} */
const originals = new Map();

before(async () => {
  const result = /** @type {{ output: { type: string; code: string }[] }[]} */ (
    /** @type {unknown} */ (
      await build({
        configFile: false,
        logLevel: "silent",
        plugins: [
          svelte({ compilerOptions: { runes: true } }),
          {
            name: "changelog-app",
            resolveId(id) {
              if (id.startsWith("$app/")) return `\0mock:${id}`;
            },
            load(id) {
              if (id === "\0mock:$app/state")
                return 'export const page = { url: new URL("https://example.test/base/items/3/changelog") };';
              if (id === "\0mock:$app/paths")
                return 'export const resolve = (path) => "/base/" + path.replace(/^\\//, "");';
            },
          },
        ],
        resolve: { alias: { $lib: resolve("src/lib") } },
        build: {
          write: false,
          lib: { entry: "tests/changelog-runtime-entry.js", formats: ["es"] },
          rolldownOptions: { output: { codeSplitting: false } },
        },
      })
    )
  );
  const bundle = result[0].output.find((item) => item.type === "chunk");
  assert.ok(bundle);
  browserWindow = new Window({
    url: "https://example.test/base/items/3/changelog",
  });
  for (const name of [
    "window",
    "document",
    "navigator",
    "Comment",
    "Text",
    "Node",
    "Element",
    "HTMLElement",
    "Event",
  ]) {
    originals.set(name, Object.getOwnPropertyDescriptor(globalThis, name));
    Object.defineProperty(globalThis, name, {
      configurable: true,
      value:
        name === "window" ? browserWindow : Reflect.get(browserWindow, name),
    });
  }
  originals.set("fetch", Object.getOwnPropertyDescriptor(globalThis, "fetch"));
  const importedModule = /** @type {unknown} */ (
    await import(
      `data:text/javascript;base64,${Buffer.from(bundle.code).toString("base64")}`
    )
  );
  harness = /** @type {typeof import("./changelog-runtime-entry")} */ (
    importedModule
  );
});

after(async () => {
  for (const [name, descriptor] of originals) {
    if (descriptor) Object.defineProperty(globalThis, name, descriptor);
    else Reflect.deleteProperty(globalThis, name);
  }
  await browserWindow.happyDOM.abort();
});

void test("loading, authorization, error and retry states stay distinct", async () => {
  const target = browserWindow.document.createElement("div");
  browserWindow.document.body.append(target);
  let mode = "forbidden";
  globalThis.fetch = async (input) => {
    await Promise.resolve();
    const url =
      typeof input === "string"
        ? input
        : input instanceof URL
          ? input.href
          : input.url;
    if (url.endsWith("/users/me")) {
      if (mode === "login") return new Response(null, { status: 401 });
      return Response.json({ id: 1, is_admin: false, teams: [] });
    }
    if (mode === "forbidden" || mode === "login")
      return new Response(null, { status: 403 });
    if (mode === "error") return new Response(null, { status: 500 });
    if (url.includes("/audit/"))
      return Response.json({ entries: [], count: 0, limit: 50, offset: 0 });
    return Response.json({ family: "generic" });
  };
  // @ts-expect-error Happy DOM's element differs from the DOM lib type.
  const component = harness.mountPage(target, undefined);
  harness.flushSync();
  assert.match(target.textContent, /Loading changelog/);
  /** @param {string} text */
  const waitFor = async (text) => {
    for (let i = 0; i < 50 && !target.textContent.includes(text); i++) {
      await new Promise((resolve) => setTimeout(resolve, 5));
      harness.flushSync();
    }
    assert.match(target.textContent, new RegExp(text));
  };
  await waitFor("permission");
  await harness.unmount(component);

  mode = "login";
  // @ts-expect-error Happy DOM's element differs from the DOM lib type.
  const login = harness.mountPage(target, undefined);
  await waitFor("logged in");
  const loginLink = target.querySelector('a[href*="/v1/auth/saml/login"]');
  assert.ok(loginLink);
  assert.match(loginLink.getAttribute("href") ?? "", /return_to=/);
  await harness.unmount(login);

  mode = "error";
  // @ts-expect-error Happy DOM's element differs from the DOM lib type.
  const error = harness.mountPage(target, undefined);
  await waitFor("Could not load");
  mode = "success";
  const retry = target.querySelector("button");
  assert.ok(retry);
  retry.click();
  await waitFor("No changelog entries");
  assert.equal(
    target.querySelector("a")?.getAttribute("href"),
    "/base/items/3",
  );
  await harness.unmount(error);
  target.remove();
});

void test("detail shows auth, missing and retry states and renders a snapshot", async () => {
  const target = browserWindow.document.createElement("div");
  browserWindow.document.body.append(target);
  let mode = "login";
  globalThis.fetch = async (input) => {
    await Promise.resolve();
    const url =
      typeof input === "string"
        ? input
        : input instanceof URL
          ? input.href
          : input.url;
    if (url.endsWith("/users/me")) {
      if (mode === "login") return new Response(null, { status: 401 });
      return Response.json({ id: 1, is_admin: false, teams: [] });
    }
    if (mode === "login" || mode === "forbidden")
      return new Response(null, { status: 403 });
    if (mode === "error") return new Response(null, { status: 500 });
    if (url.endsWith("/environment-reviews")) return Response.json([{ id: 8 }]);
    if (url.includes("/audit/")) {
      if (mode === "missing") return new Response(null, { status: 404 });
      return Response.json({
        id: 12,
        operation: "U",
        created_at: "2026-01-01T00:00:00Z",
        author: { name: "Alice", kind: "user" },
        data: {
          empty: "",
          nothing: null,
          enabled: false,
          count: 0,
          nested: { list: [1, null] },
        },
      });
    }
    return Response.json({ family: "generic" });
  };
  /** @param {string} text */
  const waitFor = async (text) => {
    for (let i = 0; i < 50 && !target.textContent.includes(text); i++) {
      await new Promise((resolve) => setTimeout(resolve, 5));
      harness.flushSync();
    }
    assert.ok(target.textContent.includes(text), target.textContent);
  };
  for (const [current, expected] of [
    ["login", "logged in"],
    ["forbidden", "permission"],
    ["missing", "not found"],
  ]) {
    mode = current;
    // @ts-expect-error Happy DOM's element differs from the DOM lib type.
    const component = harness.mountDetail(target, 8);
    await waitFor(expected);
    await harness.unmount(component);
  }
  mode = "error";
  // @ts-expect-error Happy DOM's element differs from the DOM lib type.
  const component = harness.mountDetail(target, 8);
  harness.flushSync();
  assert.match(target.textContent, /Loading changelog detail/);
  await waitFor("Could not load");
  mode = "success";
  target.querySelector("button")?.click();
  await waitFor("Alice (user)");
  assert.equal(
    target.querySelector("a")?.getAttribute("href"),
    "/base/items/3/environments/8/changelog",
  );
  assert.ok(
    [...target.querySelectorAll("button")].some(
      (button) => button.textContent === "JSON",
    ),
  );
  const rows = [...target.querySelectorAll("tbody tr")].map((row) =>
    [...row.querySelectorAll("td")].map((cell) => cell.textContent),
  );
  assert.deepEqual(rows, [
    ["empty", ""],
    ["nothing", "null"],
    ["enabled", "false"],
    ["count", "0"],
    ["nested", '{"list":[1,null]}'],
  ]);
  await harness.unmount(component);
  target.remove();
});

void test("detail ignores a response for a previous audit ID", async () => {
  const target = browserWindow.document.createElement("div");
  browserWindow.document.body.append(target);
  /** @type {((value: Response) => void) | undefined} */
  let resolveOld;
  const makeEntry = (/** @type {number} */ id) =>
    Response.json({
      id,
      operation: "U",
      created_at: "2026-01-01T00:00:00Z",
      author: { name: "Alice", kind: "user" },
      data: { marker: `entry-${id}` },
    });
  globalThis.fetch = (input) => {
    const url =
      typeof input === "string"
        ? input
        : input instanceof URL
          ? input.href
          : input.url;
    if (url.endsWith("/audit/artefacts/3/12"))
      return new Promise((resolve) => {
        resolveOld = resolve;
      });
    if (url.endsWith("/audit/artefacts/3/13"))
      return Promise.resolve(makeEntry(13));
    return Promise.resolve(Response.json({ family: "generic" }));
  };
  // @ts-expect-error Happy DOM's element differs from the DOM lib type.
  const { component, setAuditId } = harness.mountReactiveDetail(target);
  harness.flushSync();
  for (let i = 0; i < 50 && !resolveOld; i++)
    await new Promise((resolve) => setTimeout(resolve, 5));
  assert.ok(resolveOld);
  setAuditId(13);
  harness.flushSync();
  for (let i = 0; i < 50 && !target.textContent.includes("entry-13"); i++) {
    await new Promise((resolve) => setTimeout(resolve, 5));
    harness.flushSync();
  }
  assert.match(target.textContent, /entry-13/);
  resolveOld(makeEntry(12));
  await new Promise((resolve) => setTimeout(resolve, 10));
  harness.flushSync();
  assert.match(target.textContent, /entry-13/);
  assert.doesNotMatch(target.textContent, /entry-12/);
  await harness.unmount(component);
  target.remove();
});

void test("JSON actions use authenticated requests, handle failures and release resources", async () => {
  const target = browserWindow.document.createElement("div");
  browserWindow.document.body.append(target);
  const originalOpen = Object.getOwnPropertyDescriptor(browserWindow, "open");
  const originalCreate = Object.getOwnPropertyDescriptor(
    URL,
    "createObjectURL",
  );
  const originalRevoke = Object.getOwnPropertyDescriptor(
    URL,
    "revokeObjectURL",
  );
  const originalTimeout = globalThis.setTimeout;
  /** @type {(() => void)[]} */
  const cleanup = [];
  /** @type {string[]} */
  const revoked = [];
  /** @type {Blob[]} */
  const blobs = [];
  /** @type {{url: string, options: RequestInit | undefined}[]} */
  const requests = [];
  let mode = "success";
  let opened = 0;
  let openedAtClick = 0;
  let closed = 0;
  let navigated = "";
  /** @type {{resolve?: (value: Response) => void}} */
  const pendingJson = {};
  browserWindow.open = /** @type {typeof browserWindow.open} */ (
    /** @type {unknown} */ (
      () => {
        opened++;
        if (mode === "blocked") return null;
        return {
          opener: window,
          closed: false,
          close: () => closed++,
          location: {
            replace: (/** @type {string} */ url) => {
              if (mode === "navigation") throw new Error("navigation failed");
              navigated = url;
            },
          },
        };
      }
    )
  );
  URL.createObjectURL = (blob) => {
    blobs.push(/** @type {Blob} */ (blob));
    return `blob:test-${blobs.length}`;
  };
  URL.revokeObjectURL = (url) => revoked.push(url);
  globalThis.setTimeout = /** @type {typeof setTimeout} */ (
    /** @type {unknown} */ (
      (/** @type {() => void} */ callback, /** @type {number} */ delay) => {
        if (delay === 60_000) {
          cleanup.push(callback);
          return 0;
        }
        return originalTimeout(callback, delay);
      }
    )
  );
  const entry = {
    id: 12,
    operation: "U",
    created_at: "2026-01-01T00:00:00Z",
    author: { name: "Alice", kind: "user" },
    data: { marker: "snapshot" },
  };
  globalThis.fetch = async (input, options) => {
    const url =
      typeof input === "string"
        ? input
        : input instanceof URL
          ? input.href
          : input.url;
    requests.push({ url, options });
    if (url.endsWith("/environment-reviews")) return Response.json([{ id: 8 }]);
    if (!url.includes("/audit/")) return Response.json({ family: "generic" });
    if (url.includes("?limit="))
      return Response.json({
        entries: [entry],
        count: 1,
        limit: 50,
        offset: 0,
      });
    if (mode === "pending") {
      assert.ok(opened > openedAtClick, "tab must open before fetching");
      return new Promise((resolve) => {
        pendingJson.resolve = resolve;
      });
    }
    if (mode === "network") throw new Error("network");
    if (mode === "auth") return new Response(null, { status: 401 });
    if (mode === "server") return new Response(null, { status: 500 });
    return Response.json(entry);
  };
  /** @param {() => boolean} condition */
  const waitFor = async (condition) => {
    for (let i = 0; i < 50 && !condition(); i++) {
      await new Promise((resolve) => setTimeout(resolve, 5));
      harness.flushSync();
    }
    assert.ok(condition(), target.textContent);
  };
  try {
    for (const detail of [false, true]) {
      for (const reviewId of [undefined, 8]) {
        mode = "success";
        const component = detail
          ? // @ts-expect-error Happy DOM's element differs from the DOM lib type.
            harness.mountDetail(target, reviewId)
          : // @ts-expect-error Happy DOM's element differs from the DOM lib type.
            harness.mountPage(target, reviewId);
        await waitFor(() => target.textContent.includes("Alice"));
        const button = [...target.querySelectorAll("button")].find(
          (item) => item.textContent === "JSON",
        );
        assert.ok(button);
        requests.length = 0;
        mode = "pending";
        openedAtClick = opened;
        button.click();
        harness.flushSync();
        assert.ok(button.disabled);
        assert.match(target.textContent, /Loading JSON/);
        assert.ok(pendingJson.resolve);
        assert.equal(requests.length, 1);
        assert.equal(
          requests[0].url,
          `http://localhost:30000/v1/audit/${reviewId === undefined ? "artefacts/3" : "environment-reviews/8"}/12`,
        );
        assert.equal(requests[0].options?.credentials, "include");
        assert.equal(
          new Headers(requests[0].options.headers).get("X-CSRF-Token"),
          "1",
        );
        pendingJson.resolve(Response.json(entry));
        await waitFor(() => !button.disabled);
        assert.equal(navigated, `blob:test-${blobs.length}`);
        const blob = blobs.at(-1);
        assert.ok(blob);
        assert.deepEqual(JSON.parse(await blob.text()), entry);
        assert.ok(!revoked.includes(navigated));
        cleanup.shift()?.();
        assert.ok(revoked.includes(navigated));
        await harness.unmount(component);
      }
    }

    mode = "success";
    // @ts-expect-error Happy DOM's element differs from the DOM lib type.
    const component = harness.mountPage(target, undefined);
    await waitFor(() => target.textContent.includes("Alice"));
    const button = [...target.querySelectorAll("button")].find(
      (item) => item.textContent === "JSON",
    );
    assert.ok(button);
    for (const failure of [
      "blocked",
      "auth",
      "server",
      "network",
      "navigation",
    ]) {
      mode = failure;
      requests.length = 0;
      const previousClosed = closed;
      button.click();
      harness.flushSync();
      await waitFor(() => target.querySelector('[role="alert"]') !== null);
      if (failure === "blocked") {
        assert.match(target.textContent, /allow pop-ups/);
        assert.equal(requests.length, 0);
        assert.equal(closed, previousClosed);
      } else {
        assert.equal(closed, previousClosed + 1);
        if (failure === "auth") assert.match(target.textContent, /permission/);
        if (failure === "navigation")
          assert.ok(revoked.includes(`blob:test-${blobs.length}`));
      }
    }
    mode = "pending";
    openedAtClick = opened;
    button.click();
    harness.flushSync();
    const previousClosed = closed;
    await harness.unmount(component);
    assert.equal(closed, previousClosed + 1);
    assert.ok(requests.at(-1)?.options?.signal?.aborted);
    pendingJson.resolve?.(Response.json(entry));
    await Promise.resolve();
  } finally {
    if (originalOpen)
      Object.defineProperty(browserWindow, "open", originalOpen);
    else Reflect.deleteProperty(browserWindow, "open");
    if (originalCreate)
      Object.defineProperty(URL, "createObjectURL", originalCreate);
    else Reflect.deleteProperty(URL, "createObjectURL");
    if (originalRevoke)
      Object.defineProperty(URL, "revokeObjectURL", originalRevoke);
    else Reflect.deleteProperty(URL, "revokeObjectURL");
    globalThis.setTimeout = originalTimeout;
    target.remove();
  }
});
