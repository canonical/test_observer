// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

/* eslint-disable
  @typescript-eslint/no-unsafe-argument,
  @typescript-eslint/no-unsafe-assignment,
  @typescript-eslint/no-unsafe-call,
  @typescript-eslint/no-unsafe-member-access,
  @typescript-eslint/no-unsafe-return,
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

class TestResizeObserver {
  #targets = new Set();

  observe(target) {
    this.#targets.add(target);
  }

  disconnect() {
    this.#targets.clear();
  }
}

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
    "HTMLDialogElement",
    "HTMLInputElement",
    "HTMLMediaElement",
    "HTMLSelectElement",
    "HTMLTextAreaElement",
    "Event",
    "KeyboardEvent",
    "MouseEvent",
    "CustomEvent",
    "CSS",
    "MutationObserver",
    "ResizeObserver",
    "getComputedStyle",
    "requestAnimationFrame",
  ]) {
    originalGlobals.set(
      name,
      Object.getOwnPropertyDescriptor(globalThis, name),
    );
    Object.defineProperty(globalThis, name, {
      configurable: true,
      value:
        name === "window"
          ? browser
          : name === "ResizeObserver"
            ? TestResizeObserver
            : Reflect.get(browser, name),
    });
  }
  // Happy DOM does not implement native Popovers. Model the public toggle,
  // trigger and light-dismiss behavior used by the condition-chip editor.
  /** @type {Set<import('happy-dom').HTMLElement>} */
  const openPopovers = new Set();
  const popoverToggle = (name, oldState, newState) =>
    Object.assign(new browser.Event(name), { oldState, newState });
  /** @param {import('happy-dom').HTMLElement} element */
  function hidePopover(element) {
    if (!openPopovers.has(element)) return;
    element.dispatchEvent(popoverToggle("beforetoggle", "open", "closed"));
    openPopovers.delete(element);
    element.removeAttribute("data-test-open");
    element.dispatchEvent(popoverToggle("toggle", "open", "closed"));
  }
  /** @param {import('happy-dom').HTMLElement} element */
  function showPopover(element) {
    if (openPopovers.has(element)) return;
    for (const other of openPopovers) hidePopover(other);
    element.dispatchEvent(popoverToggle("beforetoggle", "closed", "open"));
    openPopovers.add(element);
    element.setAttribute("data-test-open", "");
    element.dispatchEvent(popoverToggle("toggle", "closed", "open"));
  }
  // eslint-disable-next-line @typescript-eslint/unbound-method -- Preserve the receiver explicitly in this test adapter.
  const originalFocus = browser.HTMLElement.prototype.focus;
  // eslint-disable-next-line @typescript-eslint/unbound-method -- Preserve the receiver explicitly in this test adapter.
  const originalMatches = browser.Element.prototype.matches;
  browser.Element.prototype.matches = function (selector) {
    if (selector === ":popover-open")
      return this.hasAttribute("data-test-open");
    if (selector === ":modal") return this.hasAttribute("data-test-modal");
    return originalMatches.call(this, selector);
  };
  browser.HTMLElement.prototype.focus = function (...args) {
    const popover = this.closest("[popover]");
    if (popover && !popover.hasAttribute("data-test-open")) return;
    originalFocus.apply(this, args);
  };
  Object.defineProperties(browser.HTMLElement.prototype, {
    showPopover: {
      value() {
        showPopover(this);
      },
    },
    hidePopover: {
      value() {
        hidePopover(this);
      },
    },
  });
  browser.document.addEventListener("click", (event) => {
    const target = /** @type {import('happy-dom').Element} */ (event.target);
    const trigger = target.closest("button[popovertarget]");
    const popover = trigger
      ? browser.document.getElementById(
          trigger.getAttribute("popovertarget") ?? "",
        )
      : null;
    if (popover) {
      if (openPopovers.has(popover)) hidePopover(popover);
      else showPopover(popover);
      return;
    }
    for (const open of openPopovers)
      if (!open.contains(target)) hidePopover(open);
  });
  const dialogToggleEvent = (name, oldState, newState) =>
    Object.assign(new browser.Event(name), { oldState, newState });
  browser.HTMLDialogElement.prototype.showModal = function () {
    if (this.open) return;
    this.dispatchEvent(dialogToggleEvent("beforetoggle", "closed", "open"));
    this.open = true;
    this.setAttribute("data-test-modal", "");
    this.dispatchEvent(dialogToggleEvent("toggle", "closed", "open"));
  };
  browser.HTMLDialogElement.prototype.close = function () {
    if (!this.open) return;
    this.dispatchEvent(dialogToggleEvent("beforetoggle", "open", "closed"));
    this.open = false;
    this.removeAttribute("data-test-modal");
    this.dispatchEvent(dialogToggleEvent("toggle", "open", "closed"));
    setTimeout(() => this.dispatchEvent(new browser.Event("close")));
  };
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

