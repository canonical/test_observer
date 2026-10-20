// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { build } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { Window } from "happy-dom";

/** @type {typeof import('./test-results-search-entry.svelte.js')} */
let app;
/** @type {Window} */
let browser;
/** @type {Map<string, PropertyDescriptor | undefined>} */
const globals = new Map();
const originalFetch = globalThis.fetch;

const families = [
  {
    name: "configured-route",
    api_name: "snap",
    stages: [],
    columns: [],
    filters: [],
  },
  {
    name: "another-route",
    api_name: "another-api-family",
    stages: [],
    columns: [],
    filters: [],
  },
];
const url = (/** @type {string} */ query = "") =>
  new URL(
    `https://observer.example/custom/base/test-results${query ? `?${query}` : ""}`,
  );
const json = (/** @type {unknown} */ body, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
const flush = () => new Promise((resolve) => setTimeout(resolve, 15));

function deferred() {
  /** @type {(value: Response) => void} */
  let complete;
  const promise = new Promise(
    /** @param {(value: Response) => void} resolve */ (resolve) => {
      complete = resolve;
    },
  );
  return {
    promise,
    resolve: (/** @type {Response} */ response) => {
      complete(response);
    },
  };
}

function result(id = 1) {
  return {
    test_result: {
      id,
      name: `case ${id}`,
      status: "FAILED",
      created_at: "2026-01-01T00:00:00Z",
    },
    artefact: {
      id: 42,
      name: "example artefact",
      version: "1.2",
      track: "stable",
      family: "snap",
    },
    artefact_build: { id: 3, architecture: "amd64", revision: 1 },
    test_execution: {
      id: 7,
      status: "FAILED",
      environment: { id: 5, name: "test lab", architecture: "amd64" },
      test_plan: "smoke",
    },
  };
}
const response = (ids = [1], count = ids.length, limit = 50, offset = 0) =>
  json({ count, limit, offset, test_results: ids.map(result) });

before(async () => {
  const built = /** @type {{output: {type: string; code: string}[]}[]} */ (
    /** @type {unknown} */ (
      await build({
        configFile: false,
        logLevel: "silent",
        plugins: [svelte({ compilerOptions: { runes: true } })],
        resolve: { alias: { $lib: resolve("src/lib") } },
        build: {
          write: false,
          lib: {
            entry: "tests/test-results-search-entry.svelte.js",
            formats: ["es"],
          },
          rolldownOptions: { output: { codeSplitting: false } },
        },
      })
    )
  );
  const bundle = built[0].output.find((item) => item.type === "chunk");
  assert.ok(bundle);
  browser = new Window({ url: url().href });
  for (const name of [
    "window",
    "document",
    "navigator",
    "Comment",
    "Text",
    "Node",
    "Element",
    "HTMLElement",
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
  // Happy DOM does not implement the native Popover API used by Pragma. Model
  // its beforetoggle/toggle, declarative triggers and auto light-dismiss here.
  // Rendering can settle between beforetoggle and the native open transition;
  // focus on a still-closed popover must be ignored, just like the browser.
  // Real top-layer positioning and keyboard traversal still need browser QA.
  /** @type {Set<import('happy-dom').HTMLElement>} */
  const openPopovers = new Set();
  /** @param {string} name @param {string} oldState @param {string} newState */
  const toggleEvent = (name, oldState, newState) =>
    Object.assign(new browser.Event(name), { oldState, newState });
  /** @param {import('happy-dom').HTMLElement} element */
  function hidePopover(element) {
    if (!openPopovers.has(element)) return;
    element.dispatchEvent(toggleEvent("beforetoggle", "open", "closed"));
    openPopovers.delete(element);
    element.removeAttribute("data-test-open");
    element.dispatchEvent(toggleEvent("toggle", "open", "closed"));
  }
  /** @param {import('happy-dom').HTMLElement} element */
  function showPopover(element) {
    if (openPopovers.has(element)) return;
    element.dispatchEvent(toggleEvent("beforetoggle", "closed", "open"));
    for (const other of openPopovers) hidePopover(other);
    setTimeout(() => {
      if (!element.isConnected) return;
      openPopovers.add(element);
      element.setAttribute("data-test-open", "");
      element.dispatchEvent(toggleEvent("toggle", "closed", "open"));
    });
  }
  // Preserve the native methods' dynamic receivers; invoke only with .call().
  // eslint-disable-next-line @typescript-eslint/unbound-method
  const originalFocus = browser.HTMLElement.prototype.focus;
  // eslint-disable-next-line @typescript-eslint/unbound-method
  const originalMatches = browser.Element.prototype.matches;
  browser.Element.prototype.matches = function (selector) {
    if (selector === ":popover-open")
      return this.hasAttribute("data-test-open");
    return originalMatches.call(this, selector);
  };
  browser.HTMLElement.prototype.focus = function () {
    const containingPopover = this.closest("[popover]");
    if (containingPopover && !containingPopover.hasAttribute("data-test-open"))
      return;
    originalFocus.call(this);
  };
  Object.defineProperties(browser.HTMLElement.prototype, {
    showPopover: {
      /** @this {import('happy-dom').HTMLElement} */
      value() {
        showPopover(this);
      },
    },
    hidePopover: {
      /** @this {import('happy-dom').HTMLElement} */
      value() {
        hidePopover(this);
      },
    },
  });
  browser.document.addEventListener("click", (event) => {
    const target = /** @type {import('happy-dom').Element} */ (event.target);
    const trigger =
      /** @type {import('happy-dom').HTMLButtonElement | null} */ (
        target.closest("button[popovertarget]")
      );
    const popover = trigger
      ? browser.document.getElementById(
          trigger.getAttribute("popovertarget") ?? "",
        )
      : null;
    if (popover) {
      trigger?.focus();
      if (openPopovers.has(popover)) hidePopover(popover);
      else showPopover(popover);
    } else {
      for (const open of openPopovers)
        if (!open.contains(target)) hidePopover(open);
    }
  });
  // Model the browser's default Enter activation for native popover triggers.
  browser.document.addEventListener("keydown", (event) => {
    const target = /** @type {import('happy-dom').HTMLButtonElement} */ (
      event.target
    );
    if (
      event.key === "Enter" &&
      !event.defaultPrevented &&
      target.matches("button[popovertarget]")
    )
      target.click();
  });
  // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
  app = /** @type {typeof import('./test-results-search-entry.svelte.js')} */ (
    /** @type {unknown} */ (
      await import(
        `data:text/javascript;base64,${Buffer.from(bundle.code).toString("base64")}`
      )
    )
  );
});

after(async () => {
  globalThis.fetch = originalFetch;
  await browser.happyDOM.abort();
  for (const [name, descriptor] of globals) {
    if (descriptor) Object.defineProperty(globalThis, name, descriptor);
    else Reflect.deleteProperty(globalThis, name);
  }
});

void test("family display names capitalize only the first route-name character, independently of API names", () => {
  for (const [name, expected] of [
    ["configured-route", "Configured-route"],
    ["customWidgets", "CustomWidgets"],
    ["aPI-bundles", "API-bundles"],
    ["Already-Mixed", "Already-Mixed"],
    [" spaced", " spaced"],
    ["", ""],
  ]) {
    const family = { ...families[0], name, api_name: "unrelated-api-family" };
    assert.equal(app.familyDisplayName(family), expected);
    assert.equal(family.name, name);
    assert.equal(family.api_name, "unrelated-api-family");
  }
});

void test("all eight list filters match OpenAPI names, repeated parameters, and backend exact-match contracts", async () => {
  // JSON.parse's untyped return is narrowed to the schema fragment under test.
  // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
  const schema =
    /** @type {{ paths: Record<string, {get: {parameters: {name: string; schema: {anyOf?: {type?: string}[]} }[]}}> }} */ (
      JSON.parse(
        await readFile(
          new URL("../../../backend/schemata/openapi.json", import.meta.url),
          "utf8",
        ),
      )
    );
  const parameters = schema.paths["/v1/test-results"].get.parameters;
  const matching = await readFile(
    new URL(
      "../../../backend/test_observer/controllers/test_results/filter_test_results.py",
      import.meta.url,
    ),
    "utf8",
  );
  for (const key of app.SEARCH_FILTERS) {
    assert.ok(
      parameters
        .find((parameter) => parameter.name === key)
        ?.schema.anyOf?.some((type) => type.type === "array"),
      key,
    );
    assert.match(matching, new RegExp(`\\.in_\\(filters\\.${key}\\)`));
  }
  const params = new URLSearchParams(
    "families=snap&test_result_statuses=FAILED,PASSED&test_result_statuses=SKIPPED&artefacts=alpha, beta&artefacts=alpha&artefact_versions=1%2B2&artefact_tracks=stable&environments=lab&test_plans=smoke&test_cases=case",
  );
  const query = app.parseSearch(params, families);
  assert.deepEqual(query.problems, []);
  assert.deepEqual(query.filters.test_result_statuses, [
    "FAILED",
    "PASSED",
    "SKIPPED",
  ]);
  assert.deepEqual(query.filters.artefacts, ["alpha", "beta"]);
  assert.equal(query.hasFilters, true);
  const apiParams = app.searchParams(query.filters, 2, 4);
  assert.deepEqual(apiParams.getAll("artefacts"), ["alpha", "beta"]);
  assert.deepEqual(apiParams.getAll("test_result_statuses"), [
    "FAILED",
    "PASSED",
    "SKIPPED",
  ]);
  assert.equal(apiParams.get("artefact_versions"), "1+2");
  assert.equal(apiParams.get("offset"), "4");
  assert.deepEqual(app.parseSearch(apiParams, families).filters, query.filters);
  assert.equal(
    app.viewRunPath(
      /** @type {import('../src/lib/testResultsSearch').SearchResult} */ (
        /** @type {unknown} */ (result())
      ),
      families,
      "/other/base",
    ),
    "/other/base/configured-route/42?testExecutionId=7&testResultId=1",
  );
  assert.equal(
    app.viewRunPath(
      /** @type {import('../src/lib/testResultsSearch').SearchResult} */ (
        /** @type {unknown} */ (result())
      ),
      [],
      "",
    ),
    null,
  );
});

void test("unsupported and invalid URL filters block instead of silently broadening the search", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(response());
  };
  const store = new app.TestResultsSearchStore();
  for (const query of [
    "artefacts=ok&issues=1",
    "families=unknown",
    "test_result_statuses=UNKNOWN",
    "artefacts=ok&offset=-1",
    "artefacts=ok&limit=0",
    "artefacts=ok&limit=1&limit=2",
    "artefacts=ok&offset=9007199254740992",
  ]) {
    const applied = app.parseSearch(url(query).searchParams, families);
    assert.ok(applied.problems.length, query);
    await store.search(applied);
    assert.equal(store.response, null);
    assert.equal(store.loading, false);
  }
  for (const query of [
    "",
    "limit=2&offset=3",
    "artefacts= , ",
    "view=invalid",
    "view=invalid&limit=2&offset=3",
  ]) {
    await store.search(app.parseSearch(url(query).searchParams, families));
  }
  assert.equal(calls, 0);
});

void test("search uses configured API defaults and replaces pages, safely ending on short or empty responses", async () => {
  /** @type {{url: URL; options: RequestInit}[]} */
  const calls = [];
  const replies = [
    response([1, 2], 9, 2),
    response([3], 9, 2, 2),
    response([], 9, 2, 4),
  ];
  globalThis.fetch = (input, options = {}) => {
    calls.push({
      url: new URL(input instanceof Request ? input.url : input),
      options,
    });
    return Promise.resolve(replies.shift() ?? response());
  };
  const store = new app.TestResultsSearchStore();
  for (const offset of [0, 2, 4]) {
    await store.search(
      app.parseSearch(
        url(`artefacts=one,two&test_cases=case&limit=2&offset=${offset}`)
          .searchParams,
        families,
      ),
    );
    assert.equal(store.response?.offset, offset);
    assert.deepEqual(
      store.response.test_results.map((r) => r.test_result.id),
      offset === 0 ? [1, 2] : offset === 2 ? [3] : [],
    );
  }
  assert.equal(calls.length, 3);
  for (const call of calls) {
    assert.equal(call.url.pathname, "/v1/test-results");
    assert.deepEqual(call.url.searchParams.getAll("artefacts"), ["one", "two"]);
    assert.equal(call.options.credentials, "include");
    assert.equal(new Headers(call.options.headers).get("X-CSRF-Token"), "1");
    assert.equal(call.options.method ?? "GET", "GET");
  }
});

void test("old results, errors and session checks cannot replace a newer query or a cleared search", async () => {
  for (const oldStatus of [200, 401, 403, 500]) {
    const old = deferred();
    let sessionCalls = 0;
    globalThis.fetch = (input) => {
      const request = new URL(input instanceof Request ? input.url : input);
      if (request.pathname.endsWith("/users/me")) {
        sessionCalls++;
        return Promise.resolve(json(null));
      }
      return request.searchParams.get("artefacts") === "old"
        ? old.promise
        : Promise.resolve(response([2]));
    };
    const store = new app.TestResultsSearchStore();
    const older = store.search(
      app.parseSearch(url("artefacts=old").searchParams, families),
    );
    await store.search(
      app.parseSearch(url("artefacts=new").searchParams, families),
    );
    old.resolve(oldStatus === 200 ? response([1]) : json({}, oldStatus));
    await older;
    assert.equal(store.response?.test_results[0]?.test_result.id, 2);
    assert.equal(store.error, null);
    assert.equal(store.accessError, null);
    assert.equal(sessionCalls, 0);
  }
  const session = deferred();
  let checking = false;
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    if (request.pathname.endsWith("/users/me")) {
      checking = true;
      return session.promise;
    }
    return Promise.resolve(json({}, 403));
  };
  const store = new app.TestResultsSearchStore();
  const older = store.search(
    app.parseSearch(url("artefacts=old").searchParams, families),
  );
  await flush();
  assert.equal(checking, true);
  await store.search(app.parseSearch(url().searchParams, families));
  session.resolve(json({ id: 5, teams: [], is_admin: false }));
  await older;
  assert.equal(store.response, null);
  assert.equal(store.accessError, null);
  assert.equal(store.loading, false);
});

