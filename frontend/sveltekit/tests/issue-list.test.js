// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0
/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-argument, @typescript-eslint/no-unsafe-return */
/* eslint-disable @typescript-eslint/require-await -- Mock fetches intentionally resolve fixture responses. */
import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { resolve } from "node:path";
import { build } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { Window } from "happy-dom";

let app;
let browser;
const descriptors = new Map();
const originalFetch = globalThis.fetch;
const flush = () => new Promise((resolve) => setTimeout(resolve, 15));
const filters = (projects = []) => ({
  sources: [],
  statuses: ["open", "unknown"],
  families: [],
  projects,
  query: "",
});
const row = (id, project = "A") => ({
  id,
  source: "github",
  project,
  key: String(id),
  title: `Issue ${id}`,
  status: "open",
  url: `https://example.invalid/${id}`,
});
const response = (rows, count = rows.length, offset = 0) =>
  new Response(JSON.stringify({ issues: rows, count, offset, limit: 50 }));
function deferred() {
  let release;
  const promise = new Promise((resolve) => (release = resolve));
  return { promise, release: (value) => release(value) };
}

before(async () => {
  browser = new Window({ url: "http://localhost" });
  for (const key of [
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
    "HTMLInputElement",
    "getComputedStyle",
    "requestAnimationFrame",
    "cancelAnimationFrame",
  ]) {
    descriptors.set(key, Object.getOwnPropertyDescriptor(globalThis, key));
    const value = browser[key];
    Object.defineProperty(globalThis, key, {
      configurable: true,
      value:
        typeof value === "function" && !/^[A-Z]/.test(key)
          ? value.bind(browser)
          : value,
    });
  }
  const built = await build({
    configFile: false,
    logLevel: "silent",
    plugins: [svelte({ configFile: false })],
    resolve: { alias: { $lib: resolve("src/lib") }, conditions: ["browser"] },
    build: {
      write: false,
      lib: { entry: "tests/issue-list-entry.svelte.js", formats: ["es"] },
      rolldownOptions: { output: { codeSplitting: false } },
    },
  });
  const bundle = built[0].output.find((item) => item.type === "chunk");
  app = await import(
    `data:text/javascript;base64,${Buffer.from(bundle.code).toString("base64")}`
  );
});

after(() => {
  globalThis.fetch = originalFetch;
  for (const [key, descriptor] of descriptors) {
    if (descriptor) Object.defineProperty(globalThis, key, descriptor);
    else Reflect.deleteProperty(globalThis, key);
  }
  void browser.happyDOM.abort();
});

void test("independent result/facet pages keep raw offsets, deduplicate, retry locally and reset the result project", async () => {
  let resultScope = "A";
  const results = new app.IssueListPages(() => resultScope);
  const facets = new app.IssueListPages(() => "facets");
  const calls = [];
  let fail = true;
  globalThis.fetch = async (input) => {
    const params = new URL(input).searchParams;
    calls.push(params);
    const offset = Number(params.get("offset"));
    if (!params.has("project") && offset === 2 && fail)
      return new Response(JSON.stringify({ detail: "Facet denied" }), {
        status: 403,
      });
    return response(
      offset ? [row(2), row(3, "B")] : [row(1), row(2)],
      4,
      offset,
    );
  };
  await Promise.all([
    results.reset(filters(["A"]), "A"),
    facets.reset(filters(), "facets"),
  ]);
  await facets.more();
  assert.equal(facets.error, "Facet denied");
  assert.equal(results.error, "");
  assert.deepEqual(
    results.rows.map((item) => item.id),
    [1, 2],
  );
  fail = false;
  await facets.retry();
  assert.equal(facets.nextOffset, 4);
  assert.equal(facets.hasMore, false);
  assert.deepEqual(
    facets.rows.map((item) => item.id),
    [1, 2, 3],
  );
  resultScope = "A+B";
  await results.reset(filters(["A", "B"]), resultScope);
  assert.equal(calls.at(-1).has("project"), false);
  assert.equal(calls.at(-1).get("offset"), "0");
  await results.more();
  assert.equal(calls.at(-1).get("offset"), "2");
  assert.equal(results.nextOffset, 4);
  assert.equal(
    facets.nextOffset,
    4,
    "result selection never resets facet progress",
  );
  results.dispose();
  facets.dispose();
});

