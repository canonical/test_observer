// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-argument, @typescript-eslint/no-unsafe-return */
import assert from "node:assert/strict";
import { before, after, test } from "node:test";
import { resolve } from "node:path";
import { build } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { Window } from "happy-dom";

let app;
let browser;
const globals = new Map();
const originalFetch = globalThis.fetch;
const flush = () => new Promise((resolve) => setTimeout(resolve, 20));
const json = (body, status = 200) =>
  new Response(JSON.stringify(body), { status });
const user = {
  id: 21,
  name: "Ordinary rerun editor",
  is_admin: false,
  teams: [{ permissions: ["change_rerun", "change_rerun_bulk"] }],
};
const ready = {
  available: true,
  loading: false,
  moving: false,
  accessError: false,
  unapplied: false,
  mutating: false,
};
function deferred() {
  let release;
  const promise = new Promise((resolve) => (release = resolve));
  return { promise, release: (value) => release(value) };
}
before(async () => {
  browser = new Window({ url: "http://localhost/wip/issues/73" });
  for (const name of [
    "window",
    "document",
    "navigator",
    "Comment",
    "Text",
    "Node",
    "Element",
    "HTMLElement",
    "HTMLDialogElement",
    "HTMLInputElement",
    "HTMLMediaElement",
    "HTMLSelectElement",
    "HTMLTextAreaElement",
    "Event",
    "KeyboardEvent",
    "MouseEvent",
    "CSS",
    "ResizeObserver",
    "MutationObserver",
    "customElements",
    "getComputedStyle",
    "requestAnimationFrame",
    "cancelAnimationFrame",
  ]) {
    globals.set(name, Object.getOwnPropertyDescriptor(globalThis, name));
    Object.defineProperty(globalThis, name, {
      configurable: true,
      value: name === "window" ? browser : Reflect.get(browser, name),
    });
  }
  // Test-only native dialog adapter. Chromium separately covers real top layer.
  // Preserve the dynamic receiver; invoke only with .call().
  // eslint-disable-next-line @typescript-eslint/unbound-method
  const matches = browser.Element.prototype.matches;
  browser.Element.prototype.matches = function (selector) {
    return selector === ":modal"
      ? this.hasAttribute("data-test-modal")
      : matches.call(this, selector);
  };
  browser.HTMLDialogElement.prototype.showModal = function () {
    this.open = true;
    this.setAttribute("data-test-modal", "");
  };
  browser.HTMLDialogElement.prototype.close = function () {
    if (!this.open) return;
    this.open = false;
    this.removeAttribute("data-test-modal");
    setTimeout(() => this.dispatchEvent(new browser.Event("close")));
  };
  const built = await build({
    configFile: false,
    logLevel: "silent",
    plugins: [svelte({ configFile: false })],
    resolve: { alias: { $lib: resolve("src/lib") }, conditions: ["browser"] },
    build: {
      write: false,
      lib: { entry: "tests/issue-reruns-entry.svelte.js", formats: ["es"] },
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
  for (const [name, descriptor] of globals) {
    if (descriptor) Object.defineProperty(globalThis, name, descriptor);
    else Reflect.deleteProperty(globalThis, name);
  }
  void browser.happyDOM.abort();
});
function button(target, text) {
  const found = [...target.querySelectorAll("button")].find(
    (item) => item.textContent.trim() === text,
  );
  assert.ok(found, `Missing button ${text}`);
  return found;
}
function dialog(ui) {
  const found = ui.target.querySelector("dialog.bulk-rerun-review");
  assert.ok(found);
  return found;
}
async function type(input, value) {
  input.value = value;
  input.dispatchEvent(new browser.Event("input", { bubbles: true }));
  await flush();
}
async function check(target, text) {
  const label = [...target.querySelectorAll("label")].find((item) =>
    item.textContent.includes(text),
  );
  assert.ok(label, text);
  label.querySelector("input").click();
  await flush();
}
function mock({
  count = 125,
  previewStatus = 200,
  writeStatus = 200,
  grants = user,
  write,
  preview,
  me,
} = {}) {
  const calls = [];
  globalThis.fetch = (input, options = {}) => {
    const url = new URL(input instanceof Request ? input.url : input);
    const call = { url, options };
    calls.push(call);
    if (url.pathname.endsWith("/users/me"))
      return Promise.resolve(me ? me() : json(grants));
    if (options.method === "POST" || options.method === "DELETE")
      return write ? write(call) : Promise.resolve(json({}, writeStatus));
    if (url.pathname.endsWith("/test-results"))
      return preview
        ? preview(call)
        : Promise.resolve(
            json(
              previewStatus === 200
                ? { count }
                : { detail: "Preview rejected" },
              previewStatus,
            ),
          );
    return Promise.resolve(
      json({ count: 625, limit: 50, offset: 0, rows: [] }),
    );
  };
  return {
    calls,
    writes: () =>
      calls.filter(({ options }) =>
        ["POST", "DELETE"].includes(options.method),
      ),
    previews: () =>
      calls.filter(({ url }) => url.pathname.endsWith("/test-results")),
  };
}
async function mount() {
  app.userStore.current = structuredClone(user);
  const target = browser.document.createElement("div");
  browser.document.body.append(target);
  const handle = app.mountResults(target);
  await flush();
  return {
    target,
    handle,
    destroy: async () => {
      await handle.destroy();
      target.remove();
    },
  };
}
async function open(ui, operation = "Create") {
  button(ui.target, `${operation} rerun requests`).click();
  await flush();
  return dialog(ui);
}

void test("issue rerun target validates exactly one pinned issue, uses full server total and freezes optional applied conditions", () => {
  const query = app.issueResultsQuery(73, {
    artefacts: ["one", "two"],
    until_date: "2026-10-25T12:00:00.123456Z",
  });
  const scope = app.issueRerunTarget(73, query, 625, ready);
  assert.equal(scope.ok, true);
  assert.equal(scope.value.count, 625);
  assert.equal(scope.value.kind, "query");
  assert.deepEqual(scope.value.filters, {
    artefacts: ["one", "two"],
    issues: [73],
    until_date: "2026-10-25T12:00:00.123456Z",
  });
  assert.throws(() => scope.value.filters.issues.push(80), TypeError);
  for (const issues of [[], [80], [73, 80], [73, 73], "any", "none"])
    assert.equal(
      app.issueRerunTarget(
        73,
        { ...query, filters: { ...query.filters, issues } },
        625,
        ready,
      ).ok,
      false,
    );
  for (const count of [null, 0, -1, 1.5, NaN])
    assert.equal(app.issueRerunTarget(73, query, count, ready).ok, false);
  assert.equal(
    app.issueRerunTarget(
      73,
      app.issueResultsQuery(73, { from_date: "bad" }),
      625,
      ready,
    ).ok,
    false,
  );
  const create = app.rerunPlan(scope.value, "create").value.payload
    .test_results_filters;
  assert.equal(create.execution_is_latest, true);
  assert.equal(create.artefact_is_archived, false);
  assert.equal(create.rerun_is_requested, false);
  const deletion = app.rerunPlan(scope.value, "delete").value.payload
    .test_results_filters;
  assert.equal(deletion.execution_is_latest, undefined);
  assert.equal(deletion.artefact_is_archived, undefined);
  assert.equal(deletion.rerun_is_requested, true);
});

void test("mounted issue create/delete freeze applied filters, not drafts/cache; preview equals payload, options/priority reset acknowledgment and success refreshes", async () => {
  const api = mock();
  const ui = await mount();
  try {
    button(ui.target, "Optional filters (0 applied groups)").click();
    await flush();
    await type(
      ui.target.querySelector('input[name="artefacts"]'),
      "applied artefact",
    );
    const artefact = ui.target.querySelector(
      'section[aria-label="Artefact filter"]',
    );
    button(artefact, "Add exact value").click();
    await flush();
    button(ui.target, "Apply filters").click();
    await flush();
    await type(
      ui.target.querySelector('input[name="artefacts"]'),
      "draft only",
    );
    button(artefact, "Add exact value").click();
    await flush();
    let review = await open(ui);
    assert.match(review.textContent, /Matches 125 test results/);
    assert.doesNotMatch(review.textContent, /draft only/);
    assert.equal(button(review, "Create rerun requests").disabled, true);
    assert.ok(review.querySelector("input.ds.checkbox"));
    assert.ok(review.querySelector("input.ds.text-input"));
    await check(review, "I have reviewed");
    await type(review.querySelector('input[inputmode="numeric"]'), "17");
    assert.equal(button(review, "Create rerun requests").disabled, true);
    await check(review, "I have reviewed");
    await check(review, "Only latest");
    assert.equal(button(review, "Create rerun requests").disabled, true);
    await check(review, "I have reviewed");
    button(review, "Create rerun requests").click();
    await flush();
    const created = api.writes()[0];
    assert.equal(created.options.method, "POST");
    assert.equal(created.url.searchParams.get("silent"), "true");
    const payload = JSON.parse(created.options.body);
    assert.equal(payload.priority, 17);
    assert.deepEqual(payload.test_results_filters, {
      artefacts: ["applied artefact"],
      issues: [73],
      artefact_is_archived: false,
      rerun_is_requested: false,
    });
    const preview = api.previews().at(-1).url.searchParams;
    for (const [key, value] of Object.entries(payload.test_results_filters))
      assert.deepEqual(
        preview.getAll(key),
        (Array.isArray(value) ? value : [value]).map(String),
      );
    assert.equal(preview.get("limit"), "0");
    assert.equal("test_execution_ids" in payload, false);
    assert.match(ui.target.textContent, /Create rerun request completed/);
    assert.equal(
      api.calls.filter(({ url }) => url.pathname.endsWith("search-page"))
        .length,
      3,
    );
    review = await open(ui, "Delete");
    const options = [...review.querySelectorAll('input[type="checkbox"]')];
    assert.deepEqual(
      options.slice(0, 2).map((input) => input.checked),
      [false, false],
    );
    await check(review, "I have reviewed");
    button(review, "Delete rerun requests").click();
    await flush();
    const deleted = api.writes()[1];
    assert.equal(deleted.options.method, "DELETE");
    assert.deepEqual(JSON.parse(deleted.options.body), {
      test_results_filters: {
        artefacts: ["applied artefact"],
        issues: [73],
        rerun_is_requested: true,
      },
    });
  } finally {
    await ui.destroy();
  }
});

void test("mounted rerun review rejects zero/failed/401/403 previews and invalid priority without any write", async () => {
  for (const scenario of [
    { count: 0 },
    { previewStatus: 500 },
    { previewStatus: 401 },
    { previewStatus: 403 },
  ]) {
    const api = mock(scenario);
    const ui = await mount();
    try {
      const review = await open(ui);
      assert.equal(button(review, "Create rerun requests").disabled, true);
      assert.match(
        review.textContent,
        scenario.count === 0 ? /Matches 0/ : /Count preview failed/,
      );
      assert.equal(api.writes().length, 0);
    } finally {
      await ui.destroy();
    }
  }
  const api = mock({ count: 50 });
  const ui = await mount();
  try {
    const review = await open(ui);
    assert.equal(button(review, "Create rerun requests").disabled, false);
    for (const value of ["", "1.5", "1000001", "1e3", "not an integer"]) {
      await type(review.querySelector('input[inputmode="numeric"]'), value);
      assert.equal(button(review, "Create rerun requests").disabled, true);
      assert.match(review.textContent, /priority must be an integer/);
    }
    assert.equal(api.writes().length, 0);
  } finally {
    await ui.destroy();
  }
});

void test("mounted rerun review requires both fresh ordinary grants and rechecks authorization before writing", async () => {
  for (const permissions of [[], ["change_rerun"], ["change_rerun_bulk"]]) {
    const api = mock({
      count: 1,
      grants: { ...user, teams: [{ permissions }] },
    });
    const ui = await mount();
    try {
      const review = await open(ui);
      assert.equal(button(review, "Create rerun requests").disabled, true);
      assert.equal(api.writes().length, 0);
    } finally {
      await ui.destroy();
    }
  }
  let meCount = 0;
  const api = mock({ count: 1, me: () => json(++meCount === 1 ? user : null) });
  const ui = await mount();
  try {
    const review = await open(ui);
    button(review, "Create rerun requests").click();
    await flush();
    assert.equal(meCount, 2);
    assert.equal(api.writes().length, 0);
    assert.match(review.textContent, /session changed/);
  } finally {
    await ui.destroy();
  }
});

void test("mounted rerun review terminal write failures and ambiguous transport never replay or refresh as success", async () => {
  for (const write of [
    () => Promise.resolve(json({ detail: "Session rejected" }, 401)),
    () => Promise.resolve(json({ detail: "Permission rejected" }, 403)),
    () => Promise.resolve(json({ detail: "Service failed" }, 500)),
    () => Promise.reject(new TypeError("Network lost")),
  ]) {
    const api = mock({ count: 1, write });
    const ui = await mount();
    try {
      const review = await open(ui);
      button(review, "Create rerun requests").click();
      await flush();
      assert.equal(api.writes().length, 1);
      assert.equal(button(review, "Create rerun requests").disabled, true);
      assert.match(review.textContent, /Refresh results|Outcome unknown/);
      button(review, "Create rerun requests").click();
      await flush();
      assert.equal(api.writes().length, 1);
      assert.doesNotMatch(ui.target.textContent, /request completed/);
    } finally {
      await ui.destroy();
    }
  }
});

void test("mounted rerun review invalidates issue and session A/B/A, fences delayed count/error bodies and unmount before authorization", async () => {
  const held = deferred();
  const api = mock({
    preview: () => {
      const res = json({});
      res.json = () => held.promise;
      return Promise.resolve(res);
    },
  });
  const ui = await mount();
  try {
    const review = await open(ui);
    ui.handle.changeIssue(80);
    ui.handle.changeIssue(73);
    await flush();
    held.release({ count: 999 });
    await flush();
    assert.match(review.textContent, /session changed/);
    assert.doesNotMatch(review.textContent, /Matches 999/);
    assert.equal(api.writes().length, 0);
  } finally {
    await ui.destroy();
  }
  const staleError = deferred();
  const writes = mock({
    count: 1,
    write: () => {
      const res = json({}, 422);
      res.json = () => staleError.promise;
      return Promise.resolve(res);
    },
  });
  const second = await mount();
  try {
    const review = await open(second);
    button(review, "Create rerun requests").click();
    await flush();
    assert.match(review.textContent, /Submitting… Closing is disabled/);
    await app.userStore.refresh(() => Promise.resolve(json(null)));
    await app.userStore.refresh(() => Promise.resolve(json(user)));
    await flush();
    staleError.release({ detail: "OBSOLETE BODY" });
    await flush();
    assert.match(review.textContent, /session changed/);
    assert.doesNotMatch(review.textContent, /OBSOLETE BODY/);
    assert.equal(writes.writes().length, 1);
    button(review, "Create rerun requests").click();
    await flush();
    assert.equal(writes.writes().length, 1);
  } finally {
    await second.destroy();
  }
  let meCount = 0;
  const auth = deferred();
  const pending = mock({
    count: 1,
    me: () => (++meCount === 1 ? json(user) : auth.promise),
  });
  const third = await mount();
  const review = await open(third);
  button(review, "Create rerun requests").click();
  await flush();
  await third.destroy();
  auth.release(json(user));
  await flush();
  assert.equal(pending.writes().length, 0);
});

void test("mounted issue applied-query invalidation is durable; identical permission refreshes preserve scope but cannot revive an invalidated review", async () => {
  const api = mock({ count: 1 });
  const ui = await mount();
  try {
    button(ui.target, "Optional filters (0 applied groups)").click();
    await flush();
    await type(
      ui.target.querySelector('input[name="artefacts"]'),
      "new applied",
    );
    button(
      ui.target.querySelector('section[aria-label="Artefact filter"]'),
      "Add exact value",
    ).click();
    await flush();
    const review = await open(ui);
    await app.userStore.refresh(() => Promise.resolve(json(user)));
    await flush();
    assert.doesNotMatch(review.textContent, /session changed/);
    assert.equal(
      button(review, "Create rerun requests").disabled,
      true,
      "a different authorization refresh revokes the old grant",
    );
    button(review, "Refresh permissions").click();
    await flush();
    assert.equal(button(review, "Create rerun requests").disabled, false);
    // Native dialogs make the background inert. Invoke an old callback to cover
    // external/programmatic applied-query changes rather than user clicks there.
    button(ui.target, "Apply filters").click();
    await flush();
    assert.match(review.textContent, /session changed/);
    await app.userStore.refresh(() => Promise.resolve(json(user)));
    await flush();
    assert.equal(button(review, "Create rerun requests").disabled, true);
    assert.equal(api.writes().length, 0);
  } finally {
    await ui.destroy();
  }
});

void test("mounted rerun review suppresses held preview errors and confirmed write completions after forced unmount", async () => {
  const body = deferred();
  const api = mock({
    preview: () => {
      const response = json({}, 422);
      response.json = () => body.promise;
      return Promise.resolve(response);
    },
  });
  const ui = await mount();
  const review = await open(ui);
  ui.handle.changeIssue(80);
  await flush();
  body.release({ detail: "OBSOLETE PREVIEW" });
  await flush();
  assert.doesNotMatch(review.textContent, /OBSOLETE PREVIEW/);
  assert.equal(api.writes().length, 0);
  await ui.destroy();

  const success = deferred();
  const writes = mock({
    count: 1,
    write: () => {
      const response = json({});
      response.json = () => success.promise;
      return Promise.resolve(response);
    },
  });
  const second = await mount();
  const active = await open(second);
  button(active, "Create rerun requests").click();
  await flush();
  assert.equal(writes.writes().length, 1);
  const before = writes.calls.length;
  await second.destroy();
  success.release({});
  await flush();
  assert.equal(
    writes.calls.length,
    before,
    "a destroyed owner cannot refresh results or replay a write",
  );
});

void test("mounted shared review preserves explicit-selection defaults, opt-in and execution grouping", async () => {
  const api = mock({ count: 1 });
  app.userStore.current = structuredClone(user);
  const target = browser.document.createElement("div");
  browser.document.body.append(target);
  const handle = app.mountReview(target, {
    kind: "explicit",
    queryKey: "explicit",
    resultIds: [1, 2],
    executions: [
      { resultId: 1, executionId: 501 },
      { resultId: 2, executionId: 501 },
    ],
  });
  try {
    await handle.start("create");
    await flush();
    const review = dialog({ target });
    assert.equal(button(review, "Create rerun requests").disabled, true);
    assert.match(
      review.textContent,
      /2 selected test results → 1 unique executions/,
    );
    await check(review, "Use these exact execution groups");
    button(review, "Create rerun requests").click();
    await flush();
    assert.deepEqual(JSON.parse(api.writes()[0].options.body), {
      test_execution_ids: [501],
      priority: 0,
    });
    assert.equal(api.previews().length, 0);
  } finally {
    await handle.destroy();
    target.remove();
  }
});
