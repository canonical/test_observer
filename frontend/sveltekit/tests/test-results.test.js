// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { resolve } from "node:path";
import { build } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { Window } from "happy-dom";

/** @typedef {{ signal?: AbortSignal }} RequestOptions */
/** @typedef {{ path: string; options: RequestOptions }} TestRequest */
/** @typedef {(path: string, options: RequestOptions) => Promise<unknown>} ApiHandler */
/** @typedef {import("../src/lib/types/test-results-search-page").TestResultSearchPageRow} SearchPageRow */
/** @typedef {import("../src/lib/types/test-results-search-page").TestResultSearchPageResponse} SearchPage */
/**
 * @typedef {object} TestResultsHarness
 * @property {() => void} flushSync
 * @property {typeof import("./test-results-entry.js").mountPage} mountPage
 * @property {TestRequest[]} requests
 * @property {() => void} resetApi
 * @property {(handler: ApiHandler) => void} setHandler
 * @property {(component: object) => Promise<void>} unmountPage
 * @property {() => string} currentSearchUrl
 * @property {(url?: string) => void} resetSearchUrl
 * @property {() => void} searchHistoryBack
 * @property {() => void} searchHistoryForward
 * @property {(params: URLSearchParams) => {page: number; pageSize: number; problems: string[]}} parseSearchPageState
 * @property {(params: URLSearchParams, familyNames?: string[]) => {filters: import("../src/lib/searchPageFilters.ts").SearchFilters; problems: string[]}} parseSearchFilters
 * @property {(row: SearchPageRow, families: import("../src/lib/types/openapi.ts").FamilyResponse[] | null, basePath: string) => string | null} searchRunPath
 * @property {() => import("../src/lib/searchPageFilters.ts").SearchFilters} emptySearchFilters
 * @property {(filters: import("../src/lib/searchPageFilters.ts").SearchFilters, source?: URLSearchParams) => URLSearchParams} serializeSearchFilters
 * @property {(filters: import("../src/lib/searchPageFilters.ts").SearchFilters) => URLSearchParams} searchFilterRequestParams
 * @property {(filters: import("../src/lib/searchPageFilters.ts").SearchFilters) => string[]} validateSearchFilters
 * @property {(value: string) => string} encodeMetadataPart
 * @property {(fetcher: typeof fetch, apiRoot: string) => Promise<string[]>} fetchApiFamilyNames
 * @property {(event: {url: URL; fetch: typeof fetch}) => Promise<{apiFamilyNames: string[]; familyNamesError: boolean}>} loadTestResultsPage
 * @property {(count: number, pageSize: number) => number} searchLastPage
 * @property {(currentPage: number, totalPages: number) => (number | "gap")[]} searchPageItems
 * @property {(source: URLSearchParams, page: number) => URLSearchParams} searchPageParams
 * @property {(response: SearchPage) => {start: number; end: number; count: number}} searchPageRange
 * @property {(range: {start: number; end: number; count: number}) => string} searchPageRangeLabel
 * @property {(page: number, pageSize: number) => URLSearchParams} searchPageRequestParams
 * @property {(source: URLSearchParams, pageSize: number) => URLSearchParams} searchPageSizeParams
 * @property {(count: number, pageSize: number) => number} searchTotalPages
 */
/** @type {TestResultsHarness | undefined} */
let harness;
/** @type {Window | undefined} */
let browserWindow;
/** @type {Map<string, PropertyDescriptor | undefined>} */
const originalGlobals = new Map();

before(async () => {
  const buildResult =
    /** @type {{ output: { type: string; code: string }[] }[]} */ (
      /** @type {unknown} */ (
        await build({
          configFile: false,
          logLevel: "silent",
          plugins: [
            svelte({ compilerOptions: { runes: true } }),
            {
              name: "test-results-sveltekit-modules",
              resolveId(id) {
                if (id === "$app/state") return "\0test:$app/state";
                if (id === "$app/navigation") return "\0test:$app/navigation";
                if (id === "$app/paths") return "\0test:$app/paths";
              },
              load(id) {
                if (id === "\0test:$app/state") {
                  return `export { page } from ${JSON.stringify(resolve("tests/test-results-runtime.svelte.js"))};`;
                }
                if (id === "\0test:$app/navigation") {
                  return `export { testGoto as goto } from ${JSON.stringify(resolve("tests/test-results-runtime.svelte.js"))};`;
                }
                if (id === "\0test:$app/paths") {
                  return `export { testResolve as resolve } from ${JSON.stringify(resolve("tests/test-results-runtime.svelte.js"))};`;
                }
              },
            },
          ],
          resolve: {
            alias: [
              {
                find: "$lib/api/client",
                replacement: resolve("tests/test-results-api.js"),
              },
              { find: "$lib", replacement: resolve("src/lib") },
            ],
          },
          build: {
            write: false,
            lib: { entry: "tests/test-results-entry.js", formats: ["es"] },
            rolldownOptions: { output: { codeSplitting: false } },
          },
        })
      )
    );
  const bundle = buildResult[0]?.output.find((item) => item.type === "chunk");
  assert.ok(bundle, "test results page bundle should be generated");

  browserWindow = new Window({ url: "http://localhost/test-results" });
  for (const name of [
    "window",
    "document",
    "navigator",
    "customElements",
    "Comment",
    "Text",
    "Node",
    "Element",
    "HTMLElement",
    "HTMLMediaElement",
    "HTMLDialogElement",
    "Event",
    "MouseEvent",
    "ResizeObserver",
    "MutationObserver",
    "getComputedStyle",
    "requestAnimationFrame",
    "cancelAnimationFrame",
  ]) {
    originalGlobals.set(
      name,
      Object.getOwnPropertyDescriptor(globalThis, name),
    );
    Object.defineProperty(globalThis, name, {
      configurable: true,
      value:
        name === "window" ? browserWindow : Reflect.get(browserWindow, name),
    });
  }

  const importedModule = /** @type {unknown} */ (
    await import(
      `data:text/javascript;base64,${Buffer.from(bundle.code).toString("base64")}`
    )
  );
  harness = /** @type {TestResultsHarness} */ (importedModule);
});

after(async () => {
  for (const [name, descriptor] of originalGlobals) {
    if (descriptor) Object.defineProperty(globalThis, name, descriptor);
    else Reflect.deleteProperty(globalThis, name);
  }
  if (browserWindow) await browserWindow.happyDOM.abort();
});

/**
 * @param {number} id
 * @param {string} name
 * @returns {SearchPageRow}
 */
function makeRow(id, name) {
  return {
    test_result: {
      id,
      created_at: "2026-01-02T03:04:05Z",
      name,
      category: `category-${id}`,
      status: "PASSED",
    },
    test_execution: {
      id: id + 100,
      environment: { name: `lab-${id}` },
      test_plan: `smoke-${id}`,
    },
    artefact: {
      id: id + 200,
      name: `artefact-${id}`,
      version: `1.${id}`,
      track: `stable-${id}`,
      family: "snap",
    },
    artefact_build: { architecture: `amd64-${id}` },
  };
}

/**
 * @param {SearchPageRow[]} rows
 * @param {{limit?: number; offset?: number; count?: number}} [paging]
 * @returns {SearchPage}
 */
function makePage(rows, paging = {}) {
  return {
    limit: paging.limit ?? 50,
    offset: paging.offset ?? 0,
    count: paging.count ?? rows.length,
    test_results: rows,
  };
}

/** @param {number} count @param {number} limit @param {number} offset */
function makeRows(count, limit, offset) {
  return Array.from(
    { length: Math.min(limit, Math.max(0, count - offset)) },
    (_, index) => {
      const id = count - offset - index;
      return makeRow(id, `server-row-${id}`);
    },
  );
}

async function settlePromises() {
  for (let index = 0; index < 10; index += 1) await Promise.resolve();
  await new Promise((resolve) => setTimeout(resolve, 0));
  harness?.flushSync();
}

/** @param {{querySelector: (selector: string) => unknown}} target @param {string} selector */
function clickButton(target, selector) {
  const button = target.querySelector(selector);
  assert.ok(button);
  /** @type {HTMLButtonElement} */ (/** @type {unknown} */ (button)).click();
}

