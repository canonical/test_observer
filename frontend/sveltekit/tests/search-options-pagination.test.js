// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

/* eslint-disable
  @typescript-eslint/no-unsafe-argument,
  @typescript-eslint/no-unsafe-assignment,
  @typescript-eslint/no-unsafe-call,
  @typescript-eslint/no-unsafe-member-access,
  @typescript-eslint/require-await
*/

import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { build } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { Window } from "happy-dom";

/** @type {typeof import("./search-options-entry.svelte.js") | undefined} */
let app;
/** @type {Window} */
let browser;
/** @type {Map<string, PropertyDescriptor | undefined>} */
const originalGlobals = new Map();
const originalFetch = globalThis.fetch;

const family = {
  name: "snaps",
  api_name: "snap",
  stages: ["beta"],
  columns: [],
  filters: [],
};
const json = (body, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
const flush = () => new Promise((resolve) => setTimeout(resolve, 10));

async function waitFor(check) {
  for (let attempt = 0; attempt < 20; attempt += 1) {
    if (check()) return;
    await flush();
  }
  assert.fail("Timed out waiting for the search option UI to update.");
}

before(async () => {
  const buildResult = await build({
    configFile: false,
    logLevel: "silent",
    plugins: [svelte({ compilerOptions: { runes: true } })],
    resolve: { alias: { $lib: resolve("src/lib") } },
    build: {
      write: false,
      lib: {
        entry: "tests/search-options-entry.svelte.js",
        formats: ["es"],
      },
      rolldownOptions: { output: { codeSplitting: false } },
    },
  });
  const bundle = buildResult[0]?.output.find((item) => item.type === "chunk");
  assert.ok(bundle, "search options test bundle should be generated");

  browser = new Window({
    url: "http://localhost/custom/base/test-results/option-2",
  });
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
    "Event",
    "MouseEvent",
    "CustomEvent",
    "MutationObserver",
    "getComputedStyle",
    "requestAnimationFrame",
  ]) {
    originalGlobals.set(
      name,
      Object.getOwnPropertyDescriptor(globalThis, name),
    );
    Object.defineProperty(globalThis, name, {
      configurable: true,
      value: name === "window" ? browser : Reflect.get(browser, name),
    });
  }
  const imported = await import(
    `data:text/javascript;base64,${Buffer.from(bundle.code).toString("base64")}`
  );
  app = /** @type {typeof import("./search-options-entry.svelte.js")} */ (
    imported
  );
});

after(async () => {
  globalThis.fetch = originalFetch;
  for (const [name, descriptor] of originalGlobals) {
    if (descriptor) Object.defineProperty(globalThis, name, descriptor);
    else Reflect.deleteProperty(globalThis, name);
  }
  await browser.happyDOM.abort();
});

function allFiltersUrl() {
  return new URL(
    "http://localhost/custom/base/test-results/option-2?" +
      [
        "families=snap",
        "test_result_statuses=FAILED",
        "test_execution_statuses=PASSED",
        "artefacts=widget",
        "artefact_versions=1.0",
        "artefact_tracks=stable",
        "environments=vm",
        "test_plans=smoke",
        "test_cases=install",
        "artefact_stages=beta",
        "artefact_is_archived=false",
        "rerun_is_requested=true",
        "execution_is_latest=false",
        "issues=42",
        "reviewer_ids=43",
        "execution_metadata=Y2F0ZWdvcnk%3D%3AdmFsdWU%3D",
        "from_date=2026-01-02T03%3A04%3A05.123456Z",
        "until_date=2026-01-03T03%3A04%3A05Z",
        "template_ids=template-9",
        "page=3",
        "page_size=25",
      ].join("&"),
  );
}

void test("page parsing keeps presentation state separate", () => {
  assert.ok(app);
  const { parseSearchPageState, parseSearchOptions } = app;
  assert.deepEqual(parseSearchPageState(new URLSearchParams()), {
    page: 1,
    pageSize: 50,
    problems: [],
  });
  assert.deepEqual(
    parseSearchPageState(new URLSearchParams("page=12&page_size=100")),
    { page: 12, pageSize: 100, problems: [] },
  );
  for (const query of [
    "page=0",
    "page=-1",
    "page=1.5",
    "page=9007199254740992",
    "page=9007199254740991",
    "page=2&page=3",
    "page_size=20",
    "page_size=25&page_size=100",
  ]) {
    const search = parseSearchOptions(
      new URLSearchParams(
        `${query}&families=snap&test_execution_statuses=FAILED`,
      ),
      [family],
    );
    assert.ok(
      search.problems.some((problem) => problem.startsWith("Invalid page")),
      query,
    );
    assert.deepEqual(search.filters.families, ["snap"]);
    assert.deepEqual(search.filters.test_execution_statuses, ["FAILED"]);
  }

  const valid = parseSearchOptions(allFiltersUrl().searchParams, [family]);
  assert.deepEqual(valid.problems, []);
  assert.equal(valid.page, 3);
  assert.equal(valid.pageSize, 25);
  assert.deepEqual(valid.filters.execution_metadata, [
    { category: "category", values: ["value"] },
  ]);
  assert.equal(valid.filters.test_execution_statuses[0], "PASSED");
});

