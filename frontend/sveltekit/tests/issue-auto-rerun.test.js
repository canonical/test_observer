// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-argument, @typescript-eslint/no-unsafe-return */
/* eslint-disable @typescript-eslint/require-await -- Mock fetch functions deliberately resolve Response objects without real network IO. */

import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { resolve } from "node:path";
import { build } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { Window } from "happy-dom";

/** @type {typeof import('./issue-auto-rerun-entry.svelte.js')} */
let app;
/** @type {Window} */
let browser;
const descriptors = new Map();
const originalFetch = globalThis.fetch;
const flush = () => new Promise((resolve) => setTimeout(resolve, 15));
const json = (body, status = 200) =>
  new Response(JSON.stringify(body), { status });
const user = {
  id: 21,
  name: "Ordinary issue editor",
  is_admin: false,
  teams: [{ permissions: ["change_issue", "change_auto_rerun"] }],
};
const detail = (enabled = false, id = 73) => ({
  id,
  source: "github",
  project: "canonical/test-observer",
  key: String(id),
  title: "Mock issue",
  status: "open",
  url: "https://github.com/canonical/test-observer/issues/73",
  labels: [],
  auto_rerun_enabled: enabled,
  attachment_rules: [],
});

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
      lib: { entry: "tests/issue-auto-rerun-entry.svelte.js", formats: ["es"] },
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

void test("auto-rerun API validates input, target issue and exact server confirmation", async () => {
  const calls = [];
  globalThis.fetch = async (input, options) => {
    calls.push({ input, options });
    return json(detail(true));
  };
  assert.equal(
    (await app.setIssueAutoRerunEnabled(73, true)).auto_rerun_enabled,
    true,
  );
  assert.match(calls[0].input, /\/v1\/issues\/73$/);
  assert.equal(calls[0].options.method, "PATCH");
  assert.equal(calls[0].options.credentials, "include");
  assert.deepEqual(JSON.parse(calls[0].options.body), {
    auto_rerun_enabled: true,
  });
  for (const id of [0, -1, 1.5, NaN, Number.MAX_SAFE_INTEGER + 1])
    await assert.rejects(app.setIssueAutoRerunEnabled(id, true), /Invalid/);
  await assert.rejects(app.setIssueAutoRerunEnabled(73, "true"), /Invalid/);
  assert.equal(calls.length, 1);
  for (const body of [
    detail(true, 80),
    detail(false),
    { ...detail(true), auto_rerun_enabled: "true" },
    null,
  ]) {
    globalThis.fetch = async () => json(body);
    await assert.rejects(
      app.setIssueAutoRerunEnabled(73, true),
      /confirm|invalid/,
    );
  }
  globalThis.fetch = async () => json(detail(false, 80));
  await assert.rejects(app.getIssue(73), /different issue/);
});

void test("session journal locks only its issue and reconciles GET/PATCH ordering without caching fresh reads", () => {
  const journal = new app.IssueAutoRerunUpdates();
  const owner = journal.owner("session A");
  const readA = journal.read(owner, 73);
  const readB = journal.read(owner, 80);
  const update = journal.begin(owner, 73);
  assert.ok(update);
  assert.equal(journal.begin(owner, 73), null);
  assert.equal(journal.busy(owner, 80), false);
  journal.confirm(update, true);
  assert.equal(journal.reconcile(readA, false), true);
  assert.equal(journal.reconcile(readB, false), false);
  assert.equal(journal.reconcile(journal.read(owner, 73), false), false);
  journal.finish(update);
  assert.equal(journal.busy(owner, 73), false);
  const reverse = journal.begin(owner, 73);
  const intervening = journal.read(owner, 73);
  journal.confirm(reverse, false);
  assert.equal(journal.reconcile(intervening, true), false);
  journal.finish(reverse);
});