/** @param {{querySelector: (selector: string) => unknown}} target */
function openFilterDrawer(target) {
  const button = target.querySelector(
    'button[aria-controls="test-result-filter-drawer"]',
  );
  assert.ok(button);
  /** @type {HTMLButtonElement} */ (/** @type {unknown} */ (button)).click();
}

/** @param {unknown} target @param {"input" | "change"} type */
function dispatchBrowserEvent(target, type) {
  assert.ok(browserWindow);
  const eventTarget = /** @type {{dispatchEvent: (event: Event) => void}} */ (
    /** @type {unknown} */ (target)
  );
  eventTarget.dispatchEvent(
    /** @type {Event} */ (
      /** @type {unknown} */ (new browserWindow.Event(type, { bubbles: true }))
    ),
  );
}

/** @param {{artefactFamilies?: import("../src/lib/types/openapi.ts").FamilyResponse[] | null; apiFamilyNames?: string[]; familyNamesError?: boolean}} [data] */
function mountInDocument(data = {}) {
  assert.ok(harness);
  assert.ok(browserWindow);
  const target = browserWindow.document.createElement("div");
  browserWindow.document.body.append(target);
  const pageData = {
    artefactFamilies: [],
    apiFamilyNames: ["snap", "deb", "charm", "image", "solution"],
    familyNamesError: false,
    ...data,
  };
  const component = harness.mountPage(
    /** @type {HTMLElement} */ (/** @type {unknown} */ (target)),
    pageData,
  );
  return { component, target };
}

/** @param {object} component @param {{ remove: () => void }} target */
async function unmountFromDocument(component, target) {
  assert.ok(harness);
  await harness.unmountPage(component);
  target.remove();
}

/** @param {TestRequest | undefined} request @param {{pageSize?: number; offset?: number}} [paging] */
function assertRequest(request, { pageSize = 50, offset = 0 } = {}) {
  assert.ok(request);
  assert.ok(request.options.signal);
  const url = new URL(request.path, "http://localhost/");
  assert.equal(url.pathname, "/test-results/search-page");
  assert.deepEqual(
    [...url.searchParams.entries()],
    [
      ["limit", String(pageSize)],
      ["offset", String(offset)],
      ["include_count", "true"],
    ],
  );
}

function deferred() {
  /** @type {((value: unknown) => void) | undefined} */
  let resolve;
  /** @type {((reason?: unknown) => void) | undefined} */
  let reject;
  const promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return {
    promise,
    /** @param {unknown} value */
    resolve: (value) => {
      if (!resolve) throw new Error("Promise resolver is not set");
      resolve(value);
    },
    /** @param {unknown} reason */
    reject: (reason) => {
      if (!reject) throw new Error("Promise rejecter is not set");
      reject(reason);
    },
  };
}

void test("loads the first server page and preserves server row order", async () => {
  assert.ok(harness);
  harness.resetApi();
  harness.resetSearchUrl();
  harness.setHandler(() =>
    Promise.resolve(
      makePage([makeRow(5, "server-newest"), makeRow(2, "server-next")]),
    ),
  );
  const { component, target } = mountInDocument();
  await settlePromises();

  const region = target.querySelector(".results-page");
  assert.ok(region);
  assert.equal(region.getAttribute("aria-busy"), "false");
  assert.equal(
    target.querySelector("h1")?.textContent.trim(),
    "Search Results (WIP)",
  );
  const grid = target.querySelector(".sv-grid-root");
  assert.ok(grid, target.innerHTML);
  const gridShell = target.querySelector(".sv-grid-shell");
  assert.ok(gridShell);
  assert.match(gridShell.getAttribute("style") ?? "", /height:\s*100%/);
  assert.equal(grid.classList.contains("sv-grid-no-row-hover"), false);
  const resultRows = [...target.querySelectorAll("tbody tr.sv-grid-row")];
  assert.equal(resultRows.length, 2);
  assert.match(resultRows[0].textContent, /server-newest/);
  assert.match(resultRows[1].textContent, /server-next/);
  const headers = [...target.querySelectorAll("thead th")].map((cell) =>
    cell.textContent.trim(),
  );
  assert.deepEqual(headers, [
    "Created",
    "Artefact",
    "Test Case",
    "Category",
    "Test Execution ID",
    "Status",
    "Track",
    "Version",
    "Environment / Build Architecture",
    "Test Plan",
    "Run",
  ]);
  assert.equal(
    target.querySelectorAll(".sv-grid-resize-handle[role=separator]").length,
    11,
  );
  assert.equal(target.querySelectorAll('[aria-label^="Filter "]').length, 0);
  assert.equal(target.querySelectorAll('[role="checkbox"]').length, 0);
  assert.equal(resultRows[0].querySelectorAll("button").length, 0);

  const pager = target.querySelector('nav[aria-label="Test result pages"]');
  assert.ok(pager);
  assert.equal(pager.parentElement, region);
  assert.equal(target.querySelector(".pager")?.closest(".grid-wrapper"), null);
  assert.equal(
    target.querySelector(".range")?.textContent.trim(),
    "Showing 1–2 of 2 results",
  );
  assert.equal(
    target.querySelector('[aria-current="page"]')?.textContent.trim(),
    "1",
  );
  assert.equal(
    target
      .querySelector('[aria-label="Previous page"]')
      ?.hasAttribute("disabled"),
    true,
  );
  assert.equal(
    target.querySelector('[aria-label="Next page"]')?.hasAttribute("disabled"),
    true,
  );
  assertRequest(harness.requests[0]);

  await unmountFromDocument(component, target);
});

void test("Run links use configured family routes and the deployment base", async () => {
  assert.ok(harness);
  const mapped = makeRow(5, "routed-case");
  mapped.artefact.family = "custom family";
  const unmapped = makeRow(2, "unmapped-case");
  unmapped.artefact.family = "deb";
  harness.resetApi();
  harness.resetSearchUrl();
  harness.setHandler(() => Promise.resolve(makePage([mapped, unmapped])));

  const { component, target } = mountInDocument({
    artefactFamilies: [{ name: "custom family" }],
  });
  await settlePromises();

  const link = target.querySelector('a[aria-label="View Run for routed-case"]');
  assert.ok(link);
  assert.equal(
    link.getAttribute("href"),
    "/custom/base/family/custom%20family/205?testExecutionId=105&testResultId=5",
  );
  assert.match(target.textContent, /Run unavailable/);
  const unmappedRow = [...target.querySelectorAll("tbody tr")].find((row) =>
    row.textContent.includes("unmapped-case"),
  );
  assert.ok(unmappedRow);
  assert.equal(unmappedRow.querySelector("a"), null);
  assert.equal(
    harness.requests.length,
    1,
    "rendering links sends no extra request",
  );

  await unmountFromDocument(component, target);
});

void test("Run path uses API family names, encoded route names, and both IDs", () => {
  assert.ok(harness);
  const row = makeRow(5, "case");
  row.artefact.family = "custom route";
  assert.equal(
    harness.searchRunPath(row, [{ name: "custom route" }], "/custom/base/"),
    "/custom/base/family/custom%20route/205?testExecutionId=105&testResultId=5",
  );
  assert.equal(
    harness.searchRunPath(row, [{ name: "custom route" }], "/"),
    "/family/custom%20route/205?testExecutionId=105&testResultId=5",
  );
  assert.equal(
    harness.searchRunPath(row, [{ name: "another-family" }], ""),
    null,
  );
  assert.equal(harness.searchRunPath(row, null, ""), null);
});

void test("requests an applied page URL with only server paging parameters", async () => {
  assert.ok(harness);
  harness.resetApi();
  harness.resetSearchUrl("http://localhost/test-results?page=3&page_size=25");
  harness.setHandler((path) => {
    const url = new URL(path, "http://localhost/");
    return Promise.resolve(
      makePage(
        makeRows(
          57,
          Number(url.searchParams.get("limit")),
          Number(url.searchParams.get("offset")),
        ),
        {
          limit: Number(url.searchParams.get("limit")),
          offset: Number(url.searchParams.get("offset")),
          count: 57,
        },
      ),
    );
  });
  const { component, target } = mountInDocument();
  await settlePromises();

  assertRequest(harness.requests[0], { pageSize: 25, offset: 50 });
  assert.equal(
    target.querySelector(".range")?.textContent.trim(),
    "Showing 51–57 of 57 results",
  );
  assert.equal(
    target.querySelector('[aria-current="page"]')?.textContent.trim(),
    "3",
  );

  await unmountFromDocument(component, target);
});