void test("page transitions preserve filters and page size", () => {
  assert.ok(app);
  const {
    resetSearchOptionsPage,
    searchOptionsPageParams,
    searchOptionsPageSizeParams,
  } = app;
  const source = allFiltersUrl().searchParams;
  const next = searchOptionsPageParams(source, 4);
  assert.equal(next.get("page"), "4");
  assert.equal(next.get("page_size"), "25");
  assert.equal(next.get("test_execution_statuses"), "PASSED");

  const sized = searchOptionsPageSizeParams(next, 100);
  assert.equal(sized.get("page"), "1");
  assert.equal(sized.get("page_size"), "100");
  assert.equal(
    sized.get("execution_metadata"),
    source.get("execution_metadata"),
  );

  const reset = resetSearchOptionsPage(next);
  assert.equal(reset.get("page"), "1");
  assert.equal(reset.get("page_size"), "25");
  assert.equal(reset.get("families"), "snap");
  assert.throws(() => searchOptionsPageParams(source, 0), RangeError);
  assert.throws(() => searchOptionsPageSizeParams(source, 75), RangeError);
});

void test("page loader serializes filters and exact ranges", async () => {
  assert.ok(app);
  const { loadSearchOptionsPage, parseSearchOptions, searchOptionsPageRange } =
    app;
  const parsed = parseSearchOptions(allFiltersUrl().searchParams, [family]);
  const calls = [];
  const rows = [{ id: 8 }, { id: 9 }, { id: 10 }];
  const exactResponse = { count: 53, limit: 25, offset: 50, rows };
  const response = await loadSearchOptionsPage(parsed.filters, 3, 25, {
    request: async (path, options) => {
      calls.push({ path, options });
      return exactResponse;
    },
  });
  assert.equal(response, exactResponse);
  assert.equal(response.rows, rows);
  const request = new URLSearchParams(calls[0].path.split("?")[1]);
  assert.equal(calls[0].path.split("?")[0], "test-results/search-page");
  assert.equal(request.get("offset"), "50");
  assert.equal(request.get("limit"), "25");
  assert.equal(request.get("include_count"), "true");
  assert.equal(request.has("page"), false);
  assert.equal(request.has("page_size"), false);
  assert.deepEqual(
    [...new Set(request.keys())]
      .filter(
        (key) => key !== "offset" && key !== "limit" && key !== "include_count",
      )
      .sort(),
    [
      "artefact_is_archived",
      "artefact_stages",
      "artefact_tracks",
      "artefact_versions",
      "artefacts",
      "environments",
      "execution_is_latest",
      "execution_metadata",
      "families",
      "from_date",
      "issues",
      "rerun_is_requested",
      "reviewer_ids",
      "template_ids",
      "test_cases",
      "test_execution_statuses",
      "test_plans",
      "test_result_statuses",
      "until_date",
    ].sort(),
  );
  assert.deepEqual(searchOptionsPageRange(response), {
    start: 51,
    end: 53,
    count: 53,
  });
  assert.deepEqual(
    searchOptionsPageRange({ ...response, count: 0, offset: 0, rows: [] }),
    { start: 0, end: 0, count: 0 },
  );
  assert.throws(
    () => searchOptionsPageRange({ ...response, count: null }),
    /exact result count/,
  );
  await assert.rejects(
    loadSearchOptionsPage(parsed.filters, 3, 25, {
      request: async () => ({ ...exactResponse, count: null }),
    }),
    /exact result count/,
  );
});

void test("option scaffold navigates under base path", async () => {
  assert.ok(app);
  const requests = [];
  globalThis.fetch = async (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    requests.push(request);
    const offset = Number(request.searchParams.get("offset"));
    const limit = Number(request.searchParams.get("limit"));
    return json({
      count: 76,
      offset,
      limit,
      rows: Array.from(
        { length: Math.min(limit, 76 - offset) },
        (_, index) => ({ id: offset + index + 1 }),
      ),
    });
  };
  const target = browser.document.createElement("div");
  browser.document.body.append(target);
  const ui = app.mountSearchOption(target, allFiltersUrl(), [family], 3);
  try {
    await flush();
    assert.match(target.textContent, /Showing 51–75 of 76 results/);
    assert.equal(target.querySelector("select")?.value, "25");
    assert.equal(requests[0].pathname, "/v1/test-results/search-page");
    assert.equal(requests[0].searchParams.get("offset"), "50");
    assert.equal(requests[0].searchParams.get("limit"), "25");

    const next = [...target.querySelectorAll("button")].find(
      (button) => button.textContent.trim() === "Next",
    );
    assert.ok(next);
    next.click();
    assert.equal(
      ui.navigations.at(-1).pathname,
      "/custom/base/test-results/option-3",
    );
    assert.equal(ui.navigations.at(-1).searchParams.get("page"), "4");
    assert.equal(ui.navigations.at(-1).searchParams.get("page_size"), "25");
    assert.equal(
      ui.navigations.at(-1).searchParams.get("test_execution_statuses"),
      "PASSED",
    );

    await flush();
    const select = target.querySelector("select");
    assert.ok(select);
    select.value = "100";
    select.dispatchEvent(new browser.Event("change", { bubbles: true }));
    assert.equal(ui.navigations.at(-1).searchParams.get("page"), "1");
    assert.equal(ui.navigations.at(-1).searchParams.get("page_size"), "100");
    assert.equal(ui.navigations.at(-1).searchParams.get("families"), "snap");

    await waitFor(() =>
      target.textContent.includes("Showing 1–76 of 76 results"),
    );
    assert.equal(target.querySelector("select")?.value, "100");

    const defaultUrl = new URL(
      "http://localhost/custom/base/test-results/option-3?families=snap",
    );
    ui.restore(defaultUrl);
    await waitFor(() =>
      target.textContent.includes("Showing 1–50 of 76 results"),
    );
    assert.equal(target.querySelector("select")?.value, "50");

    const badUrl = new URL(ui.url);
    badUrl.searchParams.append("page", "2");
    badUrl.searchParams.append("page", "3");
    ui.restore(badUrl);
    await waitFor(() => Boolean(target.querySelector('[role="alert"]')));
    assert.match(
      target.querySelector('[role="alert"]')?.textContent ?? "",
      /Invalid page/,
    );
    assert.ok(
      !requests.some((request) => request.searchParams.get("page") !== null),
    );
  } finally {
    await ui.destroy();
    target.remove();
  }
});