void test("auth revalidation accurately distinguishes logged out, permission denied, and inconclusive sessions", async () => {
  for (const [pageStatus, sessionBody, sessionStatus, expected] of [
    [401, null, 200, "requiresLogin"],
    [403, {}, 401, "requiresLogin"],
    [403, { id: 5, teams: [], is_admin: false }, 200, "forbidden"],
    [401, { id: 5, teams: [], is_admin: false }, 200, "requiresLogin"],
    [403, {}, 503, "sessionCheckFailed"],
  ]) {
    globalThis.fetch = (input) =>
      Promise.resolve(
        new URL(input instanceof Request ? input.url : input).pathname.endsWith(
          "/users/me",
        )
          ? json(sessionBody, /** @type {number} */ (sessionStatus))
          : json({}, /** @type {number} */ (pageStatus)),
      );
    const store = new app.TestResultsSearchStore();
    await store.search(
      app.parseSearch(url("artefacts=one").searchParams, families),
    );
    assert.equal(store.accessError, expected);
    assert.equal(store.loading, false);
    assert.equal(store.response, null);
  }
});

void test("cancelled session body parsing cannot overwrite the shared user cache", async () => {
  const user = {
    id: 99,
    teams: [],
    is_admin: false,
    name: "Current user",
    email: "user@example.test",
    launchpad_handle: null,
  };
  await app.userStore.refresh(() => Promise.resolve(json(user)));
  const session = deferred();
  let readingBody = false;
  const oldResponse = json(null);
  oldResponse.json = async () => {
    readingBody = true;
    const response = await session.promise;
    // eslint-disable-next-line @typescript-eslint/no-unsafe-return
    return response.json();
  };
  globalThis.fetch = (input) =>
    Promise.resolve(
      new URL(input instanceof Request ? input.url : input).pathname.endsWith(
        "/users/me",
      )
        ? oldResponse
        : json({}, 403),
    );
  const store = new app.TestResultsSearchStore();
  const older = store.search(
    app.parseSearch(url("artefacts=old").searchParams, families),
  );
  await flush();
  assert.equal(readingBody, true);
  await store.search(app.parseSearch(url().searchParams, families));
  session.resolve(json(null));
  await older;
  assert.equal(app.userStore.current?.id, user.id);
  assert.equal(store.accessError, null);
});

