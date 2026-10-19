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
    friendly_name: "Configured family",
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
  for (const query of ["", "limit=2&offset=3", "artefacts= , "]) {
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
    const input = ui.target.querySelector('input[name="artefacts"]');
    assert.ok(input);
    assert.ok(ui.target.querySelector(`label[for="${input.id}"]`));
    input.value = "one, two";
    input.dispatchEvent(new browser.Event("input", { bubbles: true }));
    const family = /** @type {import('happy-dom').HTMLInputElement | null} */ (
      ui.target.querySelector('input[value="snap"]')
    );
    assert.ok(family);
    family.click();
    assert.equal(calls.length, 0, "draft edits do not fetch before applying");
    const form = ui.target.querySelector("form");
    assert.ok(form);
    // Submit event is what both keyboard Enter and the submit button invoke.
    form.dispatchEvent(
      new browser.Event("submit", { bubbles: true, cancelable: true }),
    );
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
      ui.target.querySelector('input[name="artefacts"]')?.value,
      "one, two",
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
    const local = /** @type {import('happy-dom').HTMLInputElement | null} */ (
      ui.target.querySelector(".sv-grid-global-filter input")
    );
    assert.ok(local);
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