void test("invalid, duplicate, unsupported, and unsafe URL paging state sends no request", async () => {
  assert.ok(harness);
  const invalidUrls = [
    "?page=0",
    "?page=1tail",
    "?page=9007199254740992",
    "?page=900719925474099&page_size=100",
    "?page_size=10",
    "?page=1&page=2",
    "?page_size=25&page_size=50",
    "?families=unknown",
    "?test_result_statuses=UNKNOWN",
    "?from_date=not-a-date",
    "?from_date=2026-02-02T00%3A00%3A00Z&until_date=2026-02-01T00%3A00%3A00Z",
    "?unsupported_filter=value",
    "?artefacts=",
    "?artefact_is_archived=TRUE",
    "?execution_is_latest=true&execution_is_latest=false",
    "?issues=0",
    "?issues=any&issues=42",
    "?reviewer_ids=9007199254740992",
    "?execution_metadata=not-json",
    "?execution_metadata=",
    "?assignee_ids=any",
  ];
  for (const query of invalidUrls) {
    harness.resetApi();
    harness.resetSearchUrl(`http://localhost/test-results${query}`);
    const { component, target } = mountInDocument();
    await settlePromises();
    assert.equal(harness.requests.length, 0, query);
    const alert = target.querySelector('[role="alert"]');
    assert.ok(alert, query);
    assert.match(alert.textContent, /No request was sent/);
    await unmountFromDocument(component, target);
  }
});

void test("page navigation pushes history; size changes reset page one", async () => {
  assert.ok(harness);
  harness.resetApi();
  harness.resetSearchUrl("http://localhost/test-results?page=1&page_size=25");
  harness.setHandler((_path) => {
    const params = new URL(_path, "http://localhost/").searchParams;
    const limit = Number(params.get("limit"));
    const offset = Number(params.get("offset"));
    return Promise.resolve(
      makePage(makeRows(56, limit, offset), { limit, offset, count: 56 }),
    );
  });
  const { component, target } = mountInDocument();
  await settlePromises();

  clickButton(target, '[aria-label="Next page"]');
  await settlePromises();
  assertRequest(harness.requests[1], { pageSize: 25, offset: 25 });
  assert.equal(
    target.querySelector(".range")?.textContent.trim(),
    "Showing 26–50 of 56 results",
  );

  harness.searchHistoryBack();
  await settlePromises();
  assertRequest(harness.requests[2], { pageSize: 25, offset: 0 });
  assert.equal(
    target.querySelector('[aria-current="page"]')?.textContent.trim(),
    "1",
  );
  harness.searchHistoryForward();
  await settlePromises();
  assertRequest(harness.requests[3], { pageSize: 25, offset: 25 });
  assert.equal(
    target.querySelector('[aria-current="page"]')?.textContent.trim(),
    "2",
  );

  const pageSize = target.querySelector("#search-page-size");
  assert.ok(pageSize);
  assert.ok(browserWindow);
  const pageSizeSelect = /** @type {HTMLSelectElement} */ (
    /** @type {unknown} */ (pageSize)
  );
  pageSizeSelect.value = "100";
  pageSizeSelect.dispatchEvent(
    /** @type {Event} */ (
      /** @type {unknown} */ (
        new browserWindow.Event("change", { bubbles: true })
      )
    ),
  );
  await settlePromises();
  assertRequest(harness.requests[4], { pageSize: 100, offset: 0 });
  assert.equal(
    target.querySelector('[aria-current="page"]')?.textContent.trim(),
    "1",
  );
  assert.equal(
    target.querySelector(".range")?.textContent.trim(),
    "Showing 1–56 of 56 results",
  );
  const searchUrl = target.querySelector(".results-page");
  assert.ok(searchUrl);
  assert.equal(searchUrl.getAttribute("aria-busy"), "false");

  await unmountFromDocument(component, target);
});

void test("out-of-range pages replace the URL with the last valid page and refetch", async () => {
  assert.ok(harness);
  harness.resetApi();
  harness.resetSearchUrl("http://localhost/test-results?page=8&page_size=25");
  harness.setHandler((_path) => {
    const params = new URL(_path, "http://localhost/").searchParams;
    const limit = Number(params.get("limit"));
    const offset = Number(params.get("offset"));
    return Promise.resolve(
      makePage(makeRows(57, limit, offset), { limit, offset, count: 57 }),
    );
  });
  const { component, target } = mountInDocument();
  await settlePromises();

  assert.equal(harness.requests.length, 2);
  assertRequest(harness.requests[0], { pageSize: 25, offset: 175 });
  assertRequest(harness.requests[1], { pageSize: 25, offset: 50 });
  assert.equal(
    target.querySelector('[aria-current="page"]')?.textContent.trim(),
    "3",
  );
  assert.equal(
    target.querySelector(".range")?.textContent.trim(),
    "Showing 51–57 of 57 results",
  );
  harness.searchHistoryBack();
  await settlePromises();
  assert.equal(
    harness.requests.length,
    2,
    "out-of-range correction replaces rather than pushes history",
  );
  assert.equal(
    target.querySelector('[aria-current="page"]')?.textContent.trim(),
    "3",
  );

  await unmountFromDocument(component, target);
});

void test("empty results keep the range and pager available", async () => {
  assert.ok(harness);
  harness.resetApi();
  harness.resetSearchUrl("http://localhost/test-results");
  harness.setHandler(() => Promise.resolve(makePage([], { count: 0 })));
  const { component, target } = mountInDocument();
  await settlePromises();

  assert.match(target.textContent, /No test results found/);
  assert.equal(target.querySelector(".sv-grid-root"), null);
  assert.equal(
    target.querySelector(".range")?.textContent.trim(),
    "Showing 0–0 of 0 results",
  );
  assert.ok(target.querySelector('nav[aria-label="Test result pages"]'));
  assert.equal(target.querySelector(".pager-jump"), null);
  assert.equal(
    target
      .querySelector('[aria-label="Previous page"]')
      ?.hasAttribute("disabled"),
    true,
  );
  assert.equal(
    target.querySelector('[aria-label="Next page"]')?.hasAttribute("disabled"),
    true,
  );

  await unmountFromDocument(component, target);
});

void test("an empty deep link is replaced with canonical page one", async () => {
  assert.ok(harness);
  harness.resetApi();
  harness.resetSearchUrl("http://localhost/test-results?page=7&page_size=25");
  harness.setHandler((path) => {
    const params = new URL(path, "http://localhost/").searchParams;
    return Promise.resolve(
      makePage([], {
        limit: Number(params.get("limit")),
        offset: Number(params.get("offset")),
        count: 0,
      }),
    );
  });
  const { component, target } = mountInDocument();
  await settlePromises();

  assert.equal(harness.requests.length, 2);
  assertRequest(harness.requests[0], { pageSize: 25, offset: 150 });
  assertRequest(harness.requests[1], { pageSize: 25, offset: 0 });
  const correctedUrl = harness.currentSearchUrl();
  assert.equal(
    new URL(correctedUrl).searchParams.get("page"),
    "1",
    `${correctedUrl}: ${JSON.stringify(harness.requests.map(({ path }) => path))}`,
  );
  assert.equal(
    target.querySelector(".range")?.textContent.trim(),
    "Showing 0–0 of 0 results",
  );
  harness.searchHistoryBack();
  await settlePromises();
  assert.equal(
    harness.requests.length,
    2,
    "empty correction replaces the deep-link history entry",
  );

  await unmountFromDocument(component, target);
});