/** @param {string} [query] */
function mounted(query = "") {
  const target = browser.document.createElement("div");
  browser.document.body.append(target);
  const handle = app.mountSearch(
    /** @type {HTMLElement} */ (/** @type {unknown} */ (target)),
    url(query),
    families,
  );
  return {
    target,
    handle,
    destroy: async () => {
      await handle.destroy();
      target.remove();
    },
  };
}

/** @param {import('happy-dom').HTMLElement} target @param {string} text */
function button(target, text) {
  const found = Array.from(target.querySelectorAll("button")).find((b) =>
    b.textContent.includes(text),
  );
  assert.ok(found, `Missing button ${text}`);
  return found;
}

/** @param {import('happy-dom').HTMLElement} target */
function panel(target) {
  const found = target.querySelector(".condition-popover .panel");
  assert.ok(found, "An anchored picker/editor must be open");
  return /** @type {import('happy-dom').HTMLElement} */ (found);
}

/** @param {import('happy-dom').HTMLElement} target @param {string} selector @param {string} value */
async function enter(target, selector, value) {
  const input = /** @type {import('happy-dom').HTMLInputElement | null} */ (
    target.querySelector(selector)
  );
  assert.ok(input);
  input.value = value;
  input.dispatchEvent(new browser.Event("input", { bubbles: true }));
  await flush();
  return input;
}

/** @param {import('happy-dom').HTMLElement} target @param {string} label */
async function chooseFilter(target, label) {
  button(target, "+ Add filter").click();
  await flush();
  button(panel(target), label).click();
  await flush();
}

/** @param {import('happy-dom').HTMLElement} target */
async function confirmEditor(target) {
  const form = panel(target).querySelector("form");
  assert.ok(form);
  form.dispatchEvent(
    new browser.Event("submit", { bubbles: true, cancelable: true }),
  );
  await flush();
}

/** @param {import('happy-dom').HTMLElement} target @param {string} label */
function chip(target, label) {
  const found = Array.from(target.querySelectorAll("button.chip-trigger")).find(
    (element) =>
      element.getAttribute("aria-label")?.startsWith(`Edit ${label}:`),
  );
  assert.ok(found, `Missing ${label} chip`);
  return /** @type {import('happy-dom').HTMLButtonElement} */ (found);
}

void test("search actions use dense Pragma buttons with separate icon and text slots", async () => {
  const ui = mounted("view=invalid");
  try {
    await flush();
    const search = button(ui.target, "Search");
    assert.ok(search.querySelector(".button-content > .icon.left svg"));
    assert.equal(search.querySelector(".button-content > .text svg"), null);
    assert.equal(
      search.querySelector(".button-content > .text")?.textContent.trim(),
      "Search",
    );
    for (const label of [
      "+ Add filter",
      "Search",
      "Clear all",
      "Reset table view",
    ])
      assert.ok(button(ui.target, label).classList.contains("dense"), label);
  } finally {
    await ui.destroy();
  }
});

void test("mounted controls apply exact drafts, render SvGrid context and accessible base-aware links, restore history and clear", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(response([1]));
  };
  const ui = mounted();
  try {
    await flush();
    assert.match(ui.target.textContent, /Choose at least one filter/);
    assert.equal(calls.length, 0);
    assert.equal(ui.target.querySelector("input"), null);
    assert.equal(ui.target.querySelector("fieldset"), null);
    await chooseFilter(ui.target, "Artefact names");
    const input = await enter(ui.target, 'input[name="artefacts"]', "one, two");
    assert.ok(ui.target.querySelector(`label[for="${input.id}"]`));
    await confirmEditor(ui.target);
    await chooseFilter(ui.target, "Families");
    const family = /** @type {import('happy-dom').HTMLInputElement | null} */ (
      ui.target.querySelector('input[value="snap"]')
    );
    assert.ok(family);
    assert.equal(
      family.closest("label")?.textContent.trim(),
      "Configured-route",
    );
    family.click();
    await flush();
    await confirmEditor(ui.target);
    assert.equal(calls.length, 0, "draft edits do not fetch before applying");
    assert.match(ui.target.textContent, /Changes not applied/);
    assert.match(chip(ui.target, "Families").textContent, /Configured-route/);
    button(ui.target, "Search").click();
    await flush();
    assert.deepEqual(calls[0]?.searchParams.getAll("artefacts"), [
      "one",
      "two",
    ]);
    assert.equal(calls[0]?.searchParams.get("families"), "snap");
    assert.equal(ui.handle.history.length, 2);
    assert.ok(
      ui.target.querySelector(".sv-grid-root"),
      "actual SvGrid must mount",
    );
    assert.match(
      ui.target.textContent,
      /1 matching test results on the server/,
    );
    assert.match(ui.target.textContent, /only this loaded page/);
    assert.equal(
      ui.target
        .querySelector('tbody td[data-col-id="family"]')
        ?.textContent.trim(),
      "Configured-route",
    );
    for (const text of [
      "example artefact",
      "case 1",
      "FAILED",
      "1.2",
      "stable",
      "test lab",
      "smoke",
    ])
      assert.ok(ui.target.textContent.includes(text), text);
    const link = /** @type {import('happy-dom').HTMLAnchorElement | null} */ (
      ui.target.querySelector('a[aria-label="View Run for case 1"]')
    );
    assert.ok(link, ui.target.innerHTML);
    assert.equal(
      link.getAttribute("href"),
      "/custom/base/configured-route/42?testExecutionId=7&testResultId=1",
    );
    link.focus();
    assert.equal(browser.document.activeElement, link);
    const applied = ui.handle.history[1];
    ui.handle.restore(url("test_cases=restored"));
    await flush();
    assert.equal(calls.at(-1)?.searchParams.get("test_cases"), "restored");
    ui.handle.restore(applied);
    await flush();
    assert.equal(
      chip(ui.target, "Artefact names").title,
      "Artefact names: one, two",
    );
    assert.deepEqual(calls.at(-1)?.searchParams.getAll("artefacts"), [
      "one",
      "two",
    ]);
    button(ui.target, "Clear all").click();
    await flush();
    assert.equal(ui.target.querySelector(".sv-grid-root"), null);
    assert.match(ui.target.textContent, /Choose at least one filter/);
    assert.equal(calls.length, 3, "clear must not fetch unfiltered results");
  } finally {
    await ui.destroy();
  }
});

void test("native post-opening focus works for pointer and Enter on picker, text and checkbox chips", async () => {
  globalThis.fetch = () => Promise.resolve(response());
  for (const [query, label] of [
    ["", ""],
    ["artefacts=known-value", "Artefact names"],
    ["test_result_statuses=FAILED", "Test result statuses"],
    ["families=snap", "Families"],
  ]) {
    for (const mode of ["pointer", "Enter"]) {
      const ui = mounted(query);
      try {
        await flush();
        const trigger = label
          ? chip(ui.target, label)
          : button(ui.target, "+ Add filter");
        trigger.focus();
        if (mode === "pointer") trigger.click();
        else
          trigger.dispatchEvent(
            new browser.KeyboardEvent("keydown", {
              key: "Enter",
              bubbles: true,
              cancelable: true,
            }),
          );
        await flush();
        const input = panel(ui.target).querySelector("input");
        assert.ok(input);
        assert.ok(
          browser.document.activeElement === input,
          `${mode} must focus ${label || "picker"} after native opening`,
        );
        if (!label) {
          input.value = "environ";
          input.dispatchEvent(new browser.Event("input", { bubbles: true }));
          await flush();
          assert.equal(
            panel(ui.target).querySelectorAll("li button").length,
            1,
          );
        }
        input.dispatchEvent(
          new browser.KeyboardEvent("keydown", {
            key: "Escape",
            bubbles: true,
            cancelable: true,
          }),
        );
        await flush();
        assert.equal(ui.target.querySelector(".panel"), null);
        assert.ok(
          browser.document.activeElement === trigger,
          "Escape must return focus to the opener",
        );
      } finally {
        await ui.destroy();
      }
    }
  }
});