void test("superseded successes cannot replace new scope pages, counts or loading state", async () => {
  let scope = "A";
  const stream = new app.IssueListPages(() => scope);
  const old = deferred();
  globalThis.fetch = () => old.promise;
  const pending = stream.reset(filters(), scope);
  scope = "B";
  globalThis.fetch = async () => response([row(22, "new")]);
  await stream.reset(filters(), scope);
  old.release(response([row(1, "obsolete")], 900));
  await pending;
  assert.deepEqual(
    stream.rows.map((item) => item.project),
    ["new"],
  );
  assert.equal(stream.totalCount, 1);
  assert.equal(stream.initialLoading, false);
  assert.equal(stream.error, "");
  stream.dispose();
});

void test("an old load-more success cannot append to a new facet/query scope", async () => {
  let scope = "old";
  const stream = new app.IssueListPages(() => scope);
  globalThis.fetch = async () => response([row(1)], 20);
  await stream.reset(filters(), scope);
  const laterPage = deferred();
  globalThis.fetch = () => laterPage.promise;
  const pending = stream.more();
  scope = "new";
  globalThis.fetch = async () => response([row(9, "new")]);
  await stream.reset({ ...filters(), query: "new" }, scope);
  laterPage.release(response([row(2, "obsolete")], 500, 1));
  await pending;
  assert.deepEqual(
    stream.rows.map((item) => item.id),
    [9],
  );
  assert.equal(stream.totalCount, 1);
  assert.equal(stream.nextOffset, 1);
  assert.equal(stream.loadingMore, false);
  stream.dispose();
});

void test("parsed late errors cannot cross A/B/A generations, session changes or disposal", async () => {
  for (const transition of ["A/B/A", "session", "dispose"]) {
    let scope = "A";
    const stream = new app.IssueListPages(() => scope);
    const body = deferred();
    const failure = new Response("", { status: 503 });
    failure.json = () => body.promise;
    globalThis.fetch = async () => failure;
    const pending = stream.reset(filters(), scope);
    await flush();
    if (transition === "A/B/A") {
      globalThis.fetch = async () => response([row(4)]);
      scope = "B";
      await stream.reset(filters(), scope);
      scope = "A";
      await stream.reset(filters(), scope);
    } else if (transition === "session") {
      scope = "session-2"; // Even before a reactive reset executes.
    } else stream.dispose();
    body.release({ detail: "Obsolete parsed error" });
    await pending;
    assert.equal(stream.error, "", transition);
    if (transition === "A/B/A") assert.equal(stream.rows[0].id, 4);
    stream.dispose();
  }
});

void test("pending success after unmount or session invalidation cannot populate either stream", async () => {
  for (const transition of ["session", "dispose"]) {
    let scope = "session-1";
    const streams = [
      new app.IssueListPages(() => scope),
      new app.IssueListPages(() => scope),
    ];
    const late = deferred();
    globalThis.fetch = () => late.promise;
    const pending = streams.map((stream) => stream.reset(filters(), scope));
    if (transition === "session") scope = "session-2";
    else streams.forEach((stream) => stream.dispose());
    late.release(response([row(100)], 500));
    await Promise.all(pending);
    for (const stream of streams) {
      assert.equal(stream.rows.length, 0);
      assert.equal(stream.totalCount, 0);
      stream.dispose();
    }
  }
});

void test("mounted Pragma picker filters substrings without applying them, retains selected unloaded values and removes with stable focus", async () => {
  const target = document.createElement("div");
  document.body.append(target);
  const component = app.mount(app.Picker, { target });
  try {
    app.flushSync();
    const search = target.querySelector("#project-search");
    assert.ok(search.classList.contains("ds"));
    assert.equal(target.querySelectorAll('input[type="checkbox"]').length, 3);
    search.value = "PHA/";
    search.dispatchEvent(new Event("input", { bubbles: true }));
    app.flushSync();
    assert.equal(target.querySelectorAll('input[type="checkbox"]').length, 1);
    const option = target.querySelector('input[type="checkbox"]');
    assert.equal(option.value, "Alpha/project");
    option.click();
    app.flushSync();
    assert.equal(
      target.querySelectorAll(".selected-projects button").length,
      2,
    );
    const remove = target.querySelector(
      '[aria-label="Remove project unloaded/project"]',
    );
    remove.focus();
    remove.click();
    app.flushSync();
    assert.equal(document.activeElement, search);
    assert.equal(search.value, "PHA/");
    assert.equal(
      target.querySelectorAll(".selected-projects button").length,
      1,
    );
    assert.equal(target.querySelector("select"), null);
  } finally {
    await app.unmount(component);
    target.remove();
  }
});