void test("loading, failure, and retry show no stale pager and retry the current URL", async () => {
  assert.ok(harness);
  harness.resetApi();
  harness.resetSearchUrl("http://localhost/test-results?page=2&page_size=25");
  let attempts = 0;
  harness.setHandler((_path) => {
    attempts += 1;
    return attempts === 1
      ? Promise.reject(new Error("backend unavailable"))
      : Promise.resolve(
          makePage([makeRow(7, "after-retry")], {
            limit: 25,
            offset: 25,
            count: 26,
          }),
        );
  });
  const { component, target } = mountInDocument();
  await settlePromises();

  assert.ok(target.querySelector('[role="alert"]'));
  assert.match(target.textContent, /could not be loaded/i);
  assert.equal(target.querySelector(".pager"), null);
  assert.equal(target.querySelector(".sv-grid-root"), null);
  clickButton(target, ".retry-button");
  await settlePromises();

  assertRequest(harness.requests[0], { pageSize: 25, offset: 25 });
  assertRequest(harness.requests[1], { pageSize: 25, offset: 25 });
  assert.equal(harness.requests[0]?.options.signal?.aborted, true);
  assert.match(
    target.querySelector("tbody tr")?.textContent ?? "",
    /after-retry/,
  );
  assert.equal(
    target.querySelector(".range")?.textContent.trim(),
    "Showing 26–26 of 26 results",
  );

  await unmountFromDocument(component, target);
});

void test("count missing, null, negative, or unsafe is treated as an invalid response", async () => {
  assert.ok(harness);
  const invalidCounts = [undefined, null, -1, Number.MAX_SAFE_INTEGER + 1];
  for (const count of invalidCounts) {
    harness.resetApi();
    harness.resetSearchUrl();
    harness.setHandler(() =>
      Promise.resolve({
        limit: 50,
        offset: 0,
        count,
        test_results: [],
      }),
    );
    const { component, target } = mountInDocument();
    await settlePromises();
    assert.ok(target.querySelector('[role="alert"]'));
    assert.equal(target.querySelector(".pager"), null);
    assert.equal(target.querySelector(".sv-grid-root"), null);
    await unmountFromDocument(component, target);
  }
});

void test("stale page responses cannot replace the active URL's rows", async () => {
  assert.ok(harness);
  harness.resetApi();
  harness.resetSearchUrl("http://localhost/test-results?page=1&page_size=25");
  const oldPage = deferred();
  let secondRequest = false;
  harness.setHandler((path) => {
    const offset = Number(
      new URL(path, "http://localhost/").searchParams.get("offset"),
    );
    if (offset === 25) {
      secondRequest = true;
      return oldPage.promise;
    }
    return Promise.resolve(
      makePage([makeRow(100 - offset, `active-page-${offset}`)], {
        limit: 25,
        offset,
        count: 50,
      }),
    );
  });
  const { component, target } = mountInDocument();
  await settlePromises();

  clickButton(target, '[aria-label="Next page"]');
  await settlePromises();
  assert.equal(secondRequest, true);
  assert.match(target.textContent, /Loading test results/);
  assert.equal(target.querySelector(".pager"), null);
  assert.equal(target.querySelector("tbody tr"), null);

  harness.searchHistoryBack();
  await settlePromises();
  assert.match(
    target.querySelector("tbody tr")?.textContent ?? "",
    /active-page-0/,
  );
  oldPage.resolve(
    makePage([makeRow(75, "stale-page-2")], {
      limit: 25,
      offset: 25,
      count: 50,
    }),
  );
  await settlePromises();
  assert.match(
    target.querySelector("tbody tr")?.textContent ?? "",
    /active-page-0/,
  );
  assert.doesNotMatch(target.textContent, /stale-page-2/);

  await unmountFromDocument(component, target);
});

void test("page parser, URL preservation, ranges, and compact page windows", () => {
  assert.ok(harness);
  assert.deepEqual(harness.parseSearchPageState(new URLSearchParams()), {
    page: 1,
    pageSize: 50,
    problems: [],
  });
  assert.deepEqual(
    harness.parseSearchPageState(new URLSearchParams("page=3&page_size=25")),
    {
      page: 3,
      pageSize: 25,
      problems: [],
    },
  );
  assert.equal(harness.searchPageRequestParams(3, 25).get("offset"), "50");
  assert.deepEqual(
    [
      ...harness
        .searchPageParams(new URLSearchParams("page_size=25&x=a&x=b"), 4)
        .entries(),
    ],
    [
      ["page_size", "25"],
      ["x", "a"],
      ["x", "b"],
      ["page", "4"],
    ],
  );
  assert.deepEqual(
    [
      ...harness
        .searchPageSizeParams(new URLSearchParams("page=8&other=keep"), 100)
        .entries(),
    ],
    [
      ["page", "1"],
      ["other", "keep"],
      ["page_size", "100"],
    ],
  );
  assert.deepEqual(harness.searchPageItems(5, 6), [1, 2, 3, 4, 5, 6]);
  assert.deepEqual(harness.searchPageItems(50, 100), [
    1,
    "gap",
    49,
    50,
    51,
    "gap",
    100,
  ]);
  assert.deepEqual(harness.searchPageItems(1, 100), [1, 2, "gap", 100]);
  assert.deepEqual(harness.searchPageItems(100, 100), [1, "gap", 99, 100]);
  assert.equal(harness.searchTotalPages(57, 25), 3);
  assert.equal(harness.searchLastPage(0, 25), 1);
  const range = harness.searchPageRange(
    makePage(makeRows(57, 25, 50), { limit: 25, offset: 50, count: 57 }),
  );
  assert.deepEqual(range, { start: 51, end: 57, count: 57 });
  assert.equal(
    harness.searchPageRangeLabel(range),
    "Showing 51–57 of 57 results",
  );
});

void test("session-only resize controls remain and no width persistence is introduced", async () => {
  const { readFile } = await import("node:fs/promises");
  const source = await readFile(
    new URL("../src/routes/test-results/+page.svelte", import.meta.url),
    "utf8",
  );
  assert.match(source, /columnResize/);
  assert.match(source, /fitColumns/);
  assert.match(source, /enableRowHover/);
  assert.doesNotMatch(source, /localStorage|sessionStorage/);
});