void test("open overlays use visible viewport bounds rather than tall documents and follow resize/scroll", async () => {
  globalThis.fetch = () => Promise.resolve(response());
  const ui = mounted("test_result_statuses=FAILED");
  const originalWidth = browser.innerWidth;
  const originalHeight = browser.innerHeight;
  const documentHeight = Object.getOwnPropertyDescriptor(
    browser.document.documentElement,
    "scrollHeight",
  );
  Object.defineProperty(browser.document.documentElement, "scrollHeight", {
    configurable: true,
    value: 1004,
  });
  try {
    await flush();
    const trigger = button(ui.target, "+ Add filter");
    trigger.click();
    await flush();
    const content = panel(ui.target);
    const overlay = /** @type {import('happy-dom').HTMLElement | null} */ (
      content.parentElement
    );
    assert.ok(overlay);
    // Happy DOM has no layout; supply the real QA geometry and verify the
    // resulting viewport constraints, leaving scrollbar reachability to browser QA.
    content.getBoundingClientRect = () => new browser.DOMRect(0, 0, 368, 375);
    overlay.getBoundingClientRect = () => new browser.DOMRect(0, 0, 368, 375);
    let anchorY = 132;
    trigger.getBoundingClientRect = () =>
      new browser.DOMRect(browser.innerWidth - 150, anchorY, 108, 26);
    for (const [width, height] of [
      [800, 480],
      [1440, 500],
      [800, 360],
    ]) {
      browser.happyDOM.setViewport({ width, height });
      browser.dispatchEvent(new browser.Event("resize"));
      await flush();
      const top = Number.parseFloat(overlay.style.top);
      const left = Number.parseFloat(overlay.style.left);
      const maxHeight = Number.parseFloat(overlay.style.maxHeight);
      assert.ok(
        top >= 16 && top + Math.min(375, maxHeight) <= height - 16,
        `${width}x${height} overlay must fit vertically`,
      );
      assert.ok(
        left >= 16 && left + 368 <= width - 16,
        `${width}x${height} overlay must fit horizontally`,
      );
      assert.ok(
        maxHeight < height - 32,
        "height must account for its anchor, not just the full viewport",
      );
    }
    const previousTop = Number.parseFloat(overlay.style.top);
    anchorY = 20;
    browser.document.dispatchEvent(new browser.Event("scroll"));
    await flush();
    assert.ok(
      Number.parseFloat(overlay.style.top) < previousTop,
      "scrolling must retain the trigger anchor",
    );
    assert.ok(
      browser.document.activeElement === content.querySelector("input"),
      "repositioning must not disturb input focus",
    );
  } finally {
    await ui.destroy();
    browser.happyDOM.setViewport({
      width: originalWidth,
      height: originalHeight,
    });
    if (documentHeight)
      Object.defineProperty(
        browser.document.documentElement,
        "scrollHeight",
        documentHeight,
      );
    else
      Reflect.deleteProperty(browser.document.documentElement, "scrollHeight");
  }
});

void test("searchable picker offers only eight unused fields and never creates an empty chip", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(response());
  };
  const ui = mounted();
  try {
    await flush();
    button(ui.target, "+ Add filter").click();
    await flush();
    const picker = panel(ui.target);
    assert.equal(
      picker.closest('[role="dialog"]')?.getAttribute("aria-label"),
      "Add filter",
    );
    assert.ok(
      browser.document.activeElement === picker.querySelector("input"),
      "opening must focus the picker input after the native transition",
    );
    assert.deepEqual(
      Array.from(picker.querySelectorAll("li button")).map((item) =>
        item.textContent.trim(),
      ),
      [
        "Families",
        "Test result statuses",
        "Artefact names",
        "Versions",
        "Tracks",
        "Environments",
        "Test plans",
        "Test cases",
      ],
    );
    await enter(picker, 'input[type="search"]', "  TEST  ");
    assert.equal(picker.querySelectorAll("li button").length, 3);
    await enter(picker, 'input[type="search"]', "not-a-filter");
    assert.match(picker.textContent, /No matching filters/);
    await enter(picker, 'input[type="search"]', "artefact");
    button(picker, "Artefact names").click();
    await flush();
    assert.equal(button(panel(ui.target), "Add filter").disabled, true);
    await enter(ui.target, 'input[name="artefacts"]', " , , ");
    await confirmEditor(ui.target);
    assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 0);
    assert.equal(calls, 0);
    await enter(ui.target, 'input[name="artefacts"]', "alpha, beta,alpha");
    await confirmEditor(ui.target);
    const condition = chip(ui.target, "Artefact names");
    assert.equal(browser.document.activeElement, condition);
    assert.equal(
      condition.querySelector("button"),
      null,
      "chip edit and remove cannot be nested buttons",
    );
    assert.match(condition.textContent, /alpha \+1/);
    assert.equal(condition.title, "Artefact names: alpha, beta");
    button(ui.target, "+ Add filter").click();
    await flush();
    await enter(panel(ui.target), 'input[type="search"]', "artefact");
    assert.equal(
      panel(ui.target).querySelectorAll("li button").length,
      0,
      "an existing field cannot be added twice",
    );
    button(panel(ui.target), "Cancel").click();
    await flush();
    const remove = /** @type {import('happy-dom').HTMLButtonElement | null} */ (
      ui.target.querySelector(
        'button[aria-label="Remove Artefact names filter"]',
      )
    );
    assert.ok(remove);
    assert.ok(remove.querySelector(".button-content > .icon.left svg"));
    remove.click();
    await flush();
    assert.equal(
      browser.document.activeElement,
      button(ui.target, "+ Add filter"),
    );
    await chooseFilter(ui.target, "Artefact names");
    assert.equal(ui.target.querySelector('input[name="artefacts"]')?.value, "");
    assert.equal(calls, 0);
  } finally {
    await ui.destroy();
  }
});

void test("all eight chip editors preserve configured families, checkbox statuses and exact comma values until Search", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(response());
  };
  const ui = mounted();
  try {
    await flush();
    await chooseFilter(ui.target, "Families");
    for (const family of families) {
      const checkbox =
        /** @type {import('happy-dom').HTMLInputElement | null} */ (
          panel(ui.target).querySelector(`input[value="${family.api_name}"]`)
        );
      assert.ok(checkbox);
      checkbox.click();
    }
    await flush();
    await confirmEditor(ui.target);
    assert.match(
      chip(ui.target, "Families").title,
      /Configured-route, Another-route/,
    );
    await chooseFilter(ui.target, "Test result statuses");
    assert.equal(
      panel(ui.target).querySelectorAll('input[type="checkbox"]').length,
      3,
    );
    for (const status of ["PASSED", "FAILED", "SKIPPED"]) {
      const checkbox =
        /** @type {import('happy-dom').HTMLInputElement | null} */ (
          panel(ui.target).querySelector(`input[value="${status}"]`)
        );
      assert.ok(checkbox);
      checkbox.click();
    }
    await flush();
    await confirmEditor(ui.target);
    for (const [key, label] of [
      ["artefacts", "Artefact names"],
      ["artefact_versions", "Versions"],
      ["artefact_tracks", "Tracks"],
      ["environments", "Environments"],
      ["test_plans", "Test plans"],
      ["test_cases", "Test cases"],
    ]) {
      await chooseFilter(ui.target, label);
      await enter(
        ui.target,
        `input[name="${key}"]`,
        ` first ${key}, second+${key}, first ${key}, `,
      );
      await confirmEditor(ui.target);
      assert.equal(
        chip(ui.target, label).title,
        `${label}: first ${key}, second+${key}`,
      );
    }
    assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 8);
    button(ui.target, "+ Add filter").click();
    await flush();
    assert.match(panel(ui.target).textContent, /All filters are in use/);
    assert.equal(panel(ui.target).querySelectorAll("li").length, 0);
    button(panel(ui.target), "Cancel").click();
    await flush();
    assert.equal(calls.length, 0);
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls.length, 1);
    assert.deepEqual(
      calls[0].searchParams.getAll("families"),
      families.map((family) => family.api_name),
    );
    assert.deepEqual(calls[0].searchParams.getAll("test_result_statuses"), [
      "PASSED",
      "FAILED",
      "SKIPPED",
    ]);
    for (const key of app.SEARCH_FILTERS.slice(2))
      assert.deepEqual(calls[0].searchParams.getAll(key), [
        `first ${key}`,
        `second+${key}`,
      ]);
    assert.doesNotMatch(ui.target.textContent, /Changes not applied/);
    assert.match(ui.target.textContent, /Results for applied query/);
  } finally {
    await ui.destroy();
  }
});