void test("option scaffolds revalidate auth, present access states, and retry", async () => {
  assert.ok(app);

  const unauthenticatedTarget = browser.document.createElement("div");
  browser.document.body.append(unauthenticatedTarget);
  globalThis.fetch = async (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    return request.pathname === "/v1/users/me"
      ? json(null, 401)
      : json({ detail: "login required" }, 401);
  };
  const unauthenticated = app.mountSearchOption(
    unauthenticatedTarget,
    new URL("http://localhost/custom/base/test-results/option-2"),
    [family],
  );
  try {
    await waitFor(() =>
      Boolean(unauthenticatedTarget.querySelector("a[href]")),
    );
    const login = new URL(
      unauthenticatedTarget.querySelector("a[href]").getAttribute("href"),
    );
    assert.equal(login.pathname, "/v1/auth/saml/login");
    assert.equal(login.searchParams.get("return_to"), unauthenticated.url.href);
    assert.match(unauthenticatedTarget.textContent, /logged in/);
  } finally {
    await unauthenticated.destroy();
    unauthenticatedTarget.remove();
  }

  let forbiddenRequests = 0;
  const forbiddenTarget = browser.document.createElement("div");
  browser.document.body.append(forbiddenTarget);
  globalThis.fetch = async (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    if (request.pathname === "/v1/users/me") return json({ id: 1 });
    forbiddenRequests += 1;
    return forbiddenRequests === 1
      ? json({ detail: "forbidden" }, 403)
      : json({ count: 0, offset: 0, limit: 50, rows: [] });
  };
  const forbidden = app.mountSearchOption(
    forbiddenTarget,
    new URL("http://localhost/custom/base/test-results/option-3"),
    [family],
    3,
  );
  try {
    await waitFor(() =>
      Boolean(forbiddenTarget.querySelector('.message[role="alert"] button')),
    );
    assert.match(forbiddenTarget.textContent, /don't have permission/);
    forbiddenTarget.querySelector('.message[role="alert"] button').click();
    await waitFor(() =>
      forbiddenTarget.textContent.includes("No test results"),
    );
    assert.equal(forbiddenRequests, 2);
  } finally {
    await forbidden.destroy();
    forbiddenTarget.remove();
  }

  let sessionChecks = 0;
  const uncertainTarget = browser.document.createElement("div");
  browser.document.body.append(uncertainTarget);
  globalThis.fetch = async (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    if (request.pathname === "/v1/users/me") {
      sessionChecks += 1;
      return sessionChecks === 1 ? json({}, 503) : json(null, 401);
    }
    return json({ detail: "authorization required" }, 401);
  };
  const uncertain = app.mountSearchOption(
    uncertainTarget,
    new URL("http://localhost/custom/base/test-results/option-4"),
    [family],
    4,
  );
  try {
    await waitFor(() =>
      Boolean(uncertainTarget.querySelector('.message[role="alert"] button')),
    );
    assert.match(uncertainTarget.textContent, /couldn't verify your session/);
    uncertainTarget.querySelector('.message[role="alert"] button').click();
    await waitFor(() => Boolean(uncertainTarget.querySelector("a[href]")));
    assert.equal(sessionChecks, 2);
  } finally {
    await uncertain.destroy();
    uncertainTarget.remove();
  }
});

void test("option routes use shared paging and base-aware resolution", async () => {
  for (const option of [2, 3, 4]) {
    const source = await readFile(
      resolve(`src/routes/test-results/option-${option}/+page.svelte`),
      "utf8",
    );
    assert.match(source, /resolve\("test-results\/option-/);
    assert.match(source, /SearchOptionPlaceholder/);
    assert.match(source, /navigate=\{\(next\) => goto\(next\)\}/);
  }
});