void test("A/B/A sessions cannot revive old journal confirmations, locks or completion cleanup", () => {
  const journal = new app.IssueAutoRerunUpdates();
  const owner = journal.owner("A");
  const old = journal.begin(owner, 73);
  const read = journal.read(owner, 73);
  journal.owner("B");
  const again = journal.owner("A");
  assert.notEqual(again, owner);
  const fresh = journal.begin(again, 73);
  journal.confirm(old, true);
  journal.finish(old);
  assert.equal(journal.busy(again, 73), true);
  assert.equal(journal.reconcile(read, false), false);
  journal.finish(fresh);
});

void test("fresh version-owned permissions require both ordinary grants and reject unknown, cancelled or superseded refreshes", async () => {
  for (const permissions of [
    [],
    ["change_issue"],
    ["change_auto_rerun"],
    ["change_issue", "change_auto_rerun"],
  ]) {
    const gate = await app.refreshBulkPermissions(async () =>
      json({ ...user, teams: [{ permissions }] }),
    );
    assert.equal(gate.check("autoRerun", false).ok, permissions.length === 2);
  }
  const gate = await app.refreshBulkPermissions(async () => json(user));
  await app.userStore.refresh(async () => json({ detail: "unavailable" }, 503));
  assert.equal(gate.check("autoRerun", false).ok, false);
  const unknown = await app.refreshBulkPermissions(async () => json(null, 503));
  assert.equal(
    unknown.check("autoRerun", false).ok,
    false,
    "cached ordinary grants are not evidence",
  );
  const controller = new AbortController();
  const cancelled = await app.refreshBulkPermissions(
    async () => json(user),
    controller.signal,
  );
  controller.abort();
  assert.equal(cancelled.check("autoRerun", false).ok, false);
  const held = deferred();
  const superseded = app.refreshBulkPermissions(() => held.promise);
  await app.userStore.refresh(async () => json(null));
  held.release(json(user));
  assert.equal((await superseded).check("autoRerun", false).ok, false);
});

void test("session ownership notices logout/login while no issue consumer is mounted, but keeps identical refreshes", async () => {
  await app.userStore.refresh(async () => json(user));
  const owner = app.issueAutoRerunSession();
  await app.userStore.refresh(async () => json(user));
  assert.equal(app.issueAutoRerunSession(), owner);
  await app.userStore.refresh(async () => json(null));
  await app.userStore.refresh(async () => json(user));
  assert.notEqual(app.issueAutoRerunSession(), owner);
});

void test("mounted Pragma Switch preserves confirmed state while pending/failing, locks and retries with a fresh grant check", async () => {
  await app.userStore.refresh(async () => json(user));
  const held = deferred();
  let patches = 0;
  let checks = 0;
  globalThis.fetch = async (input) => {
    if (
      (input instanceof Request ? input.url : input.toString()).endsWith(
        "users/me",
      )
    ) {
      ++checks;
      return json(user);
    }
    ++patches;
    return patches === 1 ? held.promise : json(detail(true));
  };
  const target = document.createElement("div");
  document.body.append(target);
  const ui = app.mountSetting(target, 73, false);
  const owner = app.issueAutoRerunSession();
  const unsubscribe = app.issueAutoRerunUpdates.subscribe((event) => {
    if (event.type === "confirmed") ui.update({ enabled: event.enabled });
  });
  try {
    await flush();
    const control = target.querySelector('[role="switch"]');
    assert.ok(control.classList.contains("ds"));
    assert.match(target.textContent, /Automatically request reruns/);
    control.click();
    await flush();
    assert.equal(control.checked, false);
    assert.equal(control.getAttribute("aria-checked"), "false");
    assert.equal(control.disabled, true);
    control.click();
    assert.equal(patches, 1);
    held.release(json({ detail: "Denied by mock" }, 403));
    await flush();
    assert.equal(control.checked, false);
    assert.equal(control.disabled, false);
    assert.match(target.textContent, /Update not confirmed. Denied by mock/);
    control.click();
    await flush();
    assert.equal(control.checked, true);
    assert.equal(control.getAttribute("aria-checked"), "true");
    assert.equal(checks, 2);
    assert.equal(patches, 2);
    assert.equal(app.issueAutoRerunUpdates.busy(owner, 73), false);
  } finally {
    unsubscribe();
    await ui.destroy();
    target.remove();
  }
});