void test("confirmed add/edit/remove drafts never fetch or replace applied results; Search applies the complete draft and resets pagination", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(response([1, 2], 20, 2, 2));
  };
  const ui = mounted("artefacts=old&test_cases=applied&limit=2&offset=2");
  try {
    await flush();
    chip(ui.target, "Artefact names").click();
    await flush();
    assert.equal(
      ui.target.querySelector('input[name="artefacts"]')?.value,
      "old",
    );
    await enter(ui.target, 'input[name="artefacts"]', "new, second");
    await confirmEditor(ui.target);
    const remove = /** @type {import('happy-dom').HTMLButtonElement | null} */ (
      ui.target.querySelector('button[aria-label="Remove Test cases filter"]')
    );
    assert.ok(remove);
    remove.click();
    await flush();
    await chooseFilter(ui.target, "Environments");
    await enter(ui.target, 'input[name="environments"]', "lab");
    await confirmEditor(ui.target);
    assert.equal(calls.length, 1);
    assert.equal(ui.handle.history.length, 1);
    assert.match(ui.target.textContent, /Changes not applied/);
    assert.match(ui.target.textContent, /Results for previous query/);
    assert.match(ui.target.textContent, /case 1/);
    assert.equal(button(ui.target, "Next page").disabled, true);
    assert.equal(button(ui.target, "Previous page").disabled, true);
    button(ui.target, "Next page").click();
    assert.equal(calls.length, 1);
    chip(ui.target, "Artefact names").click();
    await flush();
    await enter(ui.target, 'input[name="artefacts"]', "unconfirmed");
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls.length, 2);
    assert.deepEqual(calls[1].searchParams.getAll("artefacts"), [
      "new",
      "second",
    ]);
    assert.equal(calls[1].searchParams.get("environments"), "lab");
    assert.equal(calls[1].searchParams.has("test_cases"), false);
    assert.equal(calls[1].searchParams.has("offset"), false);
    assert.equal(ui.target.querySelector(".panel"), null);
    assert.doesNotMatch(ui.target.textContent, /Changes not applied/);
    ui.handle.restore(url("artefacts=old&test_cases=applied&limit=2&offset=2"));
    await flush();
    chip(ui.target, "Artefact names").click();
    await flush();
    await enter(ui.target, 'input[name="artefacts"]', "old");
    await confirmEditor(ui.target);
    assert.doesNotMatch(ui.target.textContent, /Changes not applied/);
    assert.equal(button(ui.target, "Next page").disabled, false);
  } finally {
    await ui.destroy();
  }
});

void test("cancel, Escape, outside dismissal and switching popovers discard edits, with meaningful focus and intentional removal", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(response());
  };
  const ui = mounted("artefacts=original&test_result_statuses=FAILED");
  const outside = browser.document.createElement("button");
  outside.textContent = "Outside control";
  browser.document.body.append(outside);
  try {
    await flush();
    for (const dismissal of ["Cancel", "Escape", "outside"]) {
      const trigger = chip(ui.target, "Artefact names");
      trigger.click();
      await flush();
      const input = await enter(
        ui.target,
        'input[name="artefacts"]',
        "discard me",
      );
      assert.ok(
        browser.document.activeElement === input,
        "opening must focus the editor input after the native transition",
      );
      const tab = new browser.KeyboardEvent("keydown", {
        key: "Tab",
        bubbles: true,
        cancelable: true,
      });
      input.dispatchEvent(tab);
      assert.equal(
        tab.defaultPrevented,
        false,
        "Tab must retain normal browser navigation",
      );
      if (dismissal === "Cancel") button(panel(ui.target), "Cancel").click();
      else if (dismissal === "Escape")
        input.dispatchEvent(
          new browser.KeyboardEvent("keydown", {
            key: "Escape",
            bubbles: true,
            cancelable: true,
          }),
        );
      else {
        outside.focus();
        outside.click();
      }
      await flush();
      assert.equal(ui.target.querySelector(".panel"), null);
      assert.equal(
        browser.document.activeElement,
        dismissal === "outside" ? outside : trigger,
      );
      assert.equal(
        chip(ui.target, "Artefact names").title,
        "Artefact names: original",
      );
      assert.doesNotMatch(ui.target.textContent, /Changes not applied/);
    }
    chip(ui.target, "Test result statuses").click();
    await flush();
    const failed = /** @type {import('happy-dom').HTMLInputElement | null} */ (
      panel(ui.target).querySelector('input[value="FAILED"]')
    );
    assert.ok(failed?.checked);
    failed.click();
    await flush();
    assert.equal(button(panel(ui.target), "Save changes").disabled, true);
    assert.match(panel(ui.target).textContent, /or remove this filter/);
    button(ui.target, "+ Add filter").click();
    await flush();
    assert.equal(ui.target.querySelectorAll(".panel").length, 1);
    assert.match(panel(ui.target).textContent, /Find a filter/);
    button(panel(ui.target), "Cancel").click();
    await flush();
    chip(ui.target, "Test result statuses").click();
    await flush();
    assert.equal(
      panel(ui.target).querySelector('input[value="FAILED"]')?.checked,
      true,
      "switching does not save cleared checkboxes",
    );
    button(panel(ui.target), "Remove filter").click();
    await flush();
    assert.equal(
      browser.document.activeElement,
      button(ui.target, "+ Add filter"),
    );
    assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 1);
    assert.equal(calls, 1);
  } finally {
    outside.remove();
    await ui.destroy();
  }
});

