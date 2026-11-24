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
  const component = harness.mountPage(target);
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
  const login = harness.mountPage(target);
  await waitFor("logged in");
  const loginLink = target.querySelector('a[href*="/v1/auth/saml/login"]');
  assert.ok(loginLink);
  assert.match(loginLink.getAttribute("href") ?? "", /return_to=/);
  await harness.unmount(login);

  mode = "error";
  // @ts-expect-error Happy DOM's element differs from the DOM lib type.
  const error = harness.mountPage(target);
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
  const json = target.querySelector('a[target="_blank"]');
  assert.equal(
    json?.getAttribute("href"),
    "http://localhost:30000/v1/audit/environment-reviews/8/12",
  );
  assert.equal(json.getAttribute("rel"), "noopener noreferrer");
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