void test("filter drawer keeps results visible and requires explicit Search to apply drafts", async () => {
  assert.ok(harness);
  harness.resetApi();
  harness.resetSearchUrl(
    "http://localhost/test-results?page=2&page_size=25&families=snap&artefact_stages=edge",
  );
  harness.setHandler((path) => {
    const params = new URL(path, "http://localhost/").searchParams;
    const limit = Number(params.get("limit"));
    const offset = Number(params.get("offset"));
    return Promise.resolve(
      makePage(makeRows(75, limit, offset), { limit, offset, count: 75 }),
    );
  });
  const { component, target } = mountInDocument({
    artefactFamilies: [{ name: "snap" }],
  });
  await settlePromises();
  assert.equal(harness.requests.length, 1);

  const toggle = target.querySelector(
    'button[aria-controls="test-result-filter-drawer"]',
  );
  assert.ok(toggle);
  openFilterDrawer(target);
  await settlePromises();
  const dialog = target.querySelector("dialog#test-result-filter-drawer");
  assert.ok(dialog);
  assert.equal(dialog.hasAttribute("open"), true);
  assert.equal(
    dialog.getAttribute("aria-labelledby"),
    "test-result-filter-title",
  );
  assert.equal(toggle.getAttribute("aria-haspopup"), "dialog");
  assert.equal(toggle.getAttribute("aria-expanded"), "true");
  assert.equal(dialog.contains(target.ownerDocument.activeElement), true);

  const visibleRows = target.querySelectorAll("tbody tr.sv-grid-row");
  assert.ok(visibleRows.length > 0);
  assert.ok(visibleRows.length <= 25);
  assert.equal(target.querySelector(".grid-wrapper")?.closest("dialog"), null);
  assert.match(
    target.querySelector(".range")?.textContent ?? "",
    /of 75 results/,
  );
  assert.ok(target.querySelector('nav[aria-label="Test result pages"]'));

  for (const selector of [
    '[name="families"]',
    '[name="test_result_statuses"]',
    '[name="artefacts"]',
    '[name="artefact_versions"]',
    '[name="artefact_tracks"]',
    '[name="environments"]',
    '[name="test_cases"]',
    '[name="test_plans"]',
    '[name="from_date"]',
    '[name="until_date"]',
    '[name="template_ids"]',
    '[name="artefact_stages"][value=""]',
    '[name="artefact_stages"][value="edge"]',
    '[name="test_execution_statuses"]',
    '[name="artefact_is_archived"]',
    '[name="rerun_is_requested"]',
    '[name="execution_is_latest"]',
    '[name="issues-mode"]',
    '[name="reviewer_ids-mode"]',
    '[name="metadata-category"]',
    '[name="metadata-value"]',
  ]) {
    assert.ok(dialog.querySelector(selector), `drawer contains ${selector}`);
  }
  assert.equal(
    /** @type {HTMLInputElement} */ (
      /** @type {unknown} */ (
        dialog.querySelector('[name="artefact_stages"][value="edge"]')
      )
    ).checked,
    true,
  );
  assert.equal(
    dialog.querySelector('[name="artefact_stages"][value="stable"]'),
    null,
  );
  assert.doesNotMatch(dialog.textContent, /not configured/);

  clickButton(target, '[aria-label="Close filters"]');
  await settlePromises();
  assert.equal(toggle.getAttribute("aria-expanded"), "false");
  assert.equal(target.ownerDocument.activeElement, toggle);

  openFilterDrawer(target);
  await settlePromises();
  const artefactInput = target.querySelector('[name="artefacts"]');
  assert.ok(artefactInput);
  const input = /** @type {HTMLTextAreaElement} */ (
    /** @type {unknown} */ (artefactInput)
  );
  input.value = "draft-only";
  dispatchBrowserEvent(input, "input");
  await settlePromises();
  assert.equal(harness.requests.length, 1, "draft edits do not fetch");
  assert.equal(
    new URL(harness.currentSearchUrl()).searchParams.has("artefacts"),
    false,
  );
  assert.match(target.textContent, /Changes not applied/);

  assert.ok(browserWindow);
  dialog.dispatchEvent(
    new browserWindow.KeyboardEvent("keydown", {
      key: "Escape",
      bubbles: true,
    }),
  );
  await settlePromises();
  assert.equal(dialog.hasAttribute("open"), false);
  assert.equal(toggle.getAttribute("aria-expanded"), "false");
  assert.equal(target.ownerDocument.activeElement, toggle);
  assert.equal(harness.requests.length, 1, "Escape closes without applying");

  openFilterDrawer(target);
  await settlePromises();
  assert.equal(
    /** @type {HTMLTextAreaElement} */ (
      /** @type {unknown} */ (target.querySelector('[name="artefacts"]'))
    ).value,
    "draft-only",
    "closing preserves the unsubmitted draft",
  );
  clickButton(target, '.filter-form button[type="submit"]');
  await settlePromises();
  assert.equal(harness.requests.length, 2);
  const appliedUrl = new URL(harness.currentSearchUrl());
  assert.equal(appliedUrl.searchParams.get("page"), "1");
  assert.equal(appliedUrl.searchParams.get("page_size"), "25");
  assert.equal(appliedUrl.searchParams.get("families"), "snap");
  assert.deepEqual(appliedUrl.searchParams.getAll("artefact_stages"), ["edge"]);
  assert.deepEqual(appliedUrl.searchParams.getAll("artefacts"), ["draft-only"]);
  assert.equal(toggle.getAttribute("aria-expanded"), "false");
  assert.equal(
    target.ownerDocument.activeElement,
    toggle,
    "applying Search restores focus after navigation completes",
  );
  await unmountFromDocument(component, target);
});

void test("filter URL parsing and canonical serialization use repeated exact values", () => {
  assert.ok(harness);
  const parsed = harness.parseSearchFilters(
    new URLSearchParams(
      "families=snap&families=deb&test_result_statuses=PASSED&artefacts=zeta&artefacts=alpha&from_date=2026-01-01T00%3A00%3A00Z",
    ),
  );
  assert.deepEqual(parsed.problems, []);
  assert.deepEqual(parsed.filters.families, ["snap", "deb"]);
  const serialized = harness.serializeSearchFilters(
    parsed.filters,
    new URLSearchParams("page=9&page_size=25"),
  );
  assert.deepEqual(
    [...serialized.entries()],
    [
      ["page_size", "25"],
      ["page", "1"],
      ["families", "deb"],
      ["families", "snap"],
      ["test_result_statuses", "PASSED"],
      ["artefacts", "alpha"],
      ["artefacts", "zeta"],
      ["from_date", "2026-01-01T00:00:00Z"],
    ],
  );
  const request = harness.searchFilterRequestParams(parsed.filters);
  assert.deepEqual(request.getAll("families"), ["deb", "snap"]);
  assert.equal(request.get("page"), null);
  assert.equal(request.get("page_size"), null);
});

void test("invalid filter values and unsupported URL keys fail closed", () => {
  assert.ok(harness);
  const futureFamily = harness.parseSearchFilters(
    new URLSearchParams("families=future-family"),
    ["snap", "deb", "charm", "image", "solution"],
  );
  assert.match(futureFamily.problems[0] ?? "", /unsupported family/);
  assert.deepEqual(futureFamily.filters.families, ["future-family"]);

  for (const query of [
    "test_result_statuses=UNKNOWN",
    "from_date=2026-02-02T00%3A00%3A00Z&until_date=2026-02-01T00%3A00%3A00Z",
    "from_date=not-a-date",
    "families=",
    "unsupported_filter=value",
  ]) {
    const parsed = harness.parseSearchFilters(new URLSearchParams(query));
    assert.ok(parsed.problems.length > 0, query);
  }
  assert.deepEqual(
    harness.validateSearchFilters(harness.emptySearchFilters()),
    [],
  );
});

void test("advanced filter URL codecs preserve false, empty stage, IDs, and Base64 metadata", () => {
  assert.ok(harness);
  const category = "device:🌱, category";
  const value = "arm64, revision: 1 — café";
  const metadata = `${harness.encodeMetadataPart(category)}:${harness.encodeMetadataPart(value)}`;
  const params = new URLSearchParams();
  params.append("artefact_stages", "");
  params.append("artefact_stages", "edge");
  params.append("artefact_is_archived", "false");
  params.append("rerun_is_requested", "true");
  params.append("execution_is_latest", "false");
  params.append("test_execution_statuses", "PASSED");
  params.append("test_execution_statuses", "FAILED");
  params.append("template_ids", "template,with punctuation");
  params.append("issues", "11");
  params.append("issues", "12");
  params.append("reviewer_ids", "any");
  params.append("execution_metadata", metadata);
  const parsed = harness.parseSearchFilters(params);
  assert.deepEqual(parsed.problems, []);
  assert.deepEqual(parsed.filters.artefact_stages, ["", "edge"]);
  assert.equal(parsed.filters.artefact_is_archived, false);
  assert.equal(parsed.filters.rerun_is_requested, true);
  assert.equal(parsed.filters.execution_is_latest, false);
  assert.deepEqual(parsed.filters.test_execution_statuses, [
    "PASSED",
    "FAILED",
  ]);
  assert.deepEqual(parsed.filters.template_ids, ["template,with punctuation"]);
  assert.deepEqual(parsed.filters.issues, [11, 12]);
  assert.equal(parsed.filters.reviewer_ids, "any");
  assert.deepEqual(parsed.filters.execution_metadata, [
    { category, values: [value] },
  ]);

  const serialized = harness.serializeSearchFilters(
    parsed.filters,
    new URLSearchParams("page=9&page_size=25"),
  );
  assert.equal(serialized.get("page"), "1");
  assert.equal(serialized.get("page_size"), "25");
  assert.deepEqual(serialized.getAll("artefact_stages"), ["", "edge"]);
  assert.equal(serialized.get("artefact_is_archived"), "false");
  assert.deepEqual(serialized.getAll("issues"), ["11", "12"]);
  assert.deepEqual(serialized.getAll("reviewer_ids"), ["any"]);
  assert.deepEqual(serialized.getAll("execution_metadata"), [metadata]);
});

void test("advanced filters reject malformed booleans, ID sentinels, and metadata pairs", () => {
  assert.ok(harness);
  for (const query of [
    "artefact_is_archived=TRUE",
    "rerun_is_requested=1",
    "execution_is_latest=yes",
    "execution_is_latest=true&execution_is_latest=false",
    "issues=any&issues=11",
    "reviewer_ids=none&reviewer_ids=any",
    "issues=0",
    "reviewer_ids=-1",
    "issues=9007199254740992",
    "reviewer_ids=2147483648",
    "execution_metadata=not-json",
    "execution_metadata=YQ==",
    "execution_metadata=:",
    `execution_metadata=${harness.encodeMetadataPart("x")}:`,
    `execution_metadata=${harness.encodeMetadataPart("x")}:${harness.encodeMetadataPart("🌱".repeat(201))}`,
  ]) {
    assert.ok(
      harness.parseSearchFilters(new URLSearchParams(query)).problems.length >
        0,
      query,
    );
  }
  assert.deepEqual(
    harness.parseSearchFilters(new URLSearchParams("artefact_stages="))
      .problems,
    [],
    "an explicitly empty stage is valid and distinct from omitted stage",
  );
  assert.deepEqual(
    harness.parseSearchFilters(new URLSearchParams("artefact_stages=%20%20"))
      .problems.length > 0,
    true,
  );
});