void test("URL restoration resets open editors and restores full long/repeated/comma values; removing the final chip and clearing never fetch unfiltered data", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(response());
  };
  const long = "long-exact-artefact-name-".repeat(8);
  const applied = url(
    `artefacts=${long},second&artefacts=third&families=another-api-family`,
  );
  const ui = mounted(applied.search.slice(1));
  try {
    await flush();
    const trigger = chip(ui.target, "Artefact names");
    assert.match(trigger.textContent, /\+2/);
    assert.equal(trigger.title, `Artefact names: ${long}, second, third`);
    assert.equal(
      trigger.getAttribute("aria-label"),
      `Edit Artefact names: ${long}, second, third`,
    );
    assert.equal(chip(ui.target, "Families").title, "Families: Another-route");
    trigger.click();
    await flush();
    assert.equal(
      ui.target.querySelector('input[name="artefacts"]')?.value,
      `${long}, second, third`,
    );
    await enter(ui.target, 'input[name="artefacts"]', "transient");
    ui.handle.restore(url("test_cases=restored"));
    await flush();
    assert.equal(ui.target.querySelector(".panel"), null);
    assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 1);
    assert.equal(chip(ui.target, "Test cases").title, "Test cases: restored");
    ui.handle.restore(applied);
    await flush();
    assert.equal(
      chip(ui.target, "Artefact names").title,
      `Artefact names: ${long}, second, third`,
    );
    assert.equal(calls.length, 3);
    button(ui.target, "Clear all").click();
    await flush();
    assert.equal(ui.handle.history.at(-1)?.search, "");
    assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 0);
    assert.equal(calls.length, 3);
    await chooseFilter(ui.target, "Test cases");
    await enter(ui.target, 'input[name="test_cases"]', "one");
    await confirmEditor(ui.target);
    button(ui.target, "Search").click();
    await flush();
    const remove = /** @type {import('happy-dom').HTMLButtonElement | null} */ (
      ui.target.querySelector('button[aria-label="Remove Test cases filter"]')
    );
    assert.ok(remove);
    remove.click();
    await flush();
    assert.match(ui.target.textContent, /clear the previous query/);
    assert.match(ui.target.textContent, /Results for previous query/);
    assert.equal(calls.length, 4);
    button(ui.target, "Search").click();
    await flush();
    assert.equal(ui.handle.history.at(-1)?.search, "");
    assert.equal(ui.target.querySelector(".sv-grid-root"), null);
    assert.equal(calls.length, 4);
    assert.ok(
      calls.every((call) =>
        app.SEARCH_FILTERS.some((key) => call.searchParams.has(key)),
      ),
    );
    await chooseFilter(ui.target, "Test cases");
    await enter(ui.target, 'input[name="test_cases"]', "draft only");
    await confirmEditor(ui.target);
    button(ui.target, "Clear all").click();
    await flush();
    assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 0);
    assert.equal(
      calls.length,
      4,
      "clearing drafts on an already-empty URL is safe too",
    );
  } finally {
    await ui.destroy();
  }
});

void test("mounted pagination disables repeated clicks while loading, maintains applied filters and stops on short data", async () => {
  const next = deferred();
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    calls.push(request);
    return request.searchParams.get("offset") === "2"
      ? next.promise
      : Promise.resolve(response([1, 2], 8, 2));
  };
  const ui = mounted("artefacts=one&limit=2");
  try {
    await flush();
    button(ui.target, "Next page").click();
    button(ui.target, "Next page").click();
    await flush();
    assert.match(ui.target.textContent, /Loading test results/);
    assert.equal(calls.length, 2);
    assert.equal(calls[1].searchParams.get("offset"), "2");
    assert.equal(calls[1].searchParams.get("artefacts"), "one");
    next.resolve(response([3], 8, 2, 2));
    await flush();
    assert.equal(button(ui.target, "Next page").disabled, true);
    assert.equal(button(ui.target, "Previous page").disabled, false);
    assert.match(ui.target.textContent, /case 3/);
    assert.doesNotMatch(ui.target.textContent, /case 1/);
    button(ui.target, "Previous page").click();
    await flush();
    assert.equal(calls.length, 3);
    assert.equal(calls[2].searchParams.get("offset"), null);
  } finally {
    await ui.destroy();
  }
});

void test("mounted grid filtering and sorting stay local without changing the backend total", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(response([2, 1], 12));
  };
  const ui = mounted("test_result_statuses=FAILED");
  try {
    await flush();
    const cells = () =>
      Array.from(
        ui.target.querySelectorAll('tbody td[data-col-id="testCase"]'),
      ).map((cell) => cell.textContent.trim());
    assert.deepEqual(cells(), ["case 2", "case 1"]);
    const sort =
      /** @type {import('happy-dom').HTMLButtonElement | undefined} */ (
        Array.from(
          ui.target.querySelectorAll("button.sv-grid-header-sort"),
        ).find((element) => element.textContent.includes("Test case"))
      );
    assert.ok(sort);
    sort.click();
    await flush();
    assert.deepEqual(cells(), ["case 1", "case 2"]);
    assert.deepEqual(
      app.decodeView(ui.handle.history.at(-1)?.searchParams.get("view") ?? null)
        ?.sorting,
      [{ id: "testCase", desc: false }],
    );
    const local = /** @type {import('happy-dom').HTMLInputElement | null} */ (
      ui.target.querySelector(".sv-grid-global-filter input")
    );
    assert.ok(local);
    local.focus();
    local.value = "no such case";
    local.dispatchEvent(new browser.Event("input", { bubbles: true }));
    await flush();
    assert.deepEqual(cells(), []);
    assert.match(
      ui.target.textContent,
      /No loaded results match the local grid filters/,
    );
    assert.match(
      ui.target.textContent,
      /12 matching test results on the server/,
    );
    assert.equal(calls, 1);
    assert.equal(
      ui.handle.history.length,
      1,
      "grid changes replace, not push history",
    );
    assert.equal(
      app.decodeView(ui.handle.history[0].searchParams.get("view"))
        ?.globalFilter,
      "no such case",
    );
    assert.equal(
      browser.document.activeElement,
      local,
      "automatic view writes preserve input focus",
    );
    // Return every customization to default using the grid itself (not Reset).
    sort.click();
    await flush();
    sort.click();
    await flush();
    local.value = "";
    local.dispatchEvent(new browser.Event("input", { bubbles: true }));
    await flush();
    assert.equal(ui.handle.history[0].searchParams.has("view"), false);
    assert.equal(calls, 1);
  } finally {
    await ui.destroy();
  }
});

void test("view is presentation-only in query identity and never appears in API parameters", () => {
  const params = url(
    "artefacts=one&artefacts=two&limit=2&offset=2&view=invalid",
  ).searchParams;
  const applied = app.parseSearch(params, families);
  assert.deepEqual(applied.problems, []);
  assert.equal(
    app
      .searchParams(applied.filters, applied.limit, applied.offset)
      .has("view"),
    false,
  );
  assert.equal(
    app.searchQueryString(params),
    "artefacts=one&artefacts=two&limit=2&offset=2",
  );
  params.set("view", "different");
  assert.equal(
    app.searchQueryString(params),
    "artefacts=one&artefacts=two&limit=2&offset=2",
  );
  params.append("unsupported", "still blocks");
  assert.match(
    app.parseSearch(params, families).problems[0],
    /Unsupported URL filter/,
  );
});

void test("explicit Search retries when URL encoding changes but backend query identity does not", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(response());
  };
  const ui = mounted("artefacts=one%20two&limit=50");
  try {
    await flush();
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls, 2);
    assert.equal(
      ui.handle.history.at(-1)?.searchParams.get("artefacts"),
      "one two",
    );
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls, 3);
  } finally {
    await ui.destroy();
  }
});

void test("presentation history adapter preserves repeated queries, base, fragment and skips stale/outgoing writes", async () => {
  let current = new URL(
    `${url("artefacts=one&artefacts=two&limit=2&offset=4").href}#anchor`,
  );
  const initial = current.href;
  let writes = 0;
  const adapter = {
    currentUrl: () => current,
    /** @param {URL} next */
    replace: (next) => {
      current = next;
      writes++;
      return Promise.resolve();
    },
  };
  await app.replaceSearchView("encoded-view", initial, adapter);
  assert.equal(writes, 1);
  assert.deepEqual(current.searchParams.getAll("artefacts"), ["one", "two"]);
  assert.equal(current.pathname, "/custom/base/test-results");
  assert.equal(current.hash, "#anchor");
  assert.equal(current.searchParams.get("offset"), "4");
  await app.replaceSearchView("old-grid", initial, adapter);
  assert.equal(writes, 1);
  await app.replaceSearchView("old-grid", current.href, {
    ...adapter,
    currentUrl: () => null,
  });
  assert.equal(writes, 1);
  await app.replaceSearchView(null, current.href, adapter);
  assert.equal(current.href, initial);
});

/** @param {import('happy-dom').HTMLElement} target */
function gridCases(target) {
  return Array.from(
    target.querySelectorAll('tbody td[data-col-id="testCase"]'),
  ).map((cell) => cell.textContent.trim());
}