void test("mounted transport failure and stale parsed error bodies cannot claim success or cross navigation/session/unmount", async () => {
  await app.userStore.refresh(async () => json(user));
  const body = deferred();
  let mode = "transport";
  globalThis.fetch = async (input) => {
    if (
      (input instanceof Request ? input.url : input.toString()).endsWith(
        "users/me",
      )
    )
      return json(user);
    if (mode === "transport") throw new Error("Mock connection lost");
    const response = json({}, 403);
    response.json = () => body.promise;
    return response;
  };
  const target = document.createElement("div");
  document.body.append(target);
  const ui = app.mountSetting(target, 73, false);
  try {
    await flush();
    target.querySelector('[role="switch"]').click();
    await flush();
    assert.match(
      target.textContent,
      /Update not confirmed. Mock connection lost/,
    );
    assert.equal(target.querySelector('[role="switch"]').checked, false);
    mode = "held";
    target.querySelector('[role="switch"]').click();
    await flush();
    ui.update({ issueId: 80 });
    await flush();
    body.release({ detail: "Old parsed denial" });
    await flush();
    assert.doesNotMatch(target.textContent, /Old parsed denial/);
    await app.userStore.refresh(async () => json(null));
    await flush();
    assert.doesNotMatch(target.textContent, /Update not confirmed/);
  } finally {
    await ui.destroy();
    target.remove();
  }
});

void test("unmount during fresh authorization cancels before any PATCH", async () => {
  await app.userStore.refresh(async () => json(user));
  const auth = deferred();
  let patches = 0;
  globalThis.fetch = async (input) => {
    if (
      (input instanceof Request ? input.url : input.toString()).endsWith(
        "users/me",
      )
    )
      return auth.promise;
    ++patches;
    return json(detail(true));
  };
  const target = document.createElement("div");
  document.body.append(target);
  const ui = app.mountSetting(target, 73, false);
  await flush();
  target.querySelector('[role="switch"]').click();
  await ui.destroy();
  auth.release(json(user));
  await flush();
  assert.equal(patches, 0);
  target.remove();
});

void test("a superseding failed refresh cannot authorize a mounted write from cached ordinary grants", async () => {
  await app.userStore.refresh(async () => json(user));
  const auth = deferred();
  let patches = 0;
  globalThis.fetch = async (input) => {
    if (
      (input instanceof Request ? input.url : input.toString()).endsWith(
        "users/me",
      )
    )
      return auth.promise;
    ++patches;
    return json(detail(true));
  };
  const target = document.createElement("div");
  document.body.append(target);
  const ui = app.mountSetting(target, 73, false);
  try {
    await flush();
    target.querySelector('[role="switch"]').click();
    await app.userStore.refresh(async () => json(null, 503));
    auth.release(json(user));
    await flush();
    assert.equal(patches, 0);
    assert.match(target.textContent, /unknown, cancelled or superseded/);
    assert.equal(target.querySelector('[role="switch"]').checked, false);
  } finally {
    await ui.destroy();
    target.remove();
  }
});

void test("a parsed mutation error cannot reappear after changing session or unmounting", async () => {
  for (const invalidation of ["session", "unmount"]) {
    await app.userStore.refresh(async () => json(user));
    const body = deferred();
    globalThis.fetch = async (input) => {
      if (
        (input instanceof Request ? input.url : input.toString()).endsWith(
          "users/me",
        )
      )
        return json(user);
      const response = json({}, 401);
      response.json = () => body.promise;
      return response;
    };
    const target = document.createElement("div");
    document.body.append(target);
    const ui = app.mountSetting(target, 73, false);
    await flush();
    target.querySelector('[role="switch"]').click();
    await flush();
    if (invalidation === "session") {
      await app.userStore.refresh(async () => json({ ...user, id: 22 }));
      await flush();
    } else await ui.destroy();
    body.release({ detail: "Obsolete 401 error body" });
    await flush();
    assert.doesNotMatch(target.textContent, /Obsolete 401 error body/);
    if (invalidation === "session") await ui.destroy();
    target.remove();
  }
});