void test("an unfiltered Search page loads families for draft validation", async () => {
  assert.ok(harness);
  /** @type {string[]} */
  const requestedUrls = [];
  const data = await harness.loadTestResultsPage({
    url: new URL("http://localhost/test-results"),
    fetch: (input) => {
      assert.equal(typeof input, "string");
      requestedUrls.push(/** @type {string} */ (input));
      return Promise.resolve(
        new Response(
          JSON.stringify([{ name: "snap" }, { name: "future-family" }]),
          { status: 200 },
        ),
      );
    },
  });
  assert.deepEqual(requestedUrls, ["http://localhost:30000/v1/families"]);
  assert.deepEqual(data.apiFamilyNames, ["snap", "future-family"]);
  assert.equal(data.familyNamesError, false);

  harness.resetApi();
  harness.resetSearchUrl();
  harness.setHandler((path) => {
    const params = new URL(path, "http://localhost/").searchParams;
    return Promise.resolve(
      makePage([], {
        limit: Number(params.get("limit")),
        offset: Number(params.get("offset")),
        count: 0,
      }),
    );
  });
  const { component, target } = mountInDocument(data);
  await settlePromises();

  openFilterDrawer(target);
  await settlePromises();
  const familyInput = target.querySelector('[name="families"]');
  assert.ok(familyInput);
  const textarea = /** @type {HTMLTextAreaElement} */ (
    /** @type {unknown} */ (familyInput)
  );
  textarea.value = "future-family";
  dispatchBrowserEvent(textarea, "input");
  clickButton(target, '.filter-form button[type="submit"]');
  await settlePromises();

  const searchRequests = harness.requests.filter(({ path }) =>
    path.startsWith("test-results/search-page?"),
  );
  assert.equal(searchRequests.length, 2);
  assert.deepEqual(
    new URL(searchRequests[1].path, "http://localhost/").searchParams.getAll(
      "families",
    ),
    ["future-family"],
  );
  await unmountFromDocument(component, target);
});

void test("family URL validation permits custom families from the API", async () => {
  assert.ok(harness);

  harness.resetApi();
  harness.resetSearchUrl(
    "http://localhost/test-results?families=future-family&execution_is_latest=false&issues=42",
  );
  harness.setHandler((path) => {
    const params = new URL(path, "http://localhost/").searchParams;
    assert.deepEqual(params.getAll("families"), ["future-family"]);
    assert.equal(params.get("execution_is_latest"), "false");
    assert.deepEqual(params.getAll("issues"), ["42"]);
    return Promise.resolve(makePage([], { count: 0 }));
  });
  const { component, target } = mountInDocument({
    apiFamilyNames: ["snap", "future-family"],
    familyNamesError: false,
  });
  await settlePromises();

  assert.equal(harness.requests.length, 1);
  assert.deepEqual(
    new URL(harness.requests[0].path, "http://localhost/").searchParams.getAll(
      "families",
    ),
    ["future-family"],
  );
  assert.equal(target.querySelector('[role="alert"]'), null);
  await unmountFromDocument(component, target);
});

void test("family names are fetched from the families API", async () => {
  assert.ok(harness);
  /** @type {{url: string; credentials: RequestCredentials | undefined; csrf: string | null}[]} */
  const requests = [];
  const familyNames = await harness.fetchApiFamilyNames((input, init = {}) => {
    if (typeof input !== "string") {
      throw new TypeError("Expected the API URL to be a string.");
    }
    const url = new URL(input);
    requests.push({
      url: url.href,
      credentials: init.credentials,
      csrf: new Headers(init.headers).get("X-CSRF-Token"),
    });
    return Promise.resolve(
      new Response(JSON.stringify([{ name: "future-family" }]), {
        status: 200,
      }),
    );
  }, "https://api.example");

  assert.deepEqual(familyNames, ["future-family"]);
  assert.deepEqual(requests, [
    {
      url: "https://api.example/v1/families",
      credentials: "include",
      csrf: "1",
    },
  ]);
});

void test("family URLs fail closed when the API family list cannot be loaded", async () => {
  assert.ok(harness);
  harness.resetApi();
  harness.resetSearchUrl(
    "http://localhost/test-results?families=future-family",
  );
  const { component, target } = mountInDocument({
    apiFamilyNames: [],
    familyNamesError: true,
  });
  await settlePromises();

  assert.equal(harness.requests.length, 0);
  assert.match(
    target.querySelector('[role="alert"]')?.textContent ?? "",
    /API family list/,
  );
  assert.match(
    target.querySelector('[role="alert"]')?.textContent ?? "",
    /No request was sent/,
  );
  await unmountFromDocument(component, target);
});

void test("filter drafts do not fetch until Search; apply, clear, page-size, and history use applied state", async () => {
  assert.ok(harness);
  harness.resetApi();
  harness.resetSearchUrl(
    "http://localhost/test-results?page=3&page_size=25&families=snap&artefacts=old",
  );
  const requests = harness.requests;
  harness.setHandler((path) => {
    const params = new URL(path, "http://localhost/").searchParams;
    const limit = Number(params.get("limit"));
    const offset = Number(params.get("offset"));
    const row = makeRow(10 + requests.length, "applied-row");
    return Promise.resolve(makePage([row], { limit, offset, count: 80 }));
  });
  const { component, target } = mountInDocument();
  await settlePromises();
  assert.equal(harness.requests.length, 1);
  const firstRequest = new URL(harness.requests[0].path, "http://localhost/");
  assert.deepEqual(firstRequest.searchParams.getAll("families"), ["snap"]);
  assert.deepEqual(firstRequest.searchParams.getAll("artefacts"), ["old"]);

  openFilterDrawer(target);
  await settlePromises();
  const artefactInput = target.querySelector('[name="artefacts"]');
  assert.ok(artefactInput);
  assert.ok(browserWindow);
  const input = /** @type {HTMLTextAreaElement} */ (
    /** @type {unknown} */ (artefactInput)
  );
  input.value = "new";
  input.dispatchEvent(
    /** @type {Event} */ (
      /** @type {unknown} */ (
        new browserWindow.Event("input", { bubbles: true })
      )
    ),
  );
  await settlePromises();
  assert.equal(harness.requests.length, 1, "editing drafts must not fetch");
  assert.match(target.textContent, /Changes not applied/);
  assert.equal(
    new URL(harness.currentSearchUrl()).searchParams.get("artefacts"),
    "old",
  );

  clickButton(target, '.filter-form button[type="submit"]');
  await settlePromises();
  assert.equal(harness.requests.length, 2);
  let appliedUrl = new URL(harness.currentSearchUrl());
  assert.equal(appliedUrl.searchParams.get("page"), "1");
  assert.equal(appliedUrl.searchParams.get("page_size"), "25");
  assert.deepEqual(appliedUrl.searchParams.getAll("families"), ["snap"]);
  assert.deepEqual(appliedUrl.searchParams.getAll("artefacts"), ["new"]);
  const appliedRequest = new URL(harness.requests[1].path, "http://localhost/");
  assert.deepEqual(appliedRequest.searchParams.getAll("artefacts"), ["new"]);

  clickButton(target, ".clear-all-button");
  await settlePromises();
  assert.equal(harness.requests.length, 2, "Clear all only changes the draft");
  assert.equal(
    new URL(harness.currentSearchUrl()).searchParams.get("artefacts"),
    "new",
  );
  assert.equal(input.value, "");
  assert.match(target.textContent, /Changes not applied/);
  clickButton(target, '.filter-form button[type="submit"]');
  await settlePromises();
  assert.equal(harness.requests.length, 3);
  appliedUrl = new URL(harness.currentSearchUrl());
  assert.equal(appliedUrl.searchParams.get("page"), "1");
  assert.equal(appliedUrl.searchParams.get("page_size"), "25");
  assert.equal(appliedUrl.searchParams.has("families"), false);
  assert.equal(appliedUrl.searchParams.has("artefacts"), false);

  harness.searchHistoryBack();
  await settlePromises();
  assert.equal(harness.requests.length, 4);
  assert.equal(
    /** @type {HTMLTextAreaElement} */ (
      /** @type {unknown} */ (target.querySelector('[name="artefacts"]'))
    ).value,
    "new",
  );
  assert.equal(
    new URL(harness.requests[3].path, "http://localhost/").searchParams.get(
      "artefacts",
    ),
    "new",
  );
  harness.searchHistoryBack();
  await settlePromises();
  assert.equal(harness.requests.length, 5);
  assert.equal(
    /** @type {HTMLTextAreaElement} */ (
      /** @type {unknown} */ (target.querySelector('[name="artefacts"]'))
    ).value,
    "old",
  );
  assert.equal(
    new URL(harness.requests[4].path, "http://localhost/").searchParams.get(
      "artefacts",
    ),
    "old",
  );

  await unmountFromDocument(component, target);
});