void test("shared URL restores sorting, global, column, facet and visibility state; removing it restores defaults without remount/fetch", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(response([3, 2, 1], 12));
  };
  const view = app.encodeView({
    sorting: [
      { id: "testCase", desc: false },
      { id: "missing", desc: true },
      { id: "run", desc: true },
    ],
    globalFilter: "case",
    columnFilters: {
      testCase: { operator: "contains", value: "2" },
      missing: { operator: "contains", value: "never" },
      run: { operator: "contains", value: "never" },
    },
    facetFilters: { status: ["FAILED"], missing: ["never"], run: ["never"] },
    hiddenColumns: ["version", "missing"],
    shownColumns: ["missing", "version"],
  });
  const ui = mounted(`artefacts=one&view=${view}`);
  try {
    await flush();
    const grid = ui.target.querySelector(".sv-grid-root");
    assert.ok(grid);
    assert.deepEqual(gridCases(ui.target), ["case 2"]);
    assert.equal(
      ui.target.querySelector('th[data-svgrid-header-col="version"]'),
      null,
    );
    assert.equal(
      ui.target.querySelector(".sv-grid-global-filter input")?.value,
      "case",
    );
    assert.equal(
      ui.handle.replacements.length,
      0,
      "restoring a URL must not echo a rewrite",
    );
    ui.handle.restore(url("artefacts=one"));
    await flush();
    assert.equal(ui.target.querySelector(".sv-grid-root"), grid);
    assert.deepEqual(gridCases(ui.target), ["case 3", "case 2", "case 1"]);
    assert.ok(ui.target.querySelector('th[data-svgrid-header-col="version"]'));
    assert.equal(
      ui.target.querySelector(".sv-grid-global-filter input")?.value,
      "",
    );
    assert.equal(calls, 1);
    assert.equal(ui.handle.replacements.length, 0);
  } finally {
    await ui.destroy();
  }
});

void test("view history changes preserve confirmed drafts, active editor, grid identity and focus", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(response([2, 1]));
  };
  const ui = mounted("artefacts=one&artefacts=two");
  try {
    await flush();
    await chooseFilter(ui.target, "Test cases");
    await enter(ui.target, 'input[name="test_cases"]', "confirmed");
    await confirmEditor(ui.target);
    chip(ui.target, "Artefact names").click();
    await flush();
    const editor = await enter(
      ui.target,
      'input[name="artefacts"]',
      "unconfirmed",
    );
    const grid = ui.target.querySelector(".sv-grid-root");
    const view = app.encodeView({
      sorting: [{ id: "testCase", desc: false }],
      globalFilter: "case 1",
    });
    ui.handle.restore(url(`artefacts=one&artefacts=two&view=${view}`));
    await flush();
    assert.equal(ui.target.querySelector('input[name="artefacts"]'), editor);
    assert.equal(editor.value, "unconfirmed");
    assert.equal(browser.document.activeElement, editor);
    assert.equal(chip(ui.target, "Test cases").title, "Test cases: confirmed");
    assert.match(ui.target.textContent, /Changes not applied/);
    assert.equal(ui.target.querySelector(".sv-grid-root"), grid);
    assert.deepEqual(gridCases(ui.target), ["case 1"]);
    ui.handle.restore(url("artefacts=one&artefacts=two"));
    await flush();
    assert.equal(browser.document.activeElement, editor);
    assert.deepEqual(gridCases(ui.target), ["case 2", "case 1"]);
    assert.equal(calls, 1);
  } finally {
    await ui.destroy();
  }
});

void test("view-only updates do not cancel/refetch pending results or auth checks", async () => {
  for (const auth of [false, true]) {
    const pending = deferred();
    /** @type {AbortSignal[]} */
    const signals = [];
    let calls = 0;
    globalThis.fetch = (input, options) => {
      calls++;
      if (options?.signal) signals.push(options.signal);
      const request = new URL(input instanceof Request ? input.url : input);
      if (auth && !request.pathname.endsWith("/users/me"))
        return Promise.resolve(json({}, 403));
      return pending.promise;
    };
    const ui = mounted("artefacts=one");
    try {
      await flush();
      const before = calls;
      const view = app.encodeView({ globalFilter: "case 1" });
      ui.handle.restore(url(`artefacts=one&view=${view}`));
      await flush();
      assert.equal(calls, before);
      assert.ok(signals.length);
      assert.ok(signals.every((signal) => !signal.aborted));
      pending.resolve(auth ? json(null) : response([2, 1]));
      await flush();
      if (auth) assert.match(ui.target.textContent, /need to be logged in/);
      else assert.deepEqual(gridCases(ui.target), ["case 1"]);
    } finally {
      await ui.destroy();
    }
  }
});

void test("outgoing grid callbacks cannot write over a newer query or recreate view after clear", async () => {
  const pending = deferred();
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return calls === 1 ? Promise.resolve(response([2, 1])) : pending.promise;
  };
  const ui = mounted("artefacts=old");
  try {
    await flush();
    const sort = /** @type {import('happy-dom').HTMLButtonElement | null} */ (
      ui.target.querySelector(
        '[data-svgrid-header-col="testCase"] button.sv-grid-header-sort',
      )
    );
    assert.ok(sort);
    sort.click();
    // The grid's sort callback is effect-driven; navigate before it flushes.
    ui.handle.restore(url("artefacts=new"));
    await flush();
    assert.equal(calls, 2);
    assert.equal(ui.handle.currentUrl.search, "?artefacts=new");
    assert.equal(ui.handle.replacements.length, 0);
    pending.resolve(response([3]));
    await flush();
    const incomingSort =
      /** @type {import('happy-dom').HTMLButtonElement | null} */ (
        ui.target.querySelector(
          '[data-svgrid-header-col="testCase"] button.sv-grid-header-sort',
        )
      );
    assert.ok(incomingSort);
    incomingSort.click();
    button(ui.target, "Clear all").click();
    await flush();
    assert.equal(ui.handle.currentUrl.search, "");
    assert.equal(ui.target.querySelector(".sv-grid-root"), null);
    assert.equal(calls, 2);
  } finally {
    await ui.destroy();
  }
});

void test("table view survives pagination, changed Search and identical Search retry; reset only view and Clear all resets everything", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(response([2, 1], 12, 2));
  };
  const view = app.encodeView({
    sorting: [{ id: "testCase", desc: false }],
    hiddenColumns: ["version"],
  });
  const ui = mounted(`artefacts=one&limit=2&view=${view}`);
  try {
    await flush();
    assert.deepEqual(gridCases(ui.target), ["case 1", "case 2"]);
    button(ui.target, "Next page").click();
    await flush();
    assert.equal(ui.handle.history.at(-1)?.searchParams.get("view"), view);
    assert.equal(calls.length, 2);
    assert.equal(calls[1].searchParams.get("offset"), "2");
    assert.deepEqual(gridCases(ui.target), ["case 1", "case 2"]);
    assert.equal(
      ui.target.querySelector('th[data-svgrid-header-col="version"]'),
      null,
    );
    chip(ui.target, "Artefact names").click();
    await flush();
    await enter(ui.target, 'input[name="artefacts"]', "changed");
    await confirmEditor(ui.target);
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls.length, 3);
    assert.equal(calls[2].searchParams.get("artefacts"), "changed");
    assert.equal(ui.handle.history.at(-1)?.searchParams.get("view"), view);
    assert.deepEqual(gridCases(ui.target), ["case 1", "case 2"]);
    // Identical explicit Search still retries, and discards unconfirmed edits.
    chip(ui.target, "Artefact names").click();
    await flush();
    await enter(ui.target, 'input[name="artefacts"]', "unconfirmed");
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls.length, 4);
    assert.equal(calls[3].searchParams.get("artefacts"), "changed");
    assert.equal(ui.target.querySelector(".panel"), null);
    assert.equal(ui.handle.history.at(-1)?.searchParams.get("view"), view);
    const grid = ui.target.querySelector(".sv-grid-root");
    button(ui.target, "Reset table view").click();
    await flush();
    assert.equal(calls.length, 4);
    assert.equal(ui.target.querySelector(".sv-grid-root"), grid);
    assert.equal(ui.handle.history.at(-1)?.searchParams.has("view"), false);
    assert.deepEqual(gridCases(ui.target), ["case 2", "case 1"]);
    assert.ok(ui.target.querySelector('th[data-svgrid-header-col="version"]'));
    ui.handle.restore(url(`artefacts=changed&view=${view}`));
    await flush();
    const beforeClear = calls.length;
    button(ui.target, "Clear all").click();
    await flush();
    assert.equal(calls.length, beforeClear);
    assert.equal(ui.handle.history.at(-1)?.search, "");
    assert.equal(ui.target.querySelector(".sv-grid-root"), null);
    assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 0);
    assert.ok(calls.every((request) => !request.searchParams.has("view")));
  } finally {
    await ui.destroy();
  }
});