function pendingPicker() {
  const target = document.createElement("div");
  const elsewhere = document.createElement("input");
  elsewhere.setAttribute("aria-label", "Another control");
  target.append(elsewhere);
  document.body.append(target);
  const pending = [];
  const listeners = new Set();
  const descriptors = new Map(
    ["addEventListener", "removeEventListener"].map((name) => [
      name,
      Object.getOwnPropertyDescriptor(document, name),
    ]),
  );
  const add = document.addEventListener.bind(document);
  const remove = document.removeEventListener.bind(document);
  document.addEventListener = (name, listener, options) => {
    if (name === "focusin" && options === true) listeners.add(listener);
    add(name, listener, options);
  };
  document.removeEventListener = (name, listener, options) => {
    if (name === "focusin" && options === true) listeners.delete(listener);
    remove(name, listener, options);
  };
  const component = app.mount(app.Picker, {
    target,
    props: {
      ontoggle: () => {
        const request = deferred();
        pending.push(request);
        return request.promise;
      },
    },
  });
  app.flushSync();
  let unmounted = false;
  const unmount = async () => {
    if (!unmounted) {
      unmounted = true;
      await app.unmount(component);
    }
  };
  return {
    target,
    elsewhere,
    pending,
    listeners,
    unmount,
    alpha: target.querySelector('input[value="Alpha/project"]'),
    beta: target.querySelector('input[value="Beta/project"]'),
    search: target.querySelector("#project-search"),
    cleanup: async () => {
      try {
        await unmount();
        pending.forEach((request) => request.release());
        await flush();
        assert.equal(
          listeners.size,
          0,
          "pending focus listeners must be released",
        );
      } finally {
        for (const [name, descriptor] of descriptors) {
          if (descriptor) Object.defineProperty(document, name, descriptor);
          else Reflect.deleteProperty(document, name);
        }
        target.remove();
      }
    },
  };
}

void test("mounted picker cancels restoration on intervening focus intent even when navigation later leaves body focused", async () => {
  const f = pendingPicker();
  try {
    f.alpha.focus();
    f.alpha.click();
    assert.equal(f.pending.length, 1);
    f.elsewhere.focus();
    assert.ok(
      document.activeElement === f.elsewhere,
      "the deliberate second focus really succeeded",
    );
    f.elsewhere.blur();
    assert.ok(
      document.activeElement === document.body,
      "model the later navigation-only blur",
    );
    f.pending[0].release();
    await flush();
    assert.ok(
      document.activeElement === document.body,
      "old checkbox must not steal focus after the intervening intent",
    );
    assert.equal(f.listeners.size, 0);
  } finally {
    await f.cleanup();
  }
});

void test("mounted picker restores owned checkbox and removal-search focus after navigation-only blur and cleans up", async () => {
  for (const action of ["checkbox", "removal"]) {
    const f = pendingPicker();
    try {
      const input = action === "checkbox" ? f.alpha : f.search;
      if (action === "checkbox") {
        f.alpha.focus();
        f.alpha.click();
      } else {
        const remove = f.target.querySelector(
          '[aria-label="Remove project unloaded/project"]',
        );
        remove.focus();
        remove.click();
        assert.ok(document.activeElement === f.search);
      }
      input.blur();
      assert.ok(document.activeElement === document.body);
      f.pending[0].release();
      await flush();
      assert.ok(document.activeElement === input, action);
      assert.equal(f.listeners.size, 0);
    } finally {
      await f.cleanup();
    }
  }
});

void test("mounted picker hidden or unmounted during pending navigation never restores focus or leaks listeners", async () => {
  for (const action of ["hide", "unmount"]) {
    const f = pendingPicker();
    try {
      f.alpha.focus();
      f.alpha.click();
      f.alpha.blur();
      if (action === "hide") f.target.hidden = true;
      else {
        await f.unmount();
        assert.equal(
          f.listeners.size,
          0,
          "unmount must remove the listener before the parent promise settles",
        );
      }
      f.pending[0].release();
      await flush();
      assert.ok(document.activeElement === document.body, action);
      assert.equal(f.listeners.size, 0);
    } finally {
      await f.cleanup();
    }
  }
});

void test("mounted picker superseding intent owns restoration and old completion cannot cancel the new owner", async () => {
  const f = pendingPicker();
  try {
    f.alpha.focus();
    f.alpha.click();
    f.beta.focus();
    f.beta.click();
    assert.equal(f.pending.length, 2);
    f.beta.blur();
    f.pending[0].release();
    await flush();
    assert.ok(
      document.activeElement === document.body,
      "superseded Alpha must not restore",
    );
    f.pending[1].release();
    await flush();
    assert.ok(
      document.activeElement === f.beta,
      "newest checkbox still owns navigation-only restoration",
    );
    assert.equal(f.listeners.size, 0);
  } finally {
    await f.cleanup();
  }
});