void test("reordering equivalent list filters does not show unapplied changes", async () => {
  assert.ok(harness);
  harness.resetApi();
  harness.resetSearchUrl(
    "http://localhost/test-results?families=snap&families=deb",
  );
  harness.setHandler(() => Promise.resolve(makePage([], { count: 0 })));
  const { component, target } = mountInDocument();
  await settlePromises();
  assert.equal(harness.requests.length, 1);

  openFilterDrawer(target);
  await settlePromises();
  const familiesField = target.querySelector('[name="families"]');
  assert.ok(familiesField);
  assert.ok(browserWindow);
  const field = /** @type {HTMLTextAreaElement} */ (
    /** @type {unknown} */ (familiesField)
  );
  field.value = "deb\nsnap";
  field.dispatchEvent(
    /** @type {Event} */ (
      /** @type {unknown} */ (
        new browserWindow.Event("input", { bubbles: true })
      )
    ),
  );
  await settlePromises();

  assert.equal(
    harness.requests.length,
    1,
    "equivalent filters must not refetch",
  );
  assert.doesNotMatch(target.textContent, /Changes not applied/);

  await unmountFromDocument(component, target);
});

void test("filter drafts preserve exact values with commas, whitespace, and line breaks", async () => {
  assert.ok(harness);
  harness.resetApi();
  harness.resetSearchUrl();
  harness.setHandler((path) => {
    const params = new URL(path, "http://localhost/").searchParams;
    const limit = Number(params.get("limit"));
    const offset = Number(params.get("offset"));
    return Promise.resolve(makePage([], { limit, offset, count: 0 }));
  });
  const { component, target } = mountInDocument();
  await settlePromises();
  assert.equal(harness.requests.length, 1);

  openFilterDrawer(target);
  await settlePromises();
  const testCaseInput = target.querySelector('[name="test_cases"]');
  assert.ok(testCaseInput);
  assert.ok(browserWindow);
  const textarea = /** @type {HTMLTextAreaElement} */ (
    /** @type {unknown} */ (testCaseInput)
  );
  textarea.value =
    "one, two\n leading and trailing \nline one\\nline two\nliteral \\\\n text";
  textarea.dispatchEvent(
    /** @type {Event} */ (
      /** @type {unknown} */ (
        new browserWindow.Event("input", { bubbles: true })
      )
    ),
  );
  await settlePromises();
  assert.equal(harness.requests.length, 1, "editing drafts must not fetch");

  clickButton(target, '.filter-form button[type="submit"]');
  await settlePromises();
  assert.equal(harness.requests.length, 2);
  const expectedValues = [
    " leading and trailing ",
    "line one\nline two",
    "literal \\n text",
    "one, two",
  ];
  assert.deepEqual(
    new URL(harness.currentSearchUrl()).searchParams.getAll("test_cases"),
    expectedValues,
  );
  assert.deepEqual(
    new URL(harness.requests[1].path, "http://localhost/").searchParams.getAll(
      "test_cases",
    ),
    expectedValues,
  );

  harness.searchHistoryBack();
  await settlePromises();
  harness.searchHistoryForward();
  await settlePromises();
  const restoredInput = target.querySelector('[name="test_cases"]');
  assert.ok(restoredInput);
  assert.equal(
    /** @type {HTMLTextAreaElement} */ (/** @type {unknown} */ (restoredInput))
      .value,
    " leading and trailing \nline one\\nline two\nliteral \\\\n text\none, two",
  );

  await unmountFromDocument(component, target);
});

void test("page-size changes preserve applied common filters", async () => {
  assert.ok(harness);
  harness.resetApi();
  harness.resetSearchUrl(
    "http://localhost/test-results?page=2&page_size=25&families=deb&artefacts=kernel",
  );
  harness.setHandler((path) => {
    const params = new URL(path, "http://localhost/").searchParams;
    const limit = Number(params.get("limit"));
    const offset = Number(params.get("offset"));
    return Promise.resolve(
      makePage(makeRows(80, limit, offset), { limit, offset, count: 80 }),
    );
  });
  const { component, target } = mountInDocument();
  await settlePromises();
  assert.equal(harness.requests.length, 1);

  const pageSize = target.querySelector("#search-page-size");
  assert.ok(pageSize);
  assert.ok(browserWindow);
  const select = /** @type {HTMLSelectElement} */ (
    /** @type {unknown} */ (pageSize)
  );
  select.value = "100";
  select.dispatchEvent(
    /** @type {Event} */ (
      /** @type {unknown} */ (
        new browserWindow.Event("change", { bubbles: true })
      )
    ),
  );
  await settlePromises();

  const searchRequests = harness.requests.filter(({ path }) =>
    path.startsWith("test-results/search-page?"),
  );
  assert.equal(searchRequests.length, 2);
  const url = new URL(harness.currentSearchUrl());
  assert.equal(url.searchParams.get("page"), "1");
  assert.equal(url.searchParams.get("page_size"), "100");
  assert.deepEqual(url.searchParams.getAll("families"), ["deb"]);
  assert.deepEqual(url.searchParams.getAll("artefacts"), ["kernel"]);
  const request = new URL(searchRequests[1].path, "http://localhost/");
  assert.deepEqual(request.searchParams.getAll("families"), ["deb"]);
  assert.deepEqual(request.searchParams.getAll("artefacts"), ["kernel"]);
  assert.equal(request.searchParams.get("limit"), "100");
  assert.equal(request.searchParams.get("offset"), "0");

  await unmountFromDocument(component, target);
});