void test("malformed/oversized views and inapplicable column refs remain usable, and view-only URLs never fetch", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(response([2, 1]));
  };
  for (const view of [
    "malformed",
    "a".repeat(8193),
    app.encodeView({
      sorting: [{ id: "run", desc: true }],
      facetFilters: { missing: ["never"] },
    }),
  ]) {
    const ui = mounted(`artefacts=one&view=${view}`);
    try {
      await flush();
      assert.deepEqual(gridCases(ui.target), ["case 2", "case 1"]);
      const before = calls;
      ui.handle.restore(url(`view=${view}&limit=2&offset=2`));
      await flush();
      assert.equal(calls, before);
      assert.match(ui.target.textContent, /Choose at least one filter/);
      await chooseFilter(ui.target, "Artefact names");
      await enter(ui.target, 'input[name="artefacts"]', "draft");
      await confirmEditor(ui.target);
      chip(ui.target, "Artefact names").click();
      await flush();
      button(ui.target, "Clear all").click();
      await flush();
      assert.equal(ui.target.querySelector(".panel"), null);
      assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 0);
    } finally {
      await ui.destroy();
    }
  }
});

void test("actual grid column/facet filters and visibility controls update a shareable URL without fetching or closing menus", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(response([2, 1]));
  };
  const ui = mounted("artefacts=one&artefacts=two");
  try {
    await flush();
    const filter = /** @type {import('happy-dom').HTMLButtonElement | null} */ (
      ui.target.querySelector('button[aria-label="Filter Test case"]')
    );
    assert.ok(filter);
    filter.click();
    await flush();
    await enter(ui.target, ".sv-grid-menu-condition-value", "case");
    let shared = app.decodeView(
      ui.handle.history.at(-1)?.searchParams.get("view") ?? null,
    );
    assert.deepEqual(shared?.columnFilters, {
      testCase: { operator: "contains", value: "case" },
    });
    const caseTwo = Array.from(
      ui.target.querySelectorAll('.sv-grid-menu [role="option"]'),
    ).find((option) => option.textContent.includes("case 2"));
    assert.ok(
      caseTwo,
      ui.target.querySelector(".sv-grid-filter-menu")?.outerHTML,
    );
    caseTwo.dispatchEvent(new browser.MouseEvent("click", { bubbles: true }));
    await flush();
    shared = app.decodeView(
      ui.handle.history.at(-1)?.searchParams.get("view") ?? null,
    );
    assert.deepEqual(shared?.facetFilters, { testCase: ["case 1"] });
    assert.deepEqual(gridCases(ui.target), ["case 1"]);
    assert.ok(
      ui.target.querySelector(".sv-grid-filter-menu"),
      "URL echo must not close the active menu",
    );
    // Dismiss via the grid's own backdrop, then use its built-in chooser.
    const backdrop = /** @type {import('happy-dom').HTMLElement | null} */ (
      ui.target.querySelector(".sv-grid-menu-backdrop")
    );
    assert.ok(backdrop);
    backdrop.click();
    await flush();
    const menu = /** @type {import('happy-dom').HTMLButtonElement | null} */ (
      ui.target.querySelector('button[aria-label="Artefact column menu"]')
    );
    assert.ok(menu);
    menu.click();
    await flush();
    button(ui.target, "Choose columns").click();
    await flush();
    const version = Array.from(
      ui.target.querySelectorAll(
        '.sv-grid-choose-columns-menu [role="option"]',
      ),
    ).find((option) => option.textContent.trim() === "Version");
    assert.ok(version);
    version.dispatchEvent(new browser.MouseEvent("click", { bubbles: true }));
    await new Promise((resolve) => setTimeout(resolve, 300));
    shared = app.decodeView(
      ui.handle.history.at(-1)?.searchParams.get("view") ?? null,
    );
    assert.deepEqual(shared?.hiddenColumns, ["version"]);
    assert.equal(
      ui.target.querySelector('th[data-svgrid-header-col="version"]'),
      null,
    );
    assert.equal(calls, 1);
    assert.equal(ui.handle.history.length, 1);
    assert.deepEqual(ui.handle.history[0].searchParams.getAll("artefacts"), [
      "one",
      "two",
    ]);
    const track = Array.from(
      ui.target.querySelectorAll(
        '.sv-grid-choose-columns-menu [role="option"]',
      ),
    ).find((option) => option.textContent.trim() === "Track");
    assert.ok(track);
    track.dispatchEvent(new browser.MouseEvent("click", { bubbles: true }));
    // Do not wait for the 250ms visibility tick before submitting Search.
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls, 2);
    assert.deepEqual(
      app
        .decodeView(ui.handle.history.at(-1)?.searchParams.get("view") ?? null)
        ?.hiddenColumns?.toSorted(),
      ["track", "version"],
    );
  } finally {
    await ui.destroy();
  }
});

void test("mounted initial/pagination-only/invalid, no-match, retry and access states render accurately", async () => {
  /** @type {{query: string; status?: number; session?: Response; text: RegExp; noFetch?: boolean}[]} */
  const cases = [
    {
      query: "limit=2&offset=2",
      text: /Choose at least one filter/,
      noFetch: true,
    },
    {
      query: "artefacts=one&issues=1",
      text: /Search not applied/,
      noFetch: true,
    },
    { query: "artefacts=one", text: /No test results match/ },
    {
      query: "artefacts=one",
      status: 500,
      text: /Could not load test results/,
    },
    {
      query: "artefacts=one",
      status: 401,
      session: json(null),
      text: /need to be logged in/,
    },
    {
      query: "artefacts=one",
      status: 403,
      session: json({ id: 5, teams: [], is_admin: false }),
      text: /don't have permission/,
    },
    {
      query: "artefacts=one",
      status: 403,
      session: json({}, 503),
      text: /couldn't verify your session/,
    },
  ];
  for (const scenario of cases) {
    let calls = 0;
    globalThis.fetch = (input) => {
      calls++;
      if (
        new URL(input instanceof Request ? input.url : input).pathname.endsWith(
          "/users/me",
        )
      )
        return Promise.resolve(scenario.session ?? json(null));
      return Promise.resolve(
        scenario.status ? json({}, scenario.status) : response([]),
      );
    };
    const ui = mounted(scenario.query);
    try {
      await flush();
      assert.match(ui.target.textContent, scenario.text);
      if (scenario.noFetch) assert.equal(calls, 0);
      if (scenario.status === 500) {
        globalThis.fetch = () => Promise.resolve(response([4]));
        button(ui.target, "Retry").click();
        await flush();
        assert.match(ui.target.textContent, /case 4/);
        assert.doesNotMatch(ui.target.textContent, /Could not load/);
      }
      if (scenario.status === 401) {
        const link = ui.target.querySelector('a[href*="/auth/saml/login"]');
        assert.ok(link);
        const href = link.getAttribute("href");
        assert.ok(href);
        const login = new URL(href);
        assert.equal(
          login.searchParams.get("return_to"),
          url(scenario.query).href,
        );
      }
    } finally {
      await ui.destroy();
    }
  }
});