function allFiltersUrl(option = 2) {
  const routeOption = option === 2.5 ? "2-5" : option;
  return new URL(
    `http://localhost/custom/base/test-results/option-${routeOption}?` +
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

/** @param {number} id @param {{stage?: string; includeStage?: boolean}} [options] */
function resultRow(id, { stage = "beta", includeStage = true } = {}) {
  const artefact = {
    id: id + 100,
    name: `artefact-${id}`,
    version: `1.${id}`,
    track: "stable",
    family: "snap",
    archived: id % 2 === 0,
    reviewers: [
      { id: id + 500, name: `Reviewer ${id}`, launchpad_handle: "reviewer" },
    ],
  };
  if (includeStage) artefact.stage = stage;
  return {
    test_result: {
      id,
      name: `case-${id}`,
      category: `category-${id}`,
      created_at: "2026-05-04T03:02:01.987654Z",
      template_id: `template-${id}`,
      status: "FAILED",
      issues: [{ id: id + 600, key: `BUG-${id}`, title: `Issue ${id}` }],
    },
    test_execution: {
      id: id + 200,
      status: "PASSED",
      environment: { name: `environment-${id}` },
      test_plan: `plan-${id}`,
      rerun_is_requested: id % 2 === 0,
      execution_is_latest: true,
      execution_metadata: [{ category: "ci", value: `run-${id}` }],
    },
    artefact,
    artefact_build: { architecture: "amd64" },
  };
}

/** @param {number} id */
function detailResult(id) {
  return {
    test_result: {
      id,
      name: `case-${id}`,
      category: `category-${id}`,
      template_id: `template-${id}`,
      status: "FAILED",
      io_log: "",
      issues: [],
    },
    test_execution: {
      id: id + 200,
      status: "PASSED",
      environment: { name: `environment-${id}` },
      test_plan: `plan-${id}`,
      created_at: "2026-05-04T03:02:01Z",
      execution_metadata: {},
    },
    artefact: {
      id: id + 100,
      name: `artefact-${id}`,
      version: `1.${id}`,
      track: "stable",
      family: "snap",
    },
    artefact_build: { architecture: "amd64" },
  };
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

  const rawFrom = "2026-01-02T04:04:05.123456+01:30";
  const rawUntil = "2026-01-03T03:04:05.123456000Z";
  const legacy = parseSearchOptions(
    new URLSearchParams(
      `from_date=${encodeURIComponent(rawFrom)}&until_date=${encodeURIComponent(rawUntil)}&page=2&page_size=25`,
    ),
    [family],
  );
  assert.deepEqual(legacy.problems, []);
  assert.equal(legacy.filters.from_date, rawFrom);
  assert.equal(legacy.filters.until_date, rawUntil);
  assert.equal(legacy.page, 2);
  assert.equal(legacy.pageSize, 25);
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

void test("pager model builds compact windows and exact range labels", () => {
  assert.ok(app);
  const {
    searchOptionsLastPage,
    searchOptionsPageItems,
    searchOptionsPageRangeLabel,
    searchOptionsTotalPages,
  } = app;

  assert.equal(searchOptionsTotalPages(0, 25), 0);
  assert.equal(searchOptionsLastPage(0, 25), 1);
  assert.equal(searchOptionsTotalPages(176, 25), 8);
  assert.deepEqual(searchOptionsPageItems(1, 0), []);
  assert.deepEqual(searchOptionsPageItems(4, 7), [1, 2, 3, 4, 5, 6, 7]);
  assert.deepEqual(searchOptionsPageItems(1, 7), [1, 2, 3, 4, 5, 6, 7]);
  assert.deepEqual(searchOptionsPageItems(1, 8), [1, 2, "gap", 8]);
  assert.deepEqual(searchOptionsPageItems(2, 8), [1, 2, 3, "gap", 8]);
  assert.deepEqual(searchOptionsPageItems(6, 12), [
    1,
    "gap",
    5,
    6,
    7,
    "gap",
    12,
  ]);
  assert.deepEqual(searchOptionsPageItems(11, 12), [1, "gap", 10, 11, 12]);
  assert.deepEqual(searchOptionsPageItems(12, 12), [1, "gap", 11, 12]);
  assert.deepEqual(
    searchOptionsPageItems(99, 12),
    [1, "gap", 11, 12],
    "the final window remains bounded by the exact page count",
  );
  assert.equal(
    searchOptionsPageRangeLabel({ start: 51, end: 53, count: 53 }),
    "Showing 51–53 of 53 results",
  );
  assert.equal(
    searchOptionsPageRangeLabel({ start: 0, end: 0, count: 0 }),
    "Showing 0–0 of 0 results",
  );
  assert.equal(
    searchOptionsPageRangeLabel({ start: 0, end: 0, count: 53 }),
    "No results on this page (53 total)",
  );
  assert.throws(() => searchOptionsTotalPages(-1, 25), /exact result count/);
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
      rows: Array.from({ length: Math.min(limit, 76 - offset) }, (_, index) =>
        resultRow(offset + index + 1),
      ),
    });
  };
  const target = browser.document.createElement("div");
  browser.document.body.append(target);
  const ui = app.mountSearchOption(target, allFiltersUrl(3), [family], 3);
  try {
    await flush();
    assert.match(target.textContent, /Showing 51–75 of 76 results/);
    assert.equal(target.querySelector(".pager select")?.value, "25");
    assert.deepEqual(
      [...target.querySelectorAll(".pager-pages button")].map((button) =>
        button.getAttribute("aria-label"),
      ),
      ["Page 1", "Page 2", "Page 3", "Page 4"],
    );
    assert.equal(
      target
        .querySelector('[aria-label="Page 3"]')
        ?.getAttribute("aria-current"),
      "page",
    );
    assert.equal(
      target.querySelector('[aria-label="Previous page"]')?.disabled,
      false,
    );
    assert.equal(
      target.querySelector('[aria-label="Next page"]')?.disabled,
      false,
    );
    const initialRequest = requests.find(
      (request) => request.pathname === "/v1/test-results/search-page",
    );
    assert.ok(initialRequest);
    assert.equal(initialRequest.searchParams.get("offset"), "50");
    assert.equal(initialRequest.searchParams.get("limit"), "25");

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
    await waitFor(() => Boolean(target.querySelector('[aria-label="Page 4"]')));
    assert.equal(
      target
        .querySelector('[aria-label="Page 4"]')
        ?.getAttribute("aria-current"),
      "page",
    );
    assert.equal(
      target.querySelector('[aria-label="Next page"]')?.disabled,
      true,
    );
    assert.equal(
      target.querySelector('[aria-label="Previous page"]')?.disabled,
      false,
    );

    const submitJump = async (value, expectedPage) => {
      const jumpInput = target.querySelector(".pager-jump-input");
      const jumpForm = target.querySelector(".pager-jump");
      assert.ok(jumpInput);
      assert.ok(jumpForm);
      jumpInput.value = String(value);
      jumpInput.dispatchEvent(new browser.Event("input", { bubbles: true }));
      await flush();
      jumpForm.dispatchEvent(
        new browser.Event("submit", { bubbles: true, cancelable: true }),
      );
      await waitFor(
        () => ui.url.searchParams.get("page") === String(expectedPage),
      );
      await waitFor(() =>
        target.textContent.includes(
          `Showing ${expectedPage === 1 ? "1" : (expectedPage - 1) * 25 + 1}–`,
        ),
      );
      assert.equal(
        target
          .querySelector(`[aria-label="Page ${expectedPage}"]`)
          ?.getAttribute("aria-current"),
        "page",
      );
      if (expectedPage === 1)
        assert.equal(
          target.querySelector('[aria-label="Previous page"]')?.disabled,
          true,
        );
      if (expectedPage === 4)
        assert.equal(
          target.querySelector('[aria-label="Next page"]')?.disabled,
          true,
        );
      assert.equal(ui.url.searchParams.get("page_size"), "25");
      assert.equal(ui.url.searchParams.get("families"), "snap");
      assert.equal(
        ui.url.searchParams.get("test_execution_statuses"),
        "PASSED",
      );
      const request = requests
        .filter((item) => item.pathname === "/v1/test-results/search-page")
        .at(-1);
      assert.ok(request);
      assert.equal(
        request.searchParams.get("offset"),
        String((expectedPage - 1) * 25),
      );
      assert.equal(request.searchParams.get("limit"), "25");
    };
    await submitJump("2", 2);
    await submitJump("999", 4);
    await submitJump("-8", 1);

    const select = target.querySelector(".pager select");
    assert.ok(select);
    select.value = "100";
    select.dispatchEvent(new browser.Event("change", { bubbles: true }));
    assert.equal(ui.navigations.at(-1).searchParams.get("page"), "1");
    assert.equal(ui.navigations.at(-1).searchParams.get("page_size"), "100");
    assert.equal(ui.navigations.at(-1).searchParams.get("families"), "snap");

    await waitFor(() =>
      target.textContent.includes("Showing 1–76 of 76 results"),
    );
    assert.equal(target.querySelector(".pager select")?.value, "100");

    const defaultUrl = new URL(
      "http://localhost/custom/base/test-results/option-3?families=snap",
    );
    ui.restore(defaultUrl);
    await waitFor(() =>
      target.textContent.includes("Showing 1–50 of 76 results"),
    );
    assert.equal(target.querySelector(".pager select")?.value, "50");

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

void test("direct out-of-range URLs canonicalize after the exact count arrives", async () => {
  assert.ok(app);

  const requests = [];
  globalThis.fetch = async (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    if (request.pathname !== "/v1/test-results/search-page")
      return json({ detail: "not found" }, 404);
    requests.push(request);
    const offset = Number(request.searchParams.get("offset"));
    const limit = Number(request.searchParams.get("limit"));
    return json({
      count: 53,
      offset,
      limit,
      rows: Array.from(
        { length: Math.min(limit, Math.max(0, 53 - offset)) },
        (_, index) => resultRow(offset + index + 1),
      ),
    });
  };

  const target = browser.document.createElement("div");
  browser.document.body.append(target);
  const initialUrl = new URL(
    "http://localhost/custom/base/test-results/option-2?page=99&page_size=25&families=snap&test_execution_statuses=PASSED",
  );
  const ui = app.mountSearchOption(target, initialUrl, [family]);
  try {
    await waitFor(() => ui.url.searchParams.get("page") === "3");
    await waitFor(() =>
      target.textContent.includes("Showing 51–53 of 53 results"),
    );
    assert.equal(ui.url.searchParams.get("page_size"), "25");
    assert.equal(ui.url.searchParams.get("families"), "snap");
    assert.equal(ui.url.searchParams.get("test_execution_statuses"), "PASSED");
    assert.deepEqual(
      requests.map((request) => request.searchParams.get("offset")),
      ["2450", "50"],
      "the initial direct URL is checked against count then the last page is fetched",
    );
    assert.deepEqual(
      requests.map((request) => request.searchParams.get("limit")),
      ["25", "25"],
    );
    assert.equal(
      target
        .querySelector('[aria-label="Page 3"]')
        ?.getAttribute("aria-current"),
      "page",
    );
    assert.equal(
      target.querySelector('[aria-label="Next page"]')?.disabled,
      true,
    );
  } finally {
    await ui.destroy();
    target.remove();
  }

  const emptyRequests = [];
  globalThis.fetch = async (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    emptyRequests.push(request);
    const offset = Number(request.searchParams.get("offset"));
    const limit = Number(request.searchParams.get("limit"));
    return json({ count: 0, offset, limit, rows: [] });
  };
  const emptyTarget = browser.document.createElement("div");
  browser.document.body.append(emptyTarget);
  const emptyUi = app.mountSearchOption(
    emptyTarget,
    new URL(
      "http://localhost/custom/base/test-results/option-4?page=7&page_size=25&families=snap",
    ),
    [family],
    4,
  );
  try {
    await waitFor(() => emptyUi.url.searchParams.get("page") === "1");
    await waitFor(() =>
      emptyTarget.textContent.includes("Showing 0–0 of 0 results"),
    );
    assert.equal(emptyUi.url.searchParams.get("page_size"), "25");
    assert.equal(emptyUi.url.searchParams.get("families"), "snap");
    assert.deepEqual(
      emptyRequests.map((request) => request.searchParams.get("offset")),
      ["150", "0"],
    );
    assert.equal(emptyTarget.querySelector(".pager select")?.value, "25");
    assert.equal(emptyTarget.querySelectorAll(".pager-pages button").length, 0);
    assert.equal(emptyTarget.querySelector(".pager-jump"), null);
    assert.equal(
      emptyTarget.querySelector('[aria-label="Previous page"]')?.disabled,
      true,
    );
    assert.equal(
      emptyTarget.querySelector('[aria-label="Next page"]')?.disabled,
      true,
    );
  } finally {
    await emptyUi.destroy();
    emptyTarget.remove();
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
      Boolean(forbiddenTarget.querySelector('[role="alert"] button')),
    );
    assert.match(forbiddenTarget.textContent, /don't have permission/);
    forbiddenTarget.querySelector('[role="alert"] button').click();
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
      Boolean(uncertainTarget.querySelector('[role="alert"] button')),
    );
    assert.match(uncertainTarget.textContent, /couldn't verify your session/);
    uncertainTarget.querySelector('[role="alert"] button').click();
    await waitFor(() => Boolean(uncertainTarget.querySelector("a[href]")));
    assert.equal(sessionChecks, 2);
  } finally {
    await uncertain.destroy();
    uncertainTarget.remove();
  }
});

void test("option routes use shared paging and base-aware resolution", async () => {
  for (const option of [2, 2.5, 3, 4]) {
    const routeOption = option === 2.5 ? "2-5" : option;
    const source = await readFile(
      resolve(`src/routes/test-results/option-${routeOption}/+page.svelte`),
      "utf8",
    );
    assert.match(
      source,
      new RegExp(`resolve\\("test-results/option-${routeOption}"\\)`),
    );
    assert.match(
      source,
      option === 2 || option === 2.5
        ? /SearchOption2/
        : option === 3
          ? /SearchOption3/
          : /SearchOption4/,
    );
    if (option === 2.5) assert.match(source, /variant=\{2\.5\}/);
    assert.match(source, /navigate=\{\(next\) => goto\(next\)\}/);
  }
});

void test("Option 2.5 has a dedicated aligned filter row and exact drafts", async () => {
  assert.ok(app);
  const requests = [];
  globalThis.fetch = async (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    requests.push(request);
    const offset = Number(request.searchParams.get("offset"));
    const limit = Number(request.searchParams.get("limit"));
    return json({ count: 100, offset, limit, rows: [resultRow(12)] });
  };

  const target = browser.document.createElement("div");
  browser.document.body.append(target);
  const initialUrl = new URL(
    "http://localhost/custom/base/test-results/option-2-5?" +
      "page=3&page_size=25&families=snap&test_execution_statuses=PASSED&" +
      "artefact_tracks=stable&from_date=2026-01-02T03%3A04%3A05.123456%2B01%3A30&" +
      "until_date=2026-01-03T03%3A04%3A05.000000-04%3A00",
  );
  const ui = app.mountSearchOption(target, initialUrl, [family], 2.5);
  try {
    await waitFor(() =>
      target.textContent.includes("Showing 51–51 of 100 results"),
    );
    assert.match(target.textContent, /Search \(Option 2\.5\)/);
    assert.equal(target.querySelector(".search-page > p"), null);
    const table = target.querySelector("table.search-option-table");
    assert.ok(table);
    const headerRows = [...table.querySelectorAll("thead tr")];
    assert.equal(
      headerRows.length,
      2,
      "the filter controls have their own thead row",
    );
    const labels = [...headerRows[0].querySelectorAll("th")].map((cell) =>
      cell.textContent.trim(),
    );
    assert.deepEqual(labels, [
      "Run",
      "Details",
      "Created",
      "Family",
      "Artefact",
      "Stage",
      "Archived",
      "Test Case",
      "Category",
      "Execution ID",
      "Execution Status",
      "Rerun Requested",
      "Latest Execution",
      "Result status",
      "Track",
      "Version",
      "Architecture",
      "Environment",
      "Test Plan",
      "Template ID",
      "Issues",
      "Reviewers",
      "Execution Metadata",
    ]);
    const filterCells = [...headerRows[1].querySelectorAll("th")];
    assert.equal(filterCells.length, 23);
    const filterIndexes = [
      2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21, 22,
    ];
    assert.deepEqual(
      filterCells.flatMap((cell, index) =>
        cell.querySelector("button[aria-label^='Filter ']") ? [index] : [],
      ),
      filterIndexes,
      "only filterable controls appear, under their matching column",
    );
    assert.equal(
      target.querySelectorAll('thead button[aria-label^="Filter "]').length,
      18,
    );
    assert.equal(
      target.querySelector('[aria-label="Filter Track"]')?.closest("th"),
      filterCells[14],
    );

    const firstRequest = requests.find(
      (request) => request.pathname === "/v1/test-results/search-page",
    );
    assert.ok(firstRequest);
    assert.equal(firstRequest.searchParams.get("offset"), "50");
    assert.equal(firstRequest.searchParams.get("limit"), "25");
    assert.equal(firstRequest.searchParams.get("include_count"), "true");
    assert.equal(
      firstRequest.searchParams.get("from_date"),
      "2026-01-02T03:04:05.123456+01:30",
    );
    assert.equal(
      firstRequest.searchParams.get("until_date"),
      "2026-01-03T03:04:05.000000-04:00",
    );

    target.querySelector('[aria-label="Filter Track"]').click();
    await flush();
    const trackInput = target.querySelector(
      '[data-search-grid-filter="artefact_tracks"]',
    );
    assert.ok(trackInput);
    trackInput.value = "stable, beta";
    trackInput.dispatchEvent(new browser.Event("input", { bubbles: true }));
    await flush();
    assert.equal(
      requests.filter(
        (request) => request.pathname === "/v1/test-results/search-page",
      ).length,
      1,
      "editing a simple exact list remains a draft",
    );

    target.querySelector('[aria-label="Filter Created"]').click();
    await flush();
    const picker = target.querySelector(
      '[data-search-grid-filter-picker="from_date"]',
    );
    const untilPicker = target.querySelector(
      '[data-search-grid-filter-picker="until_date"]',
    );
    const exactDate = target.querySelector(
      '[data-search-grid-filter="from_date"]',
    );
    const exactUntil = target.querySelector(
      '[data-search-grid-filter="until_date"]',
    );
    assert.ok(picker);
    assert.ok(untilPicker);
    assert.ok(exactDate);
    assert.ok(exactUntil);
    assert.equal(picker.getAttribute("type"), "datetime-local");
    assert.equal(picker.getAttribute("step"), "1");
    assert.equal(untilPicker.getAttribute("type"), "datetime-local");
    assert.equal(untilPicker.getAttribute("step"), "1");
    assert.equal(picker.value, "", "offset/fraction values are not projected");
    assert.equal(
      untilPicker.value,
      "",
      "offset/fraction values are not projected",
    );
    const dateEditor = target.querySelector(".date-filter");
    assert.ok(dateEditor);
    assert.equal(dateEditor.querySelectorAll('input[type="text"]').length, 0);
    assert.equal(
      dateEditor.querySelectorAll("[data-utc-picker-note]").length,
      2,
    );
    assert.deepEqual(
      [...dateEditor.querySelectorAll(".compact-bound-label")].map((heading) =>
        heading.textContent.trim(),
      ),
      ["From", "To"],
    );
    assert.equal(dateEditor.querySelectorAll(".utc-note").length, 1);
    assert.equal(
      dateEditor.querySelector(".utc-note")?.textContent.trim(),
      "All times are in UTC.",
    );
    picker.value = "2026-01-02T03:04:06";
    picker.dispatchEvent(new browser.Event("input", { bubbles: true }));
    untilPicker.value = "2026-01-03T03:04:06";
    untilPicker.dispatchEvent(new browser.Event("input", { bubbles: true }));
    await flush();
    assert.equal(
      requests.filter(
        (request) => request.pathname === "/v1/test-results/search-page",
      ).length,
      1,
      "Created edits remain drafts until Search",
    );

    target
      .querySelector('form[aria-label="Apply confirmed search filters"]')
      .dispatchEvent(
        new browser.Event("submit", { bubbles: true, cancelable: true }),
      );
    await waitFor(() => ui.url.searchParams.get("page") === "1");
    await waitFor(
      () =>
        requests.filter(
          (request) => request.pathname === "/v1/test-results/search-page",
        ).length === 2,
    );
    assert.equal(ui.url.pathname, "/custom/base/test-results/option-2-5");
    assert.equal(ui.url.searchParams.get("page_size"), "25");
    assert.equal(ui.url.searchParams.get("families"), "snap");
    assert.equal(ui.url.searchParams.get("test_execution_statuses"), "PASSED");
    assert.deepEqual(ui.url.searchParams.getAll("artefact_tracks"), [
      "stable",
      "beta",
    ]);
    assert.equal(ui.url.searchParams.get("from_date"), "2026-01-02T03:04:06Z");
    assert.equal(ui.url.searchParams.get("until_date"), "2026-01-03T03:04:06Z");
    const appliedRequest = requests.filter(
      (request) => request.pathname === "/v1/test-results/search-page",
    )[1];
    assert.equal(appliedRequest.searchParams.get("offset"), "0");
    assert.equal(appliedRequest.searchParams.get("limit"), "25");
    assert.equal(appliedRequest.searchParams.get("include_count"), "true");
    assert.deepEqual(appliedRequest.searchParams.getAll("artefact_tracks"), [
      "stable",
      "beta",
    ]);
    assert.equal(
      appliedRequest.searchParams.get("from_date"),
      "2026-01-02T03:04:06Z",
    );
    assert.equal(
      appliedRequest.searchParams.get("until_date"),
      "2026-01-03T03:04:06Z",
    );
    assert.equal(appliedRequest.searchParams.get("families"), "snap");
    assert.equal(
      appliedRequest.searchParams.get("test_execution_statuses"),
      "PASSED",
    );
  } finally {
    await ui.destroy();
    target.remove();
  }
});

void test("Option 2 renders the ordered Pragma table and server-backed filters", async () => {
  assert.ok(app);
  const requests = [];
  const serverRows = [
    resultRow(12, { stage: "" }),
    resultRow(8, { includeStage: false }),
  ];
  globalThis.fetch = async (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    requests.push(request);
    if (request.pathname === "/v1/test-results/search-page/12")
      return json(detailResult(12));
    const offset = Number(request.searchParams.get("offset"));
    const limit = Number(request.searchParams.get("limit"));
    return json({ count: 100, offset, limit, rows: serverRows });
  };

  const target = browser.document.createElement("div");
  browser.document.body.append(target);
  const ui = app.mountSearchOption(target, allFiltersUrl(), [family]);
  try {
    await waitFor(() =>
      target.textContent.includes("Showing 51–52 of 100 results"),
    );
    assert.equal(
      target.querySelector("h1")?.textContent.trim(),
      "Search (Option 2)",
    );
    assert.equal(target.querySelector(".search-page > p"), null);
    const headers = [...target.querySelectorAll("thead th")].map(
      (header) =>
        header.querySelector(".header-content > span")?.textContent.trim() ??
        header.textContent.trim(),
    );
    assert.deepEqual(headers, [
      "Run",
      "Details",
      "Created",
      "Family",
      "Artefact",
      "Stage",
      "Archived",
      "Test Case",
      "Category",
      "Execution ID",
      "Execution Status",
      "Rerun Requested",
      "Latest Execution",
      "Result status",
      "Track",
      "Version",
      "Architecture",
      "Environment",
      "Test Plan",
      "Template ID",
      "Issues",
      "Reviewers",
      "Execution Metadata",
    ]);
    assert.equal(
      target.querySelectorAll('thead button[aria-label^="Filter "]').length,
      18,
    );
    assert.equal(
      target.querySelectorAll('thead button[aria-label*="Sort"]').length,
      0,
    );
    assert.equal(
      [...target.querySelectorAll('input[type="search"]')].filter(
        (input) => !input.closest("[hidden]"),
      ).length,
      0,
    );

    const firstSearch = requests.find(
      (request) => request.pathname === "/v1/test-results/search-page",
    );
    assert.ok(firstSearch);
    assert.equal(firstSearch.searchParams.get("offset"), "50");
    assert.equal(firstSearch.searchParams.get("limit"), "25");
    assert.equal(firstSearch.searchParams.get("include_count"), "true");
    const canonicalKeys = [
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
    ];
    assert.deepEqual(
      [...new Set(firstSearch.searchParams.keys())]
        .filter((key) => !["offset", "limit", "include_count"].includes(key))
        .sort(),
      canonicalKeys,
    );
    assert.equal(
      firstSearch.searchParams.get("test_execution_statuses"),
      "PASSED",
    );
    assert.equal(
      firstSearch.searchParams.get("execution_metadata"),
      "Y2F0ZWdvcnk=:dmFsdWU=",
    );

    const nextPage = [...target.querySelectorAll(".pager button")].find(
      (button) => button.textContent.trim() === "Next",
    );
    assert.ok(nextPage);
    nextPage.click();
    await waitFor(() => ui.url.searchParams.get("page") === "4");
    await waitFor(
      () =>
        requests.filter(
          (request) => request.pathname === "/v1/test-results/search-page",
        ).length === 2,
    );
    await waitFor(() =>
      target.textContent.includes("Showing 76–77 of 100 results"),
    );
    assert.match(target.textContent, /Results for applied query/);
    const nextRequest = requests.filter(
      (request) => request.pathname === "/v1/test-results/search-page",
    )[1];
    assert.equal(nextRequest.searchParams.get("offset"), "75");
    assert.equal(nextRequest.searchParams.get("limit"), "25");

    const resultButtons = /** @type {NodeListOf<HTMLButtonElement>} */ (
      target.querySelectorAll("tbody [data-test-result-id]")
    );
    const resultIds = [...resultButtons].map(
      (button) => button.dataset.testResultId,
    );
    assert.deepEqual(resultIds, ["12", "8"]);
    const cells = target.querySelector("tbody tr").querySelectorAll("td");
    assert.equal(cells[2].textContent, "2026-05-04 03:02:01");
    assert.equal(cells[3].textContent, "Snaps");
    assert.equal(cells[5].textContent, "(none)");
    assert.equal(cells[6].textContent, "Yes");
    assert.equal(cells[20].textContent.trim(), "1 issue");
    assert.equal(cells[21].textContent.trim(), "1 reviewer");
    assert.equal(cells[22].textContent.trim(), "1 metadata pair");
    assert.equal(
      target.querySelectorAll("tbody tr")[1].querySelectorAll("td")[5]
        .textContent,
      "—",
    );

    const run = target.querySelector(
      'tbody a[aria-label="View Run for case-12"]',
    );
    assert.ok(run);
    const runUrl = new URL(run.href);
    assert.equal(runUrl.pathname, "/custom/base/snaps/112");
    assert.equal(runUrl.searchParams.get("testExecutionId"), "212");
    assert.equal(runUrl.searchParams.get("testResultId"), "12");
    assert.equal(
      requests.filter((request) =>
        request.pathname.startsWith("/v1/test-results/search-page/"),
      ).length,
      0,
    );

    const versionFilter = target.querySelector('[aria-label="Filter Version"]');
    assert.ok(versionFilter);
    versionFilter.click();
    await flush();
    const versionInput = target.querySelector(
      '[data-search-grid-filter="artefact_versions"]',
    );
    assert.ok(versionInput);
    versionInput.value = "2.0";
    versionInput.dispatchEvent(new browser.Event("input", { bubbles: true }));
    await flush();
    assert.equal(
      requests.filter(
        (request) => request.pathname === "/v1/test-results/search-page",
      ).length,
      2,
      "editing a filter must not fetch results",
    );
    assert.match(target.textContent, /Changes not applied/);
    assert.match(target.textContent, /Results for previous query/);

    const previousPage = [...target.querySelectorAll(".pager button")].find(
      (button) => button.textContent.trim() === "Previous",
    );
    assert.ok(previousPage);
    previousPage.click();
    await waitFor(() => ui.url.searchParams.get("page") === "3");
    await waitFor(
      () =>
        requests.filter(
          (request) => request.pathname === "/v1/test-results/search-page",
        ).length === 3,
    );
    await waitFor(() =>
      target.textContent.includes("Showing 51–52 of 100 results"),
    );
    assert.equal(versionInput.value, "2.0");
    assert.match(target.textContent, /Changes not applied/);
    const pagedRequest = requests.filter(
      (request) => request.pathname === "/v1/test-results/search-page",
    )[2];
    assert.equal(pagedRequest.searchParams.get("offset"), "50");
    assert.equal(pagedRequest.searchParams.get("artefact_versions"), "1.0");

    const pageSize = target.querySelector(".pager select");
    assert.ok(pageSize);
    pageSize.value = "100";
    pageSize.dispatchEvent(new browser.Event("change", { bubbles: true }));
    await waitFor(() => ui.url.searchParams.get("page_size") === "100");
    await waitFor(
      () =>
        requests.filter(
          (request) => request.pathname === "/v1/test-results/search-page",
        ).length === 4,
    );
    await waitFor(() =>
      target.textContent.includes("Showing 1–2 of 100 results"),
    );
    assert.equal(ui.url.searchParams.get("page"), "1");
    assert.equal(versionInput.value, "2.0");
    assert.match(target.textContent, /Changes not applied/);
    const resizedRequest = requests.filter(
      (request) => request.pathname === "/v1/test-results/search-page",
    )[3];
    assert.equal(resizedRequest.searchParams.get("offset"), "0");
    assert.equal(resizedRequest.searchParams.get("limit"), "100");
    assert.equal(resizedRequest.searchParams.get("artefact_versions"), "1.0");

    target
      .querySelector('form[aria-label="Apply confirmed search filters"]')
      .dispatchEvent(
        new browser.Event("submit", { bubbles: true, cancelable: true }),
      );
    await waitFor(
      () =>
        requests.filter(
          (request) => request.pathname === "/v1/test-results/search-page",
        ).length === 5,
    );
    const appliedUrl = ui.url;
    assert.equal(appliedUrl.searchParams.get("page"), "1");
    assert.equal(appliedUrl.searchParams.get("page_size"), "100");
    assert.equal(appliedUrl.searchParams.get("artefact_versions"), "2.0");
    const appliedRequest = requests.filter(
      (request) => request.pathname === "/v1/test-results/search-page",
    )[4];
    assert.equal(appliedRequest.searchParams.get("offset"), "0");
    assert.equal(appliedRequest.searchParams.get("limit"), "100");
    assert.equal(appliedRequest.searchParams.get("artefact_versions"), "2.0");
    assert.equal(
      appliedRequest.searchParams.get("test_execution_statuses"),
      "PASSED",
    );
    assert.deepEqual(
      [
        .../** @type {NodeListOf<HTMLButtonElement>} */ (
          target.querySelectorAll("tbody [data-test-result-id]")
        ),
      ].map((button) => button.dataset.testResultId),
      ["12", "8"],
      "the client must retain server order and must not filter server rows locally",
    );

    target
      .querySelector('form[aria-label="Apply confirmed search filters"]')
      .dispatchEvent(
        new browser.Event("submit", { bubbles: true, cancelable: true }),
      );
    await waitFor(
      () =>
        requests.filter(
          (request) => request.pathname === "/v1/test-results/search-page",
        ).length === 6,
    );
    await waitFor(() =>
      target.textContent.includes("Showing 1–2 of 100 results"),
    );

    target.querySelector('[data-test-result-id="12"]').click();
    await waitFor(() =>
      requests.some(
        (request) => request.pathname === "/v1/test-results/search-page/12",
      ),
    );
    assert.equal(
      requests.filter((request) =>
        request.pathname.startsWith("/v1/test-results/search-page/"),
      ).length,
      1,
      "Details is fetched only after its action is used",
    );
  } finally {
    await ui.destroy();
    target.remove();
  }
});

void test("Option 3 SidePanel search preserves shared filtering and compact table behavior", async () => {
  assert.ok(app);
  const requests = [];
  const serverRows = [resultRow(12), resultRow(8)];
  serverRows[0].test_result.created_at = "2026-05-04T03:02:01.987654+03:00";
  globalThis.fetch = async (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    requests.push(request);
    if (request.pathname === "/v1/test-results/search-page/12")
      return json(detailResult(12));
    const offset = Number(request.searchParams.get("offset"));
    const limit = Number(request.searchParams.get("limit"));
    return json({ count: 100, offset, limit, rows: serverRows });
  };

  const target = browser.document.createElement("div");
  browser.document.body.append(target);
  const ui = app.mountSearchOption(target, allFiltersUrl(3), [family], 3);
  try {
    await waitFor(() =>
      target.textContent.includes("Showing 51–52 of 100 results"),
    );
    assert.equal(
      target.querySelector("h1")?.textContent.trim(),
      "Search (Option 3)",
    );
    assert.equal(target.querySelector(".search-page > p"), null);
    const headers = [...target.querySelectorAll("thead th")].map((header) =>
      header.textContent.trim(),
    );
    assert.deepEqual(headers, [
      "Created",
      "Artefact",
      "Test Case",
      "Test Execution ID",
      "Status",
      "Track",
      "Version",
      "Environment",
      "Test Plan",
      "Actions",
    ]);

    const request = requests.find(
      (item) => item.pathname === "/v1/test-results/search-page",
    );
    assert.ok(request);
    assert.equal(request.searchParams.get("offset"), "50");
    assert.equal(request.searchParams.get("limit"), "25");
    assert.equal(request.searchParams.get("include_count"), "true");
    assert.deepEqual(
      [...new Set(request.searchParams.keys())]
        .filter((key) => !["offset", "limit", "include_count"].includes(key))
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
      ],
    );
    assert.equal(request.searchParams.get("test_execution_statuses"), "PASSED");

    const filterTrigger = target.querySelector(
      'button[aria-controls="search-option-3-filter-panel"]',
    );
    const panel = target.querySelector("dialog.search-option-filter-panel");
    assert.ok(filterTrigger);
    assert.ok(panel);
    assert.equal(panel.open, false);
    filterTrigger.click();
    await waitFor(() => panel.open);
    await waitFor(
      () =>
        browser.document.activeElement ===
        target.querySelector('[data-search-grid-filter-picker="from_date"]'),
    );
    assert.equal(filterTrigger.getAttribute("aria-expanded"), "true");
    assert.equal(target.querySelectorAll(".filter-group").length, 18);
    const canonicalFields = [
      "families",
      "test_result_statuses",
      "test_execution_statuses",
      "artefacts",
      "artefact_versions",
      "artefact_tracks",
      "environments",
      "test_plans",
      "test_cases",
      "artefact_stages",
      "artefact_is_archived",
      "rerun_is_requested",
      "execution_is_latest",
      "issues",
      "reviewer_ids",
      "execution_metadata",
      "from_date",
      "until_date",
      "template_ids",
    ];
    const editorFields = new Set(
      [...target.querySelectorAll("[data-search-grid-filter]")].map((element) =>
        element.getAttribute("data-search-grid-filter"),
      ),
    );
    for (const key of canonicalFields) assert.ok(editorFields.has(key), key);

    const closePanel = target.querySelector('[aria-label="Close filters"]');
    assert.ok(closePanel);
    closePanel.click();
    await waitFor(() => !panel.open);
    await waitFor(() => browser.document.activeElement === filterTrigger);
    assert.equal(filterTrigger.getAttribute("aria-expanded"), "false");

    const rows = [...target.querySelectorAll("tbody tr")];
    assert.equal(rows.length, 2);
    assert.deepEqual(
      rows.map(
        (row) =>
          row.querySelector("[data-test-result-id]")?.dataset.testResultId,
      ),
      ["12", "8"],
      "rows remain in API response order",
    );
    const cells = rows[0].querySelectorAll("td");
    assert.equal(cells[0].textContent, "2026-05-04 00:02:01");
    assert.equal(cells[1].textContent, "artefact-12");
    assert.match(cells[2].textContent, /case-12/);
    assert.match(cells[2].textContent, /category-12/);
    assert.equal(cells[3].textContent, "212");
    assert.equal(cells[4].textContent, "FAILED");
    assert.equal(cells[5].textContent, "stable");
    assert.equal(cells[6].textContent, "1.12");
    assert.equal(cells[7].textContent.trim(), "amd64/environment-12");
    assert.equal(cells[8].textContent, "plan-12");
    assert.equal(cells[9].querySelectorAll("[data-test-result-id]").length, 1);
    assert.equal(cells[9].querySelectorAll("a").length, 1);

    const run = cells[9].querySelector('a[aria-label="View Run for case-12"]');
    assert.ok(run);
    const runUrl = new URL(run.href);
    assert.equal(runUrl.pathname, "/custom/base/snaps/112");
    assert.equal(runUrl.searchParams.get("testExecutionId"), "212");
    assert.equal(runUrl.searchParams.get("testResultId"), "12");
    assert.equal(
      requests.filter((item) =>
        item.pathname.startsWith("/v1/test-results/search-page/"),
      ).length,
      0,
      "Details remains lazy until its action is used",
    );

    const details = cells[9].querySelector("[data-test-result-id]");
    assert.ok(details);
    details.click();
    await waitFor(() =>
      requests.some(
        (item) => item.pathname === "/v1/test-results/search-page/12",
      ),
    );
    await waitFor(() =>
      Boolean(target.querySelector("dialog.search-result-details[open]")),
    );
    const detailsDialog = target.querySelector("dialog.search-result-details");
    assert.ok(detailsDialog);
    detailsDialog.close();
    await waitFor(() => !detailsDialog.open);
    await waitFor(() => browser.document.activeElement === details);

    filterTrigger.click();
    await waitFor(() => panel.open);
    const versionInput = target.querySelector(
      '[data-search-grid-filter="artefact_versions"]',
    );
    assert.ok(versionInput);
    versionInput.value = "2.0";
    versionInput.dispatchEvent(new browser.Event("input", { bubbles: true }));
    await flush();
    assert.match(target.textContent, /Changes not applied/);
    assert.equal(
      requests.filter(
        (item) => item.pathname === "/v1/test-results/search-page",
      ).length,
      1,
      "editor changes remain drafts and do not fetch results",
    );

    target
      .querySelector(
        ".search-option-filter-panel .ds.dialog-content-footer button:last-child",
      )
      .click();
    await waitFor(() => ui.url.searchParams.get("artefact_versions") === "2.0");
    await waitFor(() => ui.url.searchParams.get("page") === "1");
    await waitFor(
      () =>
        requests.filter(
          (item) => item.pathname === "/v1/test-results/search-page",
        ).length === 2,
    );
    assert.equal(ui.url.searchParams.get("page_size"), "25");
    const appliedRequest = requests.filter(
      (item) => item.pathname === "/v1/test-results/search-page",
    )[1];
    assert.equal(appliedRequest.searchParams.get("offset"), "0");
    assert.equal(appliedRequest.searchParams.get("limit"), "25");
    assert.equal(appliedRequest.searchParams.get("artefact_versions"), "2.0");
    assert.equal(
      appliedRequest.searchParams.get("test_execution_statuses"),
      "PASSED",
    );
    await waitFor(
      () => target.querySelectorAll("tbody [data-test-result-id]").length === 2,
    );
    assert.equal(
      [...target.querySelectorAll("tbody tr")]
        .map(
          (row) =>
            row.querySelector("[data-test-result-id]")?.dataset.testResultId,
        )
        .join(","),
      "12,8",
    );
  } finally {
    await ui.destroy();
    target.remove();
  }
});

void test("Options 2–3 Created editors use UTC-only pickers and preserve one-sided bounds", async () => {
  assert.ok(app);
  for (const option of [2, 3]) {
    const requests = [];
    globalThis.fetch = async (input) => {
      const request = new URL(input instanceof Request ? input.url : input);
      requests.push(request);
      const offset = Number(request.searchParams.get("offset"));
      const limit = Number(request.searchParams.get("limit"));
      return json({ count: 100, offset, limit, rows: [resultRow(12)] });
    };

    const initialUrl = allFiltersUrl(option);
    initialUrl.searchParams.set(
      "from_date",
      "2026-01-02T04:04:05.123456+01:00",
    );
    initialUrl.searchParams.set("until_date", "2026-01-03T03:04:05.123456000Z");
    const target = browser.document.createElement("div");
    browser.document.body.append(target);
    const ui = app.mountSearchOption(target, initialUrl, [family], option);
    const searchRequests = () =>
      requests.filter(
        (request) => request.pathname === "/v1/test-results/search-page",
      );
    const openCreated = async () => {
      if (option === 2 || option === 2.5) {
        const menu = target.querySelector(
          '[data-search-grid-menu="from_date"]',
        );
        if (menu?.closest("[hidden]"))
          target
            .querySelector('thead button[aria-label="Filter Created"]')
            ?.click();
        await waitFor(
          () =>
            !target
              .querySelector('[data-search-grid-menu="from_date"]')
              ?.closest("[hidden]"),
        );
      } else {
        const isOpen = () =>
          target.querySelector("dialog.search-option-filter-panel")?.open;
        if (!isOpen()) {
          const trigger = target.querySelector(
            'button[aria-controls="search-option-3-filter-panel"]',
          );
          assert.ok(trigger, `Option ${option} filter trigger is mounted`);
          trigger.click();
        }
        await waitFor(() => isOpen());
      }
    };
    const setInput = async (selector, value) => {
      const input = target.querySelector(selector);
      assert.ok(input, `missing ${selector} in Option ${option}`);
      input.value = value;
      input.dispatchEvent(new browser.Event("input", { bubbles: true }));
      await flush();
      return input;
    };
    const submit = () => {
      if (option === 3)
        target
          .querySelector(
            ".search-option-filter-panel .ds.dialog-content-footer button:last-child",
          )
          .click();
      else
        target
          .querySelector('form[aria-label="Apply confirmed search filters"]')
          .dispatchEvent(
            new browser.Event("submit", { bubbles: true, cancelable: true }),
          );
    };

    try {
      await waitFor(() => searchRequests().length === 1);
      await openCreated();
      const fromPickerSelector = '[data-search-grid-filter-picker="from_date"]';
      const fromPicker = target.querySelector(fromPickerSelector);
      assert.ok(fromPicker);
      assert.equal(fromPicker.type, "datetime-local");
      assert.equal(fromPicker.value, "");
      assert.equal(
        target.querySelector('[data-search-grid-filter-picker="until_date"]')
          .value,
        "",
      );
      const dateEditor = target.querySelector(".date-filter");
      assert.ok(dateEditor);
      assert.equal(dateEditor.querySelectorAll('input[type="text"]').length, 0);
      assert.equal(
        dateEditor.querySelectorAll("[data-utc-picker-note]").length,
        2,
      );
      assert.deepEqual(
        [...dateEditor.querySelectorAll(".bound-label")].map((heading) =>
          heading.textContent.trim(),
        ),
        option === 2
          ? ["From", "To"]
          : ["Created — From (UTC)", "Created — To (UTC)"],
      );
      assert.equal(
        dateEditor.querySelectorAll(".utc-note").length,
        option === 2 ? 1 : 0,
      );
      assert.equal(
        target.querySelector('[data-search-grid-filter-picker="until_date"]')
          .value,
        "",
      );

      await setInput(fromPickerSelector, "2026-01-02T03:04:04");
      assert.equal(
        target.querySelector(fromPickerSelector).value,
        "2026-01-02T03:04:04",
      );
      assert.equal(searchRequests().length, 1, "date edits remain drafts");
      submit();
      await waitFor(() => ui.url.searchParams.get("page") === "1");
      await waitFor(() => searchRequests().length === 2);
      assert.equal(ui.url.searchParams.get("page_size"), "25");
      assert.equal(
        ui.url.searchParams.get("from_date"),
        "2026-01-02T03:04:04Z",
      );
      assert.equal(
        ui.url.searchParams.get("until_date"),
        "2026-01-03T03:04:05.123456000Z",
      );
      assert.equal(ui.url.searchParams.get("artefacts"), "widget");
      assert.equal(
        ui.url.searchParams.get("test_execution_statuses"),
        "PASSED",
      );
      assert.equal(ui.url.searchParams.get("template_ids"), "template-9");
      assert.equal(searchRequests().at(-1).searchParams.get("offset"), "0");
      assert.equal(searchRequests().at(-1).searchParams.get("limit"), "25");
    } finally {
      await ui.destroy();
      target.remove();
    }
  }
});

void test("Option 4 chip filters preserve exact server search and compact row actions", async () => {
  assert.ok(app);
  const requests = [];
  const serverRows = [resultRow(12), resultRow(8)];
  serverRows[0].test_result.created_at = "2026-05-04T03:02:01.987654+03:00";
  globalThis.fetch = async (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    requests.push(request);
    if (request.pathname === "/v1/test-results/search-page/12")
      return json(detailResult(12));
    if (request.pathname === "/v1/issues/42")
      return json({
        id: 42,
        source: "launchpad",
        project: "proj",
        key: "BUG-42",
        title: "Issue 42",
      });
    if (request.pathname === "/v1/users/43")
      return json({
        id: 43,
        name: "Reviewer 43",
        launchpad_handle: "reviewer-43",
      });
    const offset = Number(request.searchParams.get("offset"));
    const limit = Number(request.searchParams.get("limit"));
    return json({ count: 100, offset, limit, rows: serverRows });
  };

  const target = browser.document.createElement("div");
  browser.document.body.append(target);
  const ui = app.mountSearchOption(target, allFiltersUrl(4), [family], 4);
  try {
    await waitFor(() =>
      target.textContent.includes("Showing 51–52 of 100 results"),
    );
    assert.equal(
      target.querySelector("h1")?.textContent.trim(),
      "Search (Option 4)",
    );
    assert.equal(target.querySelector(".search-page > p"), null);
    const headers = [...target.querySelectorAll("thead th")].map((header) =>
      header.textContent.trim(),
    );
    assert.deepEqual(headers, [
      "Created",
      "Artefact",
      "Test Case",
      "Test Execution ID",
      "Status",
      "Track",
      "Version",
      "Environment",
      "Test Plan",
      "Actions",
    ]);

    const conditions = target.querySelector(
      '[aria-label="Confirmed search filters"]',
    );
    assert.ok(conditions);
    assert.equal(
      conditions.querySelectorAll(".condition").length,
      19,
      "all 19 canonical fields, including both date bounds, render as chips",
    );
    const canonicalKeys = [
      "families",
      "test_result_statuses",
      "test_execution_statuses",
      "artefacts",
      "artefact_versions",
      "artefact_tracks",
      "environments",
      "test_plans",
      "test_cases",
      "artefact_stages",
      "artefact_is_archived",
      "rerun_is_requested",
      "execution_is_latest",
      "issues",
      "reviewer_ids",
      "execution_metadata",
      "from_date",
      "until_date",
      "template_ids",
    ];
    const initialRequest = requests.find(
      (request) => request.pathname === "/v1/test-results/search-page",
    );
    assert.ok(initialRequest);
    assert.equal(initialRequest.searchParams.get("offset"), "50");
    assert.equal(initialRequest.searchParams.get("limit"), "25");
    assert.equal(initialRequest.searchParams.get("include_count"), "true");
    assert.deepEqual(
      [...new Set(initialRequest.searchParams.keys())]
        .filter((key) => !["offset", "limit", "include_count"].includes(key))
        .sort(),
      [...canonicalKeys].sort(),
    );
    assert.equal(
      initialRequest.searchParams.get("artefact_is_archived"),
      "false",
    );
    assert.equal(
      initialRequest.searchParams.get("execution_is_latest"),
      "false",
    );
    assert.equal(
      initialRequest.searchParams.get("test_execution_statuses"),
      "PASSED",
    );

    const rows = [...target.querySelectorAll("tbody tr")];
    assert.equal(rows.length, 2);
    assert.deepEqual(
      rows.map(
        (row) =>
          row.querySelector("[data-test-result-id]")?.dataset.testResultId,
      ),
      ["12", "8"],
      "server row order is retained without local filtering",
    );
    const cells = rows[0].querySelectorAll("td");
    assert.equal(cells[0].textContent, "2026-05-04 00:02:01");
    assert.equal(cells[1].textContent, "artefact-12");
    assert.match(cells[2].textContent, /case-12/);
    assert.match(cells[2].textContent, /category-12/);
    assert.equal(cells[3].textContent, "212");
    assert.equal(cells[4].textContent, "FAILED");
    assert.equal(cells[5].textContent, "stable");
    assert.equal(cells[6].textContent, "1.12");
    assert.equal(cells[7].textContent.trim(), "amd64/environment-12");
    assert.equal(cells[8].textContent, "plan-12");
    const run = cells[9].querySelector('a[aria-label="View Run for case-12"]');
    assert.ok(run);
    const runUrl = new URL(run.href);
    assert.equal(runUrl.pathname, "/custom/base/snaps/112");
    assert.equal(runUrl.searchParams.get("testExecutionId"), "212");
    assert.equal(runUrl.searchParams.get("testResultId"), "12");

    assert.equal(
      requests.filter((request) =>
        request.pathname.startsWith("/v1/test-results/search-page/"),
      ).length,
      0,
      "Details remains on demand",
    );
    const details = cells[9].querySelector("[data-test-result-id]");
    assert.ok(details);
    details.click();
    await waitFor(() =>
      requests.some(
        (request) => request.pathname === "/v1/test-results/search-page/12",
      ),
    );
    const detailsDialog = target.querySelector("dialog.search-result-details");
    assert.ok(detailsDialog);
    await waitFor(() => detailsDialog.open);
    detailsDialog.close();
    await waitFor(() => !detailsDialog.open);
    await waitFor(() => browser.document.activeElement === details);

    const submitSearch = async () => {
      target
        .querySelector('form[aria-label="Apply confirmed search filters"]')
        .dispatchEvent(
          new browser.Event("submit", { bubbles: true, cancelable: true }),
        );
    };
    const pageRequests = () =>
      requests.filter(
        (request) => request.pathname === "/v1/test-results/search-page",
      );

    target
      .querySelector('[aria-label="Remove Execution Status filter"]')
      .click();
    assert.equal(ui.url.searchParams.get("test_execution_statuses"), "PASSED");
    assert.equal(pageRequests().length, 1, "removing a chip is draft-only");
    await submitSearch();
    await waitFor(() => !ui.url.searchParams.has("test_execution_statuses"));
    await waitFor(() => pageRequests().length === 2);
    assert.equal(ui.url.searchParams.get("page"), "1");
    assert.equal(ui.url.searchParams.get("page_size"), "25");
    assert.equal(pageRequests()[1].searchParams.get("offset"), "0");
    assert.equal(pageRequests()[1].searchParams.get("limit"), "25");
    assert.equal(pageRequests()[1].searchParams.get("include_count"), "true");
    assert.equal(pageRequests()[1].searchParams.get("artefacts"), "widget");

    const addTrigger = [...target.querySelectorAll("button")].find((button) =>
      button.textContent.includes("+ Add filter"),
    );
    assert.ok(addTrigger);
    addTrigger.click();
    await waitFor(() =>
      Boolean(
        target.querySelector(
          '.condition-popover[aria-label="Add filter"] .filter-list',
        ),
      ),
    );
    const executionStatusOption = [
      ...target.querySelectorAll(
        '.condition-popover[aria-label="Add filter"] .filter-list button',
      ),
    ].find((button) => button.textContent.trim() === "Execution Status");
    assert.ok(
      executionStatusOption,
      "inactive SvelteKit-only field is offered",
    );
    executionStatusOption.click();
    await waitFor(() =>
      Boolean(target.querySelector('form[aria-label="Edit Execution Status"]')),
    );
    const passed = target.querySelector(
      'form[aria-label="Edit Execution Status"] input[value="PASSED"]',
    );
    assert.ok(passed);
    passed.click();
    assert.equal(passed.checked, true);
    const addForm = target.querySelector(
      'form[aria-label="Edit Execution Status"]',
    );
    const addFilter = [
      ...target.querySelectorAll(
        'form[aria-label="Edit Execution Status"] button',
      ),
    ].find((button) => button.textContent.trim() === "Add filter");
    assert.ok(addFilter);
    await waitFor(() => !addFilter.disabled);
    addForm.dispatchEvent(
      new browser.Event("submit", { bubbles: true, cancelable: true }),
    );
    assert.equal(
      pageRequests().length,
      2,
      "adding a chip does not fetch results",
    );
    await waitFor(() => target.textContent.includes("Changes not applied"));
    assert.equal(ui.url.searchParams.has("test_execution_statuses"), false);
    await submitSearch();
    await waitFor(
      () => ui.url.searchParams.get("test_execution_statuses") === "PASSED",
    );
    await waitFor(() => pageRequests().length === 3);
    assert.equal(ui.url.searchParams.get("page"), "1");
    assert.equal(ui.url.searchParams.get("page_size"), "25");
    assert.equal(
      pageRequests()[2].searchParams.get("test_execution_statuses"),
      "PASSED",
    );
    await waitFor(
      () => target.querySelectorAll("tbody [data-test-result-id]").length === 2,
    );
    assert.deepEqual(
      [...target.querySelectorAll("tbody [data-test-result-id]")].map(
        (button) => button.dataset.testResultId,
      ),
      ["12", "8"],
      "the server response remains in its original order after exact filter changes",
    );

    const executionChip = target.querySelector(
      'button[aria-label^="Edit Execution Status:"]',
    );
    assert.ok(executionChip);
    executionChip.click();
    await waitFor(() =>
      Boolean(target.querySelector('form[aria-label="Edit Execution Status"]')),
    );
    const editForm = target.querySelector(
      'form[aria-label="Edit Execution Status"]',
    );
    const passedEdit = editForm.querySelector('input[value="PASSED"]');
    const failedEdit = editForm.querySelector('input[value="FAILED"]');
    assert.ok(passedEdit);
    assert.ok(failedEdit);
    passedEdit.click();
    failedEdit.click();
    const save = [...editForm.querySelectorAll("button")].find(
      (button) => button.textContent.trim() === "Save changes",
    );
    assert.ok(save);
    await waitFor(() => !save.disabled);
    editForm.dispatchEvent(
      new browser.Event("submit", { bubbles: true, cancelable: true }),
    );
    await waitFor(() => target.textContent.includes("Changes not applied"));
    assert.equal(ui.url.searchParams.get("test_execution_statuses"), "PASSED");
    assert.equal(pageRequests().length, 3, "editing a chip stays a draft");
    await submitSearch();
    await waitFor(
      () => ui.url.searchParams.get("test_execution_statuses") === "FAILED",
    );
    await waitFor(() => pageRequests().length === 4);
    assert.equal(
      pageRequests()[3].searchParams.get("test_execution_statuses"),
      "FAILED",
    );
    assert.equal(pageRequests()[3].searchParams.get("offset"), "0");
    await waitFor(
      () => target.querySelectorAll("tbody [data-test-result-id]").length === 2,
    );

    target
      .querySelector('[aria-label="Remove Execution Status filter"]')
      .click();
    assert.equal(ui.url.searchParams.get("test_execution_statuses"), "FAILED");
    assert.equal(pageRequests().length, 4);
    await submitSearch();
    await waitFor(() => !ui.url.searchParams.has("test_execution_statuses"));
    await waitFor(() => pageRequests().length === 5);
    assert.equal(pageRequests()[4].searchParams.get("artefacts"), "widget");
    assert.equal(
      pageRequests()[4].searchParams.has("test_execution_statuses"),
      false,
    );
  } finally {
    await ui.destroy();
    target.remove();
  }
});

void test("Option 4 Created dialogs preserve legacy values and edit one UTC bound", async () => {
  assert.ok(app);
  const requests = [];
  globalThis.fetch = async (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    requests.push(request);
    const offset = Number(request.searchParams.get("offset"));
    const limit = Number(request.searchParams.get("limit"));
    return json({ count: 100, offset, limit, rows: [resultRow(12)] });
  };

  const from = "2026-01-02T04:04:05.123456+01:00";
  const until = "2026-01-03T03:04:05.123456000Z";
  const initialUrl = new URL(
    `http://localhost/custom/base/test-results/option-4?artefacts=widget&test_result_statuses=PASSED&from_date=${encodeURIComponent(from)}&until_date=${encodeURIComponent(until)}&page=3&page_size=25`,
  );
  const target = browser.document.createElement("div");
  browser.document.body.append(target);
  const ui = app.mountSearchOption(target, initialUrl, [family], 4);
  const pageRequests = () =>
    requests.filter(
      (request) => request.pathname === "/v1/test-results/search-page",
    );
  const openBound = async (field = "from_date") => {
    const bound = field === "from_date" ? "From" : "Until";
    const trigger = target.querySelector(
      `button[aria-label^="Edit Created — ${bound}:"]`,
    );
    assert.ok(trigger);
    assert.doesNotMatch(trigger.getAttribute("aria-label") ?? "", /\(UTC\)/);
    trigger.click();
    await waitFor(() =>
      Boolean(
        target.querySelector(`form[aria-label="Edit Created — ${bound}"]`),
      ),
    );
    return target.querySelector(`form[aria-label="Edit Created — ${bound}"]`);
  };
  const saveBound = async (form) => {
    const save = [...form.querySelectorAll("button")].find(
      (button) => button.textContent.trim() === "Save changes",
    );
    assert.ok(save);
    await waitFor(() => !save.disabled);
    save.click();
    await flush();
  };
  const apply = async (expectedCount) => {
    target
      .querySelector('form[aria-label="Apply confirmed search filters"]')
      .dispatchEvent(
        new browser.Event("submit", { bubbles: true, cancelable: true }),
      );
    await waitFor(() => pageRequests().length === expectedCount);
  };

  try {
    await waitFor(() => pageRequests().length === 1);
    const form = await openBound();
    assert.equal(form.querySelector("h2")?.textContent, "Created — From (UTC)");
    assert.deepEqual(
      [...form.querySelectorAll("h2, h3")]
        .filter((heading) => heading.textContent.includes("(UTC)"))
        .map((heading) => heading.textContent),
      ["Created — From (UTC)"],
      "the Option 4 dialog has one UTC heading and no duplicate bound heading",
    );
    const picker = form.querySelector('input[type="datetime-local"]');
    assert.ok(picker);
    assert.equal(
      picker.getAttribute("aria-label"),
      "Created — From (UTC)",
      "the input keeps its accessible name without a visible bound heading",
    );
    assert.equal(
      picker.value,
      "",
      "offset/fraction values stay out of the picker",
    );
    assert.equal(form.querySelectorAll('input[type="text"]').length, 0);
    assert.equal(form.querySelectorAll("[data-utc-picker-note]").length, 1);
    const cancel = [...form.querySelectorAll("button")].find(
      (button) => button.textContent.trim() === "Cancel",
    );
    assert.ok(cancel);
    cancel.click();
    await flush();
    assert.equal(
      pageRequests().length,
      1,
      "closing without edits does not fetch",
    );
    assert.equal(ui.url.searchParams.get("from_date"), from);
    assert.equal(ui.url.searchParams.get("until_date"), until);

    const statusTrigger = target.querySelector(
      'button[aria-label^="Edit Result status:"]',
    );
    assert.ok(statusTrigger);
    statusTrigger.click();
    await waitFor(() =>
      Boolean(target.querySelector('form[aria-label="Edit Result status"]')),
    );
    const statusForm = target.querySelector(
      'form[aria-label="Edit Result status"]',
    );
    statusForm.querySelector('input[value="PASSED"]').click();
    statusForm.querySelector('input[value="FAILED"]').click();
    await saveBound(statusForm);
    await apply(2);
    assert.equal(pageRequests()[1].searchParams.get("from_date"), from);
    assert.equal(pageRequests()[1].searchParams.get("until_date"), until);
    assert.equal(
      pageRequests()[1].searchParams.get("test_result_statuses"),
      "FAILED",
    );
    assert.equal(ui.url.searchParams.get("page_size"), "25");

    const editFrom = await openBound();
    const fromPicker = editFrom.querySelector('input[type="datetime-local"]');
    assert.ok(fromPicker);
    fromPicker.value = "2026-01-02T04:05:06";
    fromPicker.dispatchEvent(new browser.Event("input", { bubbles: true }));
    await flush();
    await saveBound(editFrom);
    await apply(3);
    assert.equal(ui.url.searchParams.get("from_date"), "2026-01-02T04:05:06Z");
    assert.equal(ui.url.searchParams.get("until_date"), until);
    assert.equal(
      pageRequests()[2].searchParams.get("from_date"),
      "2026-01-02T04:05:06Z",
    );
    assert.equal(pageRequests()[2].searchParams.get("until_date"), until);
    assert.equal(ui.url.searchParams.get("page_size"), "25");

    const clearFrom = await openBound();
    const clearedPicker = clearFrom.querySelector(
      'input[type="datetime-local"]',
    );
    assert.ok(clearedPicker);
    clearedPicker.value = "";
    clearedPicker.dispatchEvent(new browser.Event("input", { bubbles: true }));
    await flush();
    await saveBound(clearFrom);
    await apply(4);
    assert.equal(ui.url.searchParams.has("from_date"), false);
    assert.equal(ui.url.searchParams.get("until_date"), until);
    assert.equal(pageRequests()[3].searchParams.has("from_date"), false);
    assert.equal(pageRequests()[3].searchParams.get("until_date"), until);

    const reversedUrl = new URL(ui.url);
    reversedUrl.searchParams.set("from_date", "2026-01-04T00:00:00Z");
    reversedUrl.searchParams.set("until_date", "2026-01-03T00:00:00Z");
    ui.restore(reversedUrl);
    await flush();
    assert.match(target.textContent, /Invalid date range/);
    assert.equal(
      pageRequests().length,
      4,
      "reversed legacy bounds block requests",
    );
    const correctFrom = await openBound();
    const correction = correctFrom.querySelector(
      'input[type="datetime-local"]',
    );
    assert.ok(correction);
    correction.value = "2026-01-02T23:59:59";
    correction.dispatchEvent(new browser.Event("input", { bubbles: true }));
    await flush();
    await saveBound(correctFrom);
    await apply(5);
    assert.equal(ui.url.searchParams.get("from_date"), "2026-01-02T23:59:59Z");
    assert.equal(ui.url.searchParams.get("until_date"), "2026-01-03T00:00:00Z");
    assert.equal(ui.url.searchParams.get("page_size"), "25");
  } finally {
    await ui.destroy();
    target.remove();
  }
});

void test("Option 4 hydrates only a bounded set of ID labels when an ID editor opens", async () => {
  assert.ok(app);
  const issueIds = Array.from({ length: 250 }, (_, index) => 20001 + index);
  const reviewerIds = Array.from({ length: 200 }, (_, index) => 30001 + index);
  const requests = [];
  const labelRequests = [];
  const issueResolvers = new Map();
  const issueSignals = new Map();
  globalThis.fetch = async (input, options = {}) => {
    const request = new URL(input instanceof Request ? input.url : input);
    requests.push(request);
    const issue = /^\/v1\/issues\/(\d+)$/.exec(request.pathname);
    if (issue) {
      labelRequests.push(request);
      const id = Number(issue[1]);
      issueSignals.set(id, options.signal);
      return new Promise((resolve) => {
        issueResolvers.set(id, () => {
          resolve(
            json({
              id,
              source: "launchpad",
              project: "test-project",
              key: `BUG-${id}`,
              title: `Issue detail ${id}`,
            }),
          );
        });
      });
    }
    const reviewer = /^\/v1\/users\/(\d+)$/.exec(request.pathname);
    if (reviewer) {
      labelRequests.push(request);
      const id = Number(reviewer[1]);
      return json({
        id,
        name: `Reviewer detail ${id}`,
        launchpad_handle: `reviewer-${id}`,
      });
    }
    return json({
      count: 0,
      offset: Number(request.searchParams.get("offset")),
      limit: Number(request.searchParams.get("limit")),
      rows: [],
    });
  };

  const target = browser.document.createElement("div");
  browser.document.body.append(target);
  const ui = app.mountSearchOption(
    target,
    new URL(
      `http://localhost/custom/base/test-results/option-4?issues=${issueIds.join(",")}&reviewer_ids=${reviewerIds.join(",")}`,
    ),
    [family],
    4,
  );
  try {
    await waitFor(() =>
      target.textContent.includes("Showing 0–0 of 0 results"),
    );
    assert.equal(
      labelRequests.length,
      0,
      "mounting a large URL-backed ID filter sends no label-detail requests",
    );
    const issueChip = target.querySelector(
      'button[aria-label^="Edit Issues:"]',
    );
    const reviewerChip = target.querySelector(
      'button[aria-label^="Edit Reviewers:"]',
    );
    assert.ok(issueChip);
    assert.ok(reviewerChip);
    assert.match(issueChip.textContent, new RegExp(`#${issueIds[0]} \\+249`));
    assert.match(
      reviewerChip.textContent,
      new RegExp(`#${reviewerIds[0]} \\+199`),
    );
    assert.doesNotMatch(issueChip.textContent, /loading/i);
    assert.doesNotMatch(reviewerChip.textContent, /loading/i);

    const pageRequest = requests.find(
      (request) => request.pathname === "/v1/test-results/search-page",
    );
    assert.ok(pageRequest);
    assert.deepEqual(
      pageRequest.searchParams.getAll("issues"),
      issueIds.map(String),
      "large issue filters remain complete in the server request",
    );
    assert.deepEqual(
      pageRequest.searchParams.getAll("reviewer_ids"),
      reviewerIds.map(String),
      "large reviewer filters remain complete in the server request",
    );

    issueChip.click();
    await waitFor(() =>
      Boolean(target.querySelector('form[aria-label="Edit Issues"]')),
    );
    await waitFor(
      () =>
        labelRequests.filter((request) =>
          request.pathname.startsWith("/v1/issues/"),
        ).length === 10,
    );
    assert.deepEqual(
      labelRequests
        .filter((request) => request.pathname.startsWith("/v1/issues/"))
        .map((request) => Number(request.pathname.split("/").at(-1))),
      issueIds.slice(0, 10),
      "only the first ten selected issue IDs are hydrated",
    );
    assert.equal(
      labelRequests.filter((request) =>
        request.pathname.startsWith("/v1/users/"),
      ).length,
      0,
      "opening Issues does not hydrate reviewer labels",
    );
    const issueForm = target.querySelector('form[aria-label="Edit Issues"]');
    assert.equal(
      issueForm.querySelectorAll('[aria-label="Selected details"] li').length,
      issueIds.length,
      "the editor retains every selected issue ID",
    );
    issueForm
      .querySelector(`[aria-label="Remove selected ${issueIds[0]}"]`)
      .click();
    await waitFor(
      () =>
        issueForm.querySelectorAll('[aria-label="Selected details"] li')
          .length ===
        issueIds.length - 1,
    );
    assert.equal(
      labelRequests.filter((request) =>
        request.pathname.startsWith("/v1/issues/"),
      ).length,
      10,
      "editing the draft does not restart or expand label hydration",
    );
    assert.ok(
      [...issueSignals.values()].every((signal) => signal && !signal.aborted),
      "editing the draft does not cancel the bounded initial lookups",
    );
    for (const id of issueIds.slice(0, 10)) issueResolvers.get(id)?.();
    await waitFor(() =>
      issueForm.textContent.includes(`Issue detail ${issueIds[1]}`),
    );
    assert.match(
      target
        .querySelector('button[aria-label^="Edit Issues:"]')
        .getAttribute("aria-label"),
      new RegExp(`Issue detail ${issueIds[0]}`),
      "a resolved bounded lookup supplies a precise chip label",
    );
    [...issueForm.querySelectorAll("button")]
      .find((button) => button.textContent.trim() === "Cancel")
      .click();
    await waitFor(
      () => !target.querySelector('form[aria-label="Edit Issues"]'),
    );

    reviewerChip.click();
    await waitFor(() =>
      Boolean(target.querySelector('form[aria-label="Edit Reviewers"]')),
    );
    await waitFor(
      () =>
        labelRequests.filter((request) =>
          request.pathname.startsWith("/v1/users/"),
        ).length === 10,
    );
    assert.deepEqual(
      labelRequests
        .filter((request) => request.pathname.startsWith("/v1/users/"))
        .map((request) => Number(request.pathname.split("/").at(-1))),
      reviewerIds.slice(0, 10),
      "only the first ten selected reviewer IDs are hydrated",
    );
    const reviewerForm = target.querySelector(
      'form[aria-label="Edit Reviewers"]',
    );
    assert.equal(
      reviewerForm.querySelectorAll('[aria-label="Selected details"] li')
        .length,
      reviewerIds.length,
      "the editor retains every selected reviewer ID",
    );
    await waitFor(() =>
      reviewerForm.textContent.includes(`Reviewer detail ${reviewerIds[0]}`),
    );
    assert.match(
      target
        .querySelector('button[aria-label^="Edit Reviewers:"]')
        .getAttribute("aria-label"),
      new RegExp(`Reviewer detail ${reviewerIds[0]}`),
      "a resolved bounded lookup supplies a precise reviewer chip label",
    );
    assert.equal(labelRequests.length, 20);
    assert.equal(
      requests.filter(
        (request) => request.pathname === "/v1/test-results/search-page",
      ).length,
      1,
      "opening ID editors does not refetch test results",
    );
  } finally {
    for (const resolveIssue of issueResolvers.values()) resolveIssue();
    await ui.destroy();
    target.remove();
  }
});

void test("Option 4 picker exposes every filter and malformed/unknown raw conditions remain blocking", async () => {
  assert.ok(app);
  const requests = [];
  globalThis.fetch = async (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    requests.push(request);
    if (request.pathname === "/v1/test-results/search-page")
      return json({
        count: 0,
        offset: Number(request.searchParams.get("offset")),
        limit: Number(request.searchParams.get("limit")),
        rows: [],
      });
    return json({ detail: "not found" }, 404);
  };

  const target = browser.document.createElement("div");
  browser.document.body.append(target);
  const ui = app.mountSearchOption(
    target,
    new URL(
      "http://localhost/custom/base/test-results/option-4?execution_is_latest=maybe&hidden_filter=keep&page=2&page_size=25",
    ),
    [family],
    4,
  );
  try {
    await waitFor(() => Boolean(target.querySelector('[role="alert"]')));
    assert.equal(
      requests.length,
      0,
      "malformed and unknown filters block requests",
    );
    assert.ok(
      target.querySelector(
        '[aria-label="Edit Latest Execution: Invalid URL value"]',
      ),
    );

    const addTrigger = [...target.querySelectorAll("button")].find((button) =>
      button.textContent.includes("+ Add filter"),
    );
    assert.ok(addTrigger);
    addTrigger.click();
    await waitFor(() =>
      Boolean(
        target.querySelector(
          '.condition-popover[aria-label="Add filter"] .filter-list',
        ),
      ),
    );
    const options = [
      ...target.querySelectorAll(
        '.condition-popover[aria-label="Add filter"] .filter-list button',
      ),
    ].map((button) => button.textContent.trim());
    assert.equal(options.length, 18);
    for (const label of [
      "Family",
      "Result status",
      "Execution Status",
      "Issues",
      "Reviewers",
      "Artefact",
      "Artefact Version",
      "Artefact Stage",
      "Artefact Track",
      "Archived",
      "Rerun Requested",
      "Environment",
      "Test Case",
      "Test Plan",
      "Template ID",
      "Execution Metadata",
      "Created — From",
      "Created — Until",
    ])
      assert.ok(options.includes(label), label);

    const templateOption = options.includes("Template ID")
      ? [
          ...target.querySelectorAll(
            '.condition-popover[aria-label="Add filter"] .filter-list button',
          ),
        ].find((button) => button.textContent.trim() === "Template ID")
      : null;
    assert.ok(templateOption);
    templateOption.click();
    await waitFor(() =>
      Boolean(target.querySelector('form[aria-label="Edit Template ID"]')),
    );
    const templateForm = target.querySelector(
      'form[aria-label="Edit Template ID"]',
    );
    assert.ok(templateForm);
    const templateInput = templateForm.querySelector("input");
    assert.ok(templateInput);
    templateInput.value = "template-7";
    templateInput.dispatchEvent(new browser.Event("input", { bubbles: true }));
    const addTemplate = [...templateForm.querySelectorAll("button")].find(
      (button) => button.textContent.trim() === "Add filter",
    );
    assert.ok(addTemplate);
    await waitFor(() => !addTemplate.disabled);
    templateForm.dispatchEvent(
      new browser.Event("submit", { bubbles: true, cancelable: true }),
    );
    assert.equal(requests.length, 0, "unrelated chip edits remain drafts");
    target
      .querySelector('form[aria-label="Apply confirmed search filters"]')
      .dispatchEvent(
        new browser.Event("submit", { bubbles: true, cancelable: true }),
      );
    await waitFor(
      () => ui.url.searchParams.get("template_ids") === "template-7",
    );
    assert.equal(ui.url.searchParams.get("execution_is_latest"), "maybe");
    assert.equal(ui.url.searchParams.get("hidden_filter"), "keep");
    assert.equal(ui.url.searchParams.get("page"), "1");
    assert.equal(ui.url.searchParams.get("page_size"), "25");
    assert.equal(
      requests.length,
      0,
      "raw blockers survive an unrelated Search",
    );

    const removeInvalid = target.querySelector(
      '[aria-label="Remove Latest Execution filter"]',
    );
    assert.ok(removeInvalid);
    await waitFor(() => !removeInvalid.disabled);
    removeInvalid.click();
    await waitFor(
      () =>
        !target.querySelector(
          '[aria-label="Edit Latest Execution: Invalid URL value"]',
        ),
    );
    target
      .querySelector('form[aria-label="Apply confirmed search filters"]')
      .dispatchEvent(
        new browser.Event("submit", { bubbles: true, cancelable: true }),
      );
    await waitFor(() => !ui.url.searchParams.has("execution_is_latest"));
    assert.equal(ui.url.searchParams.get("hidden_filter"), "keep");
    assert.equal(
      requests.length,
      0,
      "removing one invalid field cannot erase unknown constraints",
    );

    const clear = [...target.querySelectorAll("button")].find(
      (button) => button.textContent.trim() === "Clear all",
    );
    assert.ok(clear);
    await waitFor(() => !clear.disabled);
    clear.click();
    await waitFor(() =>
      target.textContent.includes("Showing 0–0 of 0 results"),
    );
    assert.equal(ui.url.search, "?page_size=25");
    assert.equal(requests.length, 1);
    assert.equal(requests[0].searchParams.get("offset"), "0");
    assert.equal(requests[0].searchParams.get("limit"), "25");
    assert.equal(requests[0].searchParams.get("include_count"), "true");
    assert.deepEqual(
      [...requests[0].searchParams.keys()],
      ["offset", "limit", "include_count"],
      "Clear all explicitly removes raw blockers while retaining valid page size",
    );
  } finally {
    await ui.destroy();
    target.remove();
  }
});

void test("Option 3 defers selected issue and reviewer label requests until Filters opens", async () => {
  assert.ok(app);
  const requests = [];
  let resolveIssueResponse;
  let resolveReviewerResponse;
  const issueResponse = new Promise((resolve) => {
    resolveIssueResponse = resolve;
  });
  const reviewerResponse = new Promise((resolve) => {
    resolveReviewerResponse = resolve;
  });
  const issuePath = "/v1/issues/901";
  const reviewerPath = "/v1/users/902";
  globalThis.fetch = (input, options = {}) => {
    const request = new URL(input instanceof Request ? input.url : input);
    requests.push({ request, signal: options.signal });
    if (request.pathname === issuePath) return issueResponse;
    if (request.pathname === reviewerPath) return reviewerResponse;
    const offset = Number(request.searchParams.get("offset"));
    const limit = Number(request.searchParams.get("limit"));
    return json({ count: 1, offset, limit, rows: [resultRow(1)] });
  };

  const target = browser.document.createElement("div");
  browser.document.body.append(target);
  const url = new URL(
    "http://localhost/custom/base/test-results/option-3?page=1&page_size=25&issues=901&reviewer_ids=902",
  );
  const ui = app.mountSearchOption(target, url, [family], 3);
  try {
    await waitFor(() =>
      target.textContent.includes("Showing 1–1 of 1 results"),
    );
    const detailRequestCount = (pathname) =>
      requests.filter((item) => item.request.pathname === pathname).length;
    assert.equal(detailRequestCount(issuePath), 0);
    assert.equal(detailRequestCount(reviewerPath), 0);
    const initialSearch = requests.find(
      (item) => item.request.pathname === "/v1/test-results/search-page",
    );
    assert.ok(initialSearch);
    assert.equal(initialSearch.request.searchParams.get("issues"), "901");
    assert.equal(initialSearch.request.searchParams.get("reviewer_ids"), "902");

    const trigger = target.querySelector(
      'button[aria-controls="search-option-3-filter-panel"]',
    );
    assert.ok(trigger);
    trigger.click();
    const panel = target.querySelector("dialog.search-option-filter-panel");
    assert.ok(panel);
    await waitFor(() => panel.open);
    await waitFor(
      () =>
        detailRequestCount(issuePath) === 1 &&
        detailRequestCount(reviewerPath) === 1,
    );

    const issueRequest = requests.find(
      (item) => item.request.pathname === issuePath,
    );
    const reviewerRequest = requests.find(
      (item) => item.request.pathname === reviewerPath,
    );
    assert.ok(issueRequest?.signal);
    assert.ok(reviewerRequest?.signal);
    target.querySelector('[aria-label="Close filters"]').click();
    await waitFor(() => !panel.open);
    await flush();
    assert.equal(issueRequest.signal.aborted, false);
    assert.equal(reviewerRequest.signal.aborted, false);

    trigger.click();
    await waitFor(() => panel.open);
    assert.equal(detailRequestCount(issuePath), 1);
    assert.equal(detailRequestCount(reviewerPath), 1);
    assert.equal(ui.url.searchParams.get("issues"), "901");
    assert.equal(ui.url.searchParams.get("reviewer_ids"), "902");

    resolveIssueResponse(
      json({
        id: 901,
        source: "launchpad",
        project: "test-project",
        key: "BUG-901",
        title: "Seeded issue label",
      }),
    );
    resolveReviewerResponse(
      json({ id: 902, name: "Seeded reviewer", launchpad_handle: "reviewer" }),
    );
    await waitFor(
      () =>
        target.textContent.includes("Seeded issue label") &&
        target.textContent.includes("Seeded reviewer"),
    );

    target.querySelector('[aria-label="Close filters"]').click();
    await waitFor(() => !panel.open);
    trigger.click();
    await waitFor(() => panel.open);
    assert.match(target.textContent, /Seeded issue label/);
    assert.match(target.textContent, /Seeded reviewer/);
    assert.equal(detailRequestCount(issuePath), 1);
    assert.equal(detailRequestCount(reviewerPath), 1);
    assert.equal(ui.url.searchParams.get("issues"), "901");
    assert.equal(ui.url.searchParams.get("reviewer_ids"), "902");
  } finally {
    await ui.destroy();
    target.remove();
  }
});

void test("Option 3 invalidates selected ID labels across logout/login while Filters is closed or open", async () => {
  assert.ok(app);
  const profile = {
    id: 915,
    email: "same-profile@example.test",
    name: "Same Profile",
    launchpad_handle: "same-profile",
    teams: [],
    is_admin: false,
  };
  await app.userStore.refresh(() => Promise.resolve(json(null)));
  await app.userStore.refresh(() => Promise.resolve(json(profile)));
  const loadedSessionVersion = app.userStore.sessionVersion;

  const requests = [];
  let issueLabelRequests = 0;
  let reviewerLabelRequests = 0;
  const pendingIssueLabels = [];
  const pendingReviewerLabels = [];
  const issuePath = "/v1/issues/911";
  const reviewerPath = "/v1/users/912";
  globalThis.fetch = (input, options = {}) => {
    const request = new URL(input instanceof Request ? input.url : input);
    requests.push(request);
    if (request.pathname === issuePath) {
      issueLabelRequests += 1;
      if (issueLabelRequests > 2) {
        return new Promise((resolve, reject) => {
          const pending = { resolve, signal: options.signal };
          pendingIssueLabels.push(pending);
          if (options.signal?.aborted) {
            reject(new Error("Issue label request aborted"));
            return;
          }
          options.signal?.addEventListener(
            "abort",
            () => {
              reject(new Error("Issue label request aborted"));
            },
            { once: true },
          );
        });
      }
      return json({
        id: 911,
        source: "launchpad",
        project: "test-project",
        key: "BUG-911",
        title:
          issueLabelRequests === 1
            ? "Stale private issue label"
            : "Fresh private issue label",
      });
    }
    if (request.pathname === reviewerPath) {
      reviewerLabelRequests += 1;
      if (reviewerLabelRequests > 2) {
        return new Promise((resolve, reject) => {
          const pending = { resolve, signal: options.signal };
          pendingReviewerLabels.push(pending);
          if (options.signal?.aborted) {
            reject(new Error("Reviewer label request aborted"));
            return;
          }
          options.signal?.addEventListener(
            "abort",
            () => {
              reject(new Error("Reviewer label request aborted"));
            },
            { once: true },
          );
        });
      }
      return json({
        id: 912,
        name: "Same Profile Reviewer",
        launchpad_handle: "same-profile",
        email:
          reviewerLabelRequests === 1
            ? "stale-private@example.test"
            : "fresh-private@example.test",
      });
    }
    const offset = Number(request.searchParams.get("offset"));
    const limit = Number(request.searchParams.get("limit"));
    return json({ count: 1, offset, limit, rows: [resultRow(1)] });
  };

  const target = browser.document.createElement("div");
  browser.document.body.append(target);
  const ui = app.mountSearchOption(
    target,
    new URL(
      "http://localhost/custom/base/test-results/option-3?page=1&page_size=25&issues=911&reviewer_ids=912",
    ),
    [family],
    3,
  );
  try {
    await waitFor(() =>
      target.textContent.includes("Showing 1–1 of 1 results"),
    );
    const trigger = target.querySelector(
      'button[aria-controls="search-option-3-filter-panel"]',
    );
    const panel = target.querySelector("dialog.search-option-filter-panel");
    assert.ok(trigger);
    assert.ok(panel);
    assert.equal(issueLabelRequests, 0);
    assert.equal(reviewerLabelRequests, 0);

    trigger.click();
    await waitFor(() => panel.open);
    await waitFor(
      () =>
        target.textContent.includes("Stale private issue label") &&
        target.textContent.includes("stale-private@example.test"),
    );
    assert.equal(issueLabelRequests, 1);
    assert.equal(reviewerLabelRequests, 1);
    target.querySelector('[aria-label="Close filters"]').click();
    await waitFor(() => !panel.open);

    await app.userStore.refresh(() => Promise.resolve(json(null)));
    assert.equal(app.userStore.sessionVersion, loadedSessionVersion + 1);
    await waitFor(
      () =>
        !target.textContent.includes("Stale private issue label") &&
        !target.textContent.includes("stale-private@example.test"),
    );
    assert.equal(issueLabelRequests, 1);
    assert.equal(reviewerLabelRequests, 1);

    await app.userStore.refresh(() => Promise.resolve(json(profile)));
    assert.equal(app.userStore.sessionVersion, loadedSessionVersion + 2);
    await flush();
    assert.equal(app.userStore.current?.id, profile.id);
    assert.equal(
      target.textContent.includes("Stale private issue label"),
      false,
    );
    assert.equal(
      target.textContent.includes("stale-private@example.test"),
      false,
    );
    assert.equal(issueLabelRequests, 1);
    assert.equal(reviewerLabelRequests, 1);

    trigger.click();
    await waitFor(() => panel.open);
    await waitFor(
      () =>
        target.textContent.includes("Fresh private issue label") &&
        target.textContent.includes("fresh-private@example.test"),
    );
    assert.equal(issueLabelRequests, 2);
    assert.equal(reviewerLabelRequests, 2);
    assert.equal(ui.url.searchParams.get("issues"), "911");
    assert.equal(ui.url.searchParams.get("reviewer_ids"), "912");
    const searchRequest = requests.find(
      (request) => request.pathname === "/v1/test-results/search-page",
    );
    assert.ok(searchRequest);
    assert.equal(searchRequest.searchParams.get("issues"), "911");
    assert.equal(searchRequest.searchParams.get("reviewer_ids"), "912");

    await app.userStore.refresh(() => Promise.resolve(json(null)));
    assert.equal(app.userStore.sessionVersion, loadedSessionVersion + 3);
    await waitFor(
      () => issueLabelRequests === 3 && reviewerLabelRequests === 3,
    );
    assert.equal(pendingIssueLabels[0].signal.aborted, false);
    assert.equal(pendingReviewerLabels[0].signal.aborted, false);

    await app.userStore.refresh(() => Promise.resolve(json(profile)));
    assert.equal(app.userStore.sessionVersion, loadedSessionVersion + 4);
    await waitFor(
      () => issueLabelRequests === 4 && reviewerLabelRequests === 4,
    );
    await flush();
    assert.equal(
      pendingIssueLabels[0].signal.aborted,
      true,
      "logout-session work is canceled by the subsequent login transition",
    );
    assert.equal(pendingReviewerLabels[0].signal.aborted, true);
    assert.equal(
      pendingIssueLabels[1].signal.aborted,
      false,
      "the reviewer editor must not abort the current-session issue lookup",
    );
    assert.equal(
      pendingReviewerLabels[1].signal.aborted,
      false,
      "both current-session lookups remain live",
    );
    pendingIssueLabels[1].resolve(
      json({
        id: 911,
        source: "launchpad",
        project: "test-project",
        key: "BUG-911",
        title: "Open-session current issue label",
      }),
    );
    pendingReviewerLabels[1].resolve(
      json({
        id: 912,
        name: "Same Profile Reviewer",
        launchpad_handle: "same-profile",
        email: "open-session-current@example.test",
      }),
    );
    await waitFor(
      () =>
        target.textContent.includes("Open-session current issue label") &&
        target.textContent.includes("open-session-current@example.test"),
    );
    assert.equal(issueLabelRequests, 4, "no duplicate issue lookups");
    assert.equal(reviewerLabelRequests, 4, "no duplicate reviewer lookups");
    assert.equal(ui.url.searchParams.get("issues"), "911");
    assert.equal(ui.url.searchParams.get("reviewer_ids"), "912");
  } finally {
    await ui.destroy();
    target.remove();
    await app.userStore.refresh(() => Promise.resolve(json(null)));
  }
});

void test("Option 3 blocks unknown filters and reports recoverable network errors", async () => {
  assert.ok(app);
  let requests = 0;
  let shouldFail = false;
  globalThis.fetch = async (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    if (request.pathname !== "/v1/test-results/search-page") return json({});
    requests += 1;
    if (shouldFail) return json({ detail: "unavailable" }, 503);
    const offset = Number(request.searchParams.get("offset"));
    const limit = Number(request.searchParams.get("limit"));
    return json({ count: 1, offset, limit, rows: [resultRow(1)] });
  };

  const blockedTarget = browser.document.createElement("div");
  browser.document.body.append(blockedTarget);
  const blockedUrl = new URL(
    "http://localhost/custom/base/test-results/option-3?page=2&page_size=25&execution_is_latest=maybe&hidden_filter=keep",
  );
  const blocked = app.mountSearchOption(blockedTarget, blockedUrl, [family], 3);
  try {
    await waitFor(() => Boolean(blockedTarget.querySelector('[role="alert"]')));
    assert.equal(requests, 0);
    blockedTarget
      .querySelector('button[aria-controls="search-option-3-filter-panel"]')
      .click();
    await waitFor(
      () =>
        blockedTarget.querySelector("dialog.search-option-filter-panel").open,
    );
    assert.ok(
      blockedTarget.querySelector(
        '[data-search-grid-clear="execution_is_latest"]',
      ),
      "malformed active fields remain editable for explicit repair",
    );
    const clearAll = [...blockedTarget.querySelectorAll("button")].find(
      (button) => button.textContent.trim() === "Clear all",
    );
    assert.ok(clearAll);
    clearAll.click();
    await waitFor(() => requests === 1);
    assert.equal(blocked.url.searchParams.has("hidden_filter"), false);
    assert.equal(blocked.url.searchParams.get("page_size"), "25");
  } finally {
    await blocked.destroy();
    blockedTarget.remove();
  }

  shouldFail = true;
  const errorTarget = browser.document.createElement("div");
  browser.document.body.append(errorTarget);
  const errorUi = app.mountSearchOption(
    errorTarget,
    new URL("http://localhost/custom/base/test-results/option-3"),
    [family],
    3,
  );
  try {
    await waitFor(() => Boolean(errorTarget.querySelector('[role="alert"]')));
    assert.match(errorTarget.textContent, /Could not load test results/);
    shouldFail = false;
    [...errorTarget.querySelectorAll("button")]
      .find((button) => button.textContent.trim() === "Retry")
      .click();
    await waitFor(() =>
      errorTarget.textContent.includes("Showing 1–1 of 1 results"),
    );
    assert.equal(requests, 3);
  } finally {
    await errorUi.destroy();
    errorTarget.remove();
  }
});

void test("Option 2 modal invalidation restores focus to the current table", async () => {
  assert.ok(app);
  const requests = [];
  globalThis.fetch = async (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    requests.push(request);
    if (request.pathname === "/v1/test-results/search-page/12")
      return json(detailResult(12));
    const offset = Number(request.searchParams.get("offset"));
    const limit = Number(request.searchParams.get("limit"));
    return json({
      count: 60,
      offset,
      limit,
      rows: offset >= 50 ? [resultRow(99)] : [resultRow(12), resultRow(8)],
    });
  };

  const target = browser.document.createElement("div");
  browser.document.body.append(target);
  const ui = app.mountSearchOption(
    target,
    new URL(
      "http://localhost/custom/base/test-results/option-2?page=1&page_size=50",
    ),
    [family],
  );
  let destroyed = false;
  try {
    await waitFor(() =>
      Boolean(target.querySelector('[data-test-result-id="12"]')),
    );
    const tableRegion = target.querySelector(
      '[aria-label="Search results table"]',
    );
    assert.ok(tableRegion);

    const detailsTrigger = target.querySelector('[data-test-result-id="12"]');
    assert.ok(detailsTrigger);
    detailsTrigger.click();
    await waitFor(() =>
      requests.some(
        (request) => request.pathname === "/v1/test-results/search-page/12",
      ),
    );
    const pageTwo = new URL(ui.url);
    pageTwo.searchParams.set("page", "2");
    ui.restore(pageTwo);
    await waitFor(() =>
      Boolean(target.querySelector('[data-test-result-id="99"]')),
    );
    await waitFor(() => browser.document.activeElement === tableRegion);
    assert.equal(detailsTrigger.isConnected, false);

    const pageOne = new URL(ui.url);
    pageOne.searchParams.set("page", "1");
    ui.restore(pageOne);
    await waitFor(() =>
      Boolean(target.querySelector('[data-test-result-id="12"]')),
    );
    const valueTrigger = target.querySelector(
      '[data-search-grid-value-owner="12:issues"]',
    );
    assert.ok(valueTrigger);
    valueTrigger.click();
    await waitFor(() =>
      Boolean(target.querySelector("dialog.search-grid-value-dialog[open]")),
    );
    const nextPage = new URL(ui.url);
    nextPage.searchParams.set("page", "2");
    ui.restore(nextPage);
    await waitFor(() =>
      Boolean(target.querySelector('[data-test-result-id="99"]')),
    );
    await waitFor(() => browser.document.activeElement === tableRegion);
    assert.equal(valueTrigger.isConnected, false);

    const finalPageOne = new URL(ui.url);
    finalPageOne.searchParams.set("page", "1");
    ui.restore(finalPageOne);
    await waitFor(() =>
      Boolean(target.querySelector('[data-test-result-id="12"]')),
    );
    const staleDetailsTrigger = target.querySelector(
      '[data-test-result-id="12"]',
    );
    assert.ok(staleDetailsTrigger);
    staleDetailsTrigger.click();
    await waitFor(
      () =>
        requests.filter(
          (request) => request.pathname === "/v1/test-results/search-page/12",
        ).length === 2,
    );
    const outgoingTableRegion = tableRegion;
    const finalPageTwo = new URL(ui.url);
    finalPageTwo.searchParams.set("page", "2");
    ui.restore(finalPageTwo);
    await ui.destroy();
    destroyed = true;
    target.remove();
    await flush();
    assert.equal(outgoingTableRegion.isConnected, false);
    assert.notEqual(browser.document.activeElement, outgoingTableRegion);
  } finally {
    if (!destroyed) {
      await ui.destroy();
      target.remove();
    }
  }
});

void test("Option 2 blocks malformed and unknown filters until explicitly cleared", async () => {
  assert.ok(app);
  const requests = [];
  globalThis.fetch = async (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    requests.push(request);
    const offset = Number(request.searchParams.get("offset"));
    const limit = Number(request.searchParams.get("limit"));
    return json({ count: 1, offset, limit, rows: [resultRow(1)] });
  };
  const blockedUrl = new URL(
    "http://localhost/custom/base/test-results/option-2?page=2&page_size=25&artefact_is_archived=maybe&hidden_filter=keep-me",
  );
  const target = browser.document.createElement("div");
  browser.document.body.append(target);
  const ui = app.mountSearchOption(target, blockedUrl, [family]);
  try {
    await waitFor(() => Boolean(target.querySelector('[role="alert"]')));
    assert.equal(
      requests.filter(
        (request) => request.pathname === "/v1/test-results/search-page",
      ).length,
      0,
    );
    assert.equal(
      target.querySelectorAll('thead button[aria-label^="Filter "]').length,
      18,
    );

    target.querySelector('[aria-label="Filter Archived"]').click();
    await flush();
    target
      .querySelector('[data-search-grid-clear="artefact_is_archived"]')
      .click();
    target
      .querySelector('form[aria-label="Apply confirmed search filters"]')
      .dispatchEvent(
        new browser.Event("submit", { bubbles: true, cancelable: true }),
      );
    await waitFor(() => ui.url.searchParams.get("page") === "1");
    assert.equal(ui.url.searchParams.has("artefact_is_archived"), false);
    assert.equal(ui.url.searchParams.get("hidden_filter"), "keep-me");
    assert.equal(ui.url.searchParams.get("page_size"), "25");
    assert.equal(
      requests.filter(
        (request) => request.pathname === "/v1/test-results/search-page",
      ).length,
      0,
      "an unrelated unknown constraint must continue blocking the request",
    );

    const clearAll = [...target.querySelectorAll("button")].find(
      (button) => button.textContent.trim() === "Clear all",
    );
    assert.ok(clearAll);
    await waitFor(() => !clearAll.disabled);
    clearAll.click();
    await waitFor(() => !ui.url.searchParams.has("hidden_filter"));
    await waitFor(() =>
      requests.some(
        (request) => request.pathname === "/v1/test-results/search-page",
      ),
    );
    assert.equal(ui.url.searchParams.has("hidden_filter"), false);
    assert.equal(ui.url.searchParams.get("page_size"), "25");
    const request = requests.find(
      (item) => item.pathname === "/v1/test-results/search-page",
    );
    assert.ok(request);
    assert.equal(request.searchParams.get("offset"), "0");
    assert.equal(request.searchParams.get("limit"), "25");
  } finally {
    await ui.destroy();
    target.remove();
  }
});