void test("advanced controls apply canonical filters, empty stage, and page-size preservation", async () => {
  assert.ok(harness);
  harness.resetApi();
  harness.resetSearchUrl("http://localhost/test-results?page=4&page_size=25");
  harness.setHandler((path) => {
    if (!path.startsWith("test-results/search-page?"))
      return Promise.resolve(null);
    const params = new URL(path, "http://localhost/").searchParams;
    return Promise.resolve(
      makePage([], {
        limit: Number(params.get("limit")),
        offset: Number(params.get("offset")),
        count: 100,
      }),
    );
  });
  const { component, target } = mountInDocument({
    artefactFamilies: null,
  });
  await settlePromises();
  assert.equal(
    harness.requests.filter(({ path }) =>
      path.startsWith("test-results/search-page?"),
    ).length,
    1,
  );

  openFilterDrawer(target);
  await settlePromises();
  assert.ok(browserWindow);
  const stage = target.querySelector('[name="artefact_stages"][value=""]');
  assert.ok(stage);
  const stageInput = /** @type {HTMLInputElement} */ (
    /** @type {unknown} */ (stage)
  );
  stageInput.checked = true;
  dispatchBrowserEvent(stageInput, "change");
  await settlePromises();
  const stageEntry = target.querySelector("#filter-stage-entry");
  assert.ok(
    stageEntry,
    "exact stage entry remains available without family configuration",
  );
  /** @type {HTMLInputElement} */ (/** @type {unknown} */ (stageEntry)).value =
    "custom-stage";
  dispatchBrowserEvent(stageEntry, "input");
  await settlePromises();
  clickButton(target, '.advanced-control button[type="button"]');

  const archived = target.querySelector('[name="artefact_is_archived"]');
  assert.ok(archived);
  const archivedSelect = /** @type {HTMLSelectElement} */ (
    /** @type {unknown} */ (archived)
  );
  archivedSelect.value = "false";
  dispatchBrowserEvent(archivedSelect, "change");

  const executionStatus = target.querySelector(
    '[name="test_execution_statuses"][value="PASSED"]',
  );
  assert.ok(executionStatus);
  const statusInput = /** @type {HTMLInputElement} */ (
    /** @type {unknown} */ (executionStatus)
  );
  statusInput.checked = true;
  dispatchBrowserEvent(statusInput, "change");

  for (const [name, value] of [
    ["rerun_is_requested", "true"],
    ["execution_is_latest", "false"],
  ]) {
    const select = target.querySelector(`[name="${name}"]`);
    assert.ok(select);
    const input = /** @type {HTMLSelectElement} */ (
      /** @type {unknown} */ (select)
    );
    input.value = value;
    dispatchBrowserEvent(input, "change");
  }

  const template = target.querySelector('[name="template_ids"]');
  assert.ok(template);
  const templateInput = /** @type {HTMLTextAreaElement} */ (
    /** @type {unknown} */ (template)
  );
  templateInput.value = "template-42";
  dispatchBrowserEvent(templateInput, "input");

  const issueAny = target.querySelector('[name="issues-mode"][value="any"]');
  assert.ok(issueAny);
  /** @type {HTMLInputElement} */ (/** @type {unknown} */ (issueAny)).click();
  const reviewerInput = target.querySelector(
    '[data-suggestion-field="reviewer_ids"] input',
  );
  assert.ok(reviewerInput);
  /** @type {HTMLInputElement} */ (
    /** @type {unknown} */ (reviewerInput)
  ).value = "42";
  dispatchBrowserEvent(reviewerInput, "input");
  await settlePromises();
  clickButton(target, '[data-suggestion-field="reviewer_ids"] button');

  for (const [name, value] of [
    ["metadata-category", "os"],
    ["metadata-value", "Ubuntu"],
  ]) {
    const input = target.querySelector(`[name="${name}"]`);
    assert.ok(input);
    /** @type {HTMLInputElement} */ (/** @type {unknown} */ (input)).value =
      value;
    dispatchBrowserEvent(input, "input");
  }
  await settlePromises();
  clickButton(target, '.metadata-control button[type="button"]');
  clickButton(target, '.filter-form button[type="submit"]');
  await settlePromises();

  const searchRequests = harness.requests.filter(({ path }) =>
    path.startsWith("test-results/search-page?"),
  );
  assert.equal(searchRequests.length, 2);
  const url = new URL(harness.currentSearchUrl());
  assert.equal(url.searchParams.get("page"), "1");
  assert.equal(url.searchParams.get("page_size"), "25");
  assert.deepEqual(url.searchParams.getAll("artefact_stages"), [
    "",
    "custom-stage",
  ]);
  assert.equal(url.searchParams.get("artefact_is_archived"), "false");
  assert.deepEqual(url.searchParams.getAll("test_execution_statuses"), [
    "PASSED",
  ]);
  assert.equal(url.searchParams.get("rerun_is_requested"), "true");
  assert.equal(url.searchParams.get("execution_is_latest"), "false");
  assert.deepEqual(url.searchParams.getAll("template_ids"), ["template-42"]);
  assert.deepEqual(url.searchParams.getAll("issues"), ["any"]);
  assert.deepEqual(url.searchParams.getAll("reviewer_ids"), ["42"]);
  const metadata = url.searchParams.get("execution_metadata");
  assert.equal(
    metadata,
    `${harness.encodeMetadataPart("os")}:${harness.encodeMetadataPart("Ubuntu")}`,
  );
  const request = new URL(searchRequests[1].path, "http://localhost/");
  assert.deepEqual(request.searchParams.getAll("artefact_stages"), [
    "",
    "custom-stage",
  ]);
  assert.equal(request.searchParams.get("artefact_is_archived"), "false");
  assert.equal(request.searchParams.get("reviewer_ids"), "42");
  assert.equal(target.querySelector('[role="alert"]'), null);
  await unmountFromDocument(component, target);
});

void test("failed suggestions do not prevent exact filter editing and applying", async () => {
  assert.ok(harness);
  harness.resetApi();
  harness.resetSearchUrl();
  harness.setHandler((path) => {
    if (path.startsWith("test-results/search-page?")) {
      return Promise.resolve(makePage([], { count: 0 }));
    }
    return Promise.reject(new Error("suggestion service unavailable"));
  });
  const { component, target } = mountInDocument();
  await settlePromises();

  openFilterDrawer(target);
  await settlePromises();
  assert.ok(browserWindow);
  const suggestionInput = target.querySelector(
    '[data-suggestion-field="artefacts"] input',
  );
  assert.ok(suggestionInput);
  const query = /** @type {HTMLInputElement} */ (
    /** @type {unknown} */ (suggestionInput)
  );
  query.value = "kernels";
  dispatchBrowserEvent(query, "input");
  await new Promise((resolve) => setTimeout(resolve, 300));
  await settlePromises();
  assert.match(target.textContent, /Suggestions unavailable/);

  const exact = target.querySelector('[name="artefacts"]');
  assert.ok(exact);
  const textarea = /** @type {HTMLTextAreaElement} */ (
    /** @type {unknown} */ (exact)
  );
  textarea.value = "exact artefact name";
  dispatchBrowserEvent(textarea, "input");
  clickButton(target, '.filter-form button[type="submit"]');
  await settlePromises();

  assert.deepEqual(
    new URL(harness.currentSearchUrl()).searchParams.getAll("artefacts"),
    ["exact artefact name"],
  );
  const searchRequest = harness.requests
    .filter(({ path }) => path.startsWith("test-results/search-page?"))
    .at(-1);
  assert.ok(searchRequest);
  assert.deepEqual(
    new URL(searchRequest.path, "http://localhost/").searchParams.getAll(
      "artefacts",
    ),
    ["exact artefact name"],
  );
  await unmountFromDocument(component, target);
});

void test("editing another field preserves malformed advanced URL conditions until Clear all", async () => {
  assert.ok(harness);
  harness.resetApi();
  harness.resetSearchUrl(
    "http://localhost/test-results?page=3&page_size=25&issues=any&issues=1&artefacts=old",
  );
  harness.setHandler(() => Promise.resolve(makePage([], { count: 0 })));
  const { component, target } = mountInDocument();
  await settlePromises();
  const requests = harness.requests;
  const searchRequests = () =>
    requests.filter(({ path }) => path.startsWith("test-results/search-page?"));
  assert.equal(searchRequests().length, 0);
  assert.match(target.textContent, /any\/none must be the sole value/);

  openFilterDrawer(target);
  await settlePromises();
  assert.match(
    target.querySelector("dialog [role=alert]")?.textContent ?? "",
    /any\/none must be the sole value/,
  );
  const otherFilter = target.querySelector('[name="test_plans"]');
  assert.ok(otherFilter);
  assert.ok(browserWindow);
  const field = /** @type {HTMLTextAreaElement} */ (
    /** @type {unknown} */ (otherFilter)
  );
  field.value = "new plan";
  dispatchBrowserEvent(field, "input");
  clickButton(target, '.filter-form button[type="submit"]');
  await settlePromises();
  assert.equal(
    searchRequests().length,
    0,
    "an unrelated edit must not erase the invalid issue condition",
  );
  assert.match(harness.currentSearchUrl(), /issues=any&issues=1/);

  clickButton(target, ".clear-all-button");
  await settlePromises();
  clickButton(target, '.filter-form button[type="submit"]');
  await settlePromises();
  assert.equal(
    searchRequests().length,
    1,
    JSON.stringify(searchRequests().map(({ path }) => path)),
  );
  const cleared = new URL(harness.currentSearchUrl());
  assert.equal(cleared.searchParams.has("issues"), false);
  assert.equal(cleared.searchParams.has("artefacts"), false);
  assert.deepEqual(cleared.searchParams.getAll("test_plans"), []);
  assert.equal(cleared.searchParams.get("page_size"), "25");
  await unmountFromDocument(component, target);
});
