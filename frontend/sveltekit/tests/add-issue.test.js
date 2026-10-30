// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0
/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-argument, @typescript-eslint/no-unsafe-return */
/* eslint-disable @typescript-eslint/require-await -- Mock fetches deliberately resolve Responses. */
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
const json = (body, status = 200) =>
  new Response(JSON.stringify(body), { status });
const url = "https://github.com/canonical/test-observer/issues/7";
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
    "HTMLDialogElement",
    "Element",
    "Node",
    "Text",
    "Comment",
    "Event",
    "MouseEvent",
    "CustomEvent",
    "HTMLInputElement",
    "HTMLMediaElement",
    "HTMLSelectElement",
    "HTMLTextAreaElement",
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
  // Test-only adapter: no native focus containment/layout claims in Happy DOM.
  const toggle = (oldState, newState) =>
    Object.assign(new Event("toggle"), { oldState, newState });
  browser.HTMLDialogElement.prototype.showModal = function () {
    if (this.open) return;
    this.open = true;
    this.dispatchEvent(toggle("closed", "open"));
  };
  browser.HTMLDialogElement.prototype.close = function () {
    if (!this.open) return;
    this.open = false;
    this.dispatchEvent(toggle("open", "closed"));
    setTimeout(() => this.dispatchEvent(new Event("close")));
  };
  const built = await build({
    configFile: false,
    logLevel: "silent",
    plugins: [svelte({ configFile: false })],
    resolve: { alias: { $lib: resolve("src/lib") }, conditions: ["browser"] },
    build: {
      write: false,
      lib: { entry: "tests/add-issue-entry.svelte.js", formats: ["es"] },
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

function fixture() {
  const target = document.createElement("div");
  document.body.append(target);
  let current = true;
  const added = [];
  const component = app.mount(app.AddIssue, {
    target,
    props: {
      getContext: () => (current ? "A" : "B"),
      onadded: (id) => added.push(id),
    },
  });
  app.flushSync();
  const trigger = target.querySelector("button");
  const show = () => {
    trigger.click();
    app.flushSync();
  };
  show();
  const form = target.querySelector("form");
  const input = target.querySelector("input");
  const fill = (value) => {
    input.value = value;
    input.dispatchEvent(new Event("input", { bubbles: true }));
    app.flushSync();
  };
  const submit = () =>
    form.dispatchEvent(
      new Event("submit", { bubbles: true, cancelable: true }),
    );
  return {
    target,
    added,
    trigger,
    form,
    input,
    fill,
    submit,
    show,
    invalidate: () => {
      current = false;
    },
    dispose: async () => {
      await app.unmount(component);
      target.remove();
    },
  };
}

void test("Add PUT remains idempotent and accepts only positive safe returned IDs", async () => {
  const calls = [];
  globalThis.fetch = async (input, options) => {
    calls.push({ input, options });
    return json({ id: 7 });
  };
  assert.equal((await app.createIssue(url)).id, 7);
  assert.match(calls[0].input, /\/v1\/issues$/);
  assert.equal(calls[0].options.method, "PUT");
  assert.equal(calls[0].options.credentials, "include");
  assert.deepEqual(JSON.parse(calls[0].options.body), { url });
  for (const body of [
    null,
    {},
    { id: 0 },
    { id: -1 },
    { id: 1.5 },
    { id: "7" },
    { id: Number.MAX_SAFE_INTEGER + 1 },
  ]) {
    globalThis.fetch = async () => json(body);
    await assert.rejects(app.createIssue(url), /invalid issue/);
  }
});

void test("mounted Pragma form rejects invalid URLs and synchronously locks repeated submissions and close paths", async () => {
  const f = fixture();
  let calls = 0;
  const pending = deferred();
  globalThis.fetch = () => {
    calls++;
    return pending.promise;
  };
  try {
    assert.ok(f.input.classList.contains("ds"));
    assert.ok(f.target.querySelector("dialog.ds.modal"));
    for (const invalid of [
      "",
      "not a URL",
      "http://github.com/canonical/test-observer/issues/7",
      "https://user:pass@github.com/canonical/test-observer/issues/7",
      "https://example.test/7",
    ]) {
      f.fill(invalid);
      f.submit();
      app.flushSync();
      assert.equal(calls, 0);
      assert.ok(f.target.querySelector('[role="alert"]'));
    }
    f.fill(url);
    f.submit();
    f.submit();
    f.submit();
    assert.equal(calls, 1);
    app.flushSync();
    assert.equal(f.input.disabled, true);
    assert.equal(
      f.target.querySelector('button[aria-label="Close Add issue"]').disabled,
      true,
    );
    const dialog = f.target.querySelector("dialog");
    const cancel = new Event("cancel", { cancelable: true });
    assert.equal(dialog.dispatchEvent(cancel), false);
    assert.equal(dialog.open, true);
    assert.equal(dialog.getAttribute("closedby"), "closerequest");
    pending.release(json({ id: 7 }));
    await flush();
    app.flushSync();
    assert.deepEqual(f.added, [7]);
    assert.equal(dialog.open, false);
    f.submit();
    assert.equal(calls, 1, "closed form cannot submit");
  } finally {
    await f.dispose();
  }
});

void test("mounted failed/invalid writes keep the dialog recoverable, literal errors escaped and manual retry explicit", async () => {
  const f = fixture();
  let calls = 0;
  const replies = [
    json({ detail: '<img src=x onerror="bad()"> denied' }, 403),
    json({ id: 0 }),
    json({ id: 8 }),
  ];
  globalThis.fetch = async () => {
    calls++;
    return replies.shift();
  };
  try {
    f.fill(url);
    f.submit();
    await flush();
    app.flushSync();
    assert.equal(calls, 1);
    assert.match(f.target.querySelector('[role="alert"]').textContent, /<img/);
    assert.equal(f.target.querySelector("img"), null);
    assert.equal(f.input.disabled, false);
    f.submit();
    await flush();
    app.flushSync();
    assert.deepEqual(f.added, []);
    assert.match(
      f.target.querySelector('[role="alert"]').textContent,
      /invalid issue/,
    );
    f.submit();
    await flush();
    app.flushSync();
    assert.equal(calls, 3);
    assert.deepEqual(f.added, [8]);
  } finally {
    await f.dispose();
  }
});

void test("mounted late success and parsed error cannot affect an invalidated or unmounted dialog/new operation", async () => {
  for (const transition of ["invalidate", "unmount"]) {
    for (const failure of [false, true]) {
      const old = fixture();
      const body = deferred();
      const reply = json({}, failure ? 503 : 200);
      reply.json = () => body.promise;
      globalThis.fetch = async () => reply;
      old.fill(url);
      old.submit();
      await flush();
      if (transition === "invalidate") old.invalidate();
      else await old.dispose();
      const next = fixture();
      const pending = deferred();
      globalThis.fetch = () => pending.promise;
      next.fill(url);
      next.submit();
      app.flushSync();
      body.release(failure ? { detail: "Obsolete parsed error" } : { id: 7 });
      await flush();
      app.flushSync();
      assert.deepEqual(old.added, []);
      assert.equal(
        next.input.disabled,
        true,
        "old completion cannot release new lock",
      );
      assert.equal(next.target.querySelector('[role="alert"]'), null);
      pending.release(json({ id: 9 }));
      await flush();
      app.flushSync();
      assert.deepEqual(next.added, [9]);
      if (transition !== "unmount") await old.dispose();
      await next.dispose();
    }
  }
});

void test("mounted queued close from previous opening cannot close the next opening", async () => {
  const f = fixture();
  try {
    f.target.querySelector('button[aria-label="Close Add issue"]').click();
    app.flushSync();
    f.show();
    await flush();
    app.flushSync();
    assert.equal(f.target.querySelector("dialog").open, true);
  } finally {
    await f.dispose();
  }
});
