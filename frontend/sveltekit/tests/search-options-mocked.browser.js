// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

// Opt-in real-Chromium comparison of Search Options 1–4 and 2.5 using synthetic API
// responses. Playwright is supplied externally; no credentials or live API are
// used. All non-loopback HTTP requests are blocked.
/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-return, @typescript-eslint/no-unsafe-argument */

import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { createServer } from "vite";

process.env.BASE_PATH ??= "/custom/base";
const basePath = process.env.BASE_PATH;
assert.ok(
  basePath.startsWith("/") && !basePath.endsWith("/"),
  "BASE_PATH must start with / and must not end with /",
);

const { chromium } = await import(
  process.env.PLAYWRIGHT_MODULE ?? "playwright-core"
);
const root = fileURLToPath(new URL("..", import.meta.url));
const artifacts = resolve(
  process.env.QA_ARTIFACT_DIR ?? "/tmp/opencode/search-options-mocked",
);
const reportPath = resolve(artifacts, "report.json");
const apiOrigin = "http://localhost:30000";
const searchPath = "/v1/test-results/search-page";
const detailPath = `${searchPath}/`;
const filterKeys = [
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
const filters = new URLSearchParams([
  ["families", "snap"],
  ["test_result_statuses", "PASSED"],
  ["test_execution_statuses", "PASSED"],
  ["artefacts", "widget"],
  ["artefact_versions", "1.2"],
  ["artefact_tracks", "stable"],
  ["environments", "vm"],
  ["test_plans", "smoke"],
  ["test_cases", "install"],
  ["artefact_stages", "beta"],
  ["artefact_is_archived", "false"],
  ["rerun_is_requested", "true"],
  ["execution_is_latest", "false"],
  ["issues", "42"],
  ["reviewer_ids", "43"],
  ["execution_metadata", "Y2F0ZWdvcnk=:dmFsdWU="],
  ["from_date", "2026-01-02T03:04:05Z"],
  ["until_date", "2026-01-03T03:04:05Z"],
  ["template_ids", "template-9"],
]);
const expectedFilters = Object.fromEntries(
  filterKeys.map((key) => [key, filters.getAll(key)]),
);
let activeExpectedFilters = expectedFilters;

// The same deliberately unchanged response is returned for every exact query.
// Rows are descending by ID (the server order) and intentionally contradict
// test_result_statuses=PASSED to catch local filtering in every prototype.
const rows = Array.from({ length: 300 }, (_, index) => {
  const id = 12000 - index;
  const createdAt = new Date(
    Date.UTC(2026, 9, 28, 12, 59 - index),
  ).toISOString();
  return {
    test_result: {
      id,
      name: `synthetic-case-${String(index).padStart(3, "0")}`,
      category: "synthetic-category",
      created_at: createdAt,
      template_id: "template-9",
      status: "FAILED",
      issues: [{ id: 42, key: "QA-42", title: "Synthetic issue" }],
    },
    test_execution: {
      id: id + 10000,
      status: "PASSED",
      environment: { name: "vm" },
      test_plan: "smoke",
      rerun_is_requested: true,
      execution_is_latest: false,
      execution_metadata: [{ category: "category", value: "value" }],
    },
    artefact: {
      id: id + 20000,
      name: "widget",
      version: "1.2",
      track: "stable",
      family: "snap",
      stage: "beta",
      archived: false,
      reviewers: [
        { id: 43, name: "Synthetic reviewer", launchpad_handle: "qa" },
      ],
    },
    artefact_build: { architecture: "amd64" },
  };
});

const detailsFor = (id) => {
  const row = rows.find((item) => item.test_result.id === id);
  assert.ok(row, `fixture row ${id} exists`);
  return {
    test_result: {
      id,
      name: row.test_result.name,
      category: row.test_result.category,
      template_id: row.test_result.template_id,
      status: row.test_result.status,
      io_log: "Synthetic Details fixture.",
      issues: [],
    },
    test_execution: {
      id: row.test_execution.id,
      status: row.test_execution.status,
      environment: row.test_execution.environment,
      test_plan: row.test_execution.test_plan,
      created_at: row.test_result.created_at,
      execution_metadata: { category: ["value"] },
    },
    artefact: {
      id: row.artefact.id,
      name: row.artefact.name,
      version: row.artefact.version,
      track: row.artefact.track,
      family: row.artefact.family,
    },
    artefact_build: row.artefact_build,
  };
};

const requests = [];
const unmockedApiRequests = [];
const pageErrors = [];
const routeResults = [];
let activeRoute = "not-started";
const server = await createServer({
  configFile: resolve(root, "vite.config.ts"),
  root,
  cacheDir: resolve(artifacts, "vite-cache"),
  server: { host: "127.0.0.1", port: 0, strictPort: false },
});
let browser;
let passed = false;
let failureMessage = null;

await mkdir(artifacts, { recursive: true });

function searchRequests(option) {
  return requests.filter(
    (request) =>
      request.route === option &&
      request.method === "GET" &&
      request.pathname === searchPath,
  );
}

function detailGetRequests(option, requestLog = requests) {
  return requestLog.filter(
    (request) =>
      request.route === option &&
      request.method === "GET" &&
      request.pathname.startsWith(detailPath),
  );
}

function assertCanonicalFilters(request, expected = expectedFilters) {
  const params = new URLSearchParams(request.search);
  for (const key of filterKeys)
    assert.deepEqual(
      params.getAll(key),
      expected[key],
      `Option ${request.option} sends canonical filter ${key}`,
    );
  assert.deepEqual(
    [...new Set(params.keys())]
      .filter((key) => filterKeys.includes(key))
      .sort(),
    filterKeys.filter((key) => expected[key].length > 0).sort(),
    `Option ${request.option} sends only active canonical filter keys`,
  );
  assert.equal(params.has("page"), false, "page is presentation-only");
  assert.equal(
    params.has("page_size"),
    false,
    "page_size is presentation-only",
  );
}

async function waitForNode(check, description, timeoutMs = 12000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (check()) return;
    await new Promise((resolve) => setTimeout(resolve, 25));
  }
  assert.fail(`Timed out waiting for ${description}.`);
}

async function waitForSearchRequestCount(option, count, description) {
  await waitForNode(() => searchRequests(option).length >= count, description);
  return searchRequests(option).at(-1);
}

function assertPageRequest(
  request,
  offset,
  limit,
  expected = activeExpectedFilters,
) {
  assert.ok(request, "a page request was recorded");
  const params = new URLSearchParams(request.search);
  assert.equal(params.get("offset"), String(offset));
  assert.equal(params.get("limit"), String(limit));
  assert.equal(params.get("include_count"), "true");
  assertCanonicalFilters(request, expected);
}

function assertUrlFilters(page, expected) {
  const params = new URL(page.url()).searchParams;
  for (const key of filterKeys)
    assert.deepEqual(
      params.getAll(key),
      expected[key],
      `URL retains exact filter ${key}`,
    );
}

async function assertPagerPages(page, expectedPages, expectedGaps) {
  assert.deepEqual(
    await page
      .locator(".pager-pages button")
      .evaluateAll((buttons) =>
        buttons.map((button) => button.getAttribute("aria-label")),
      ),
    expectedPages.map((number) => `Page ${number}`),
  );
  assert.equal(await page.locator(".pager-gap").count(), expectedGaps);
}

async function assertPagerNavigation(page, option) {
  const initialUrl = new URL(page.url());
  assert.equal(initialUrl.searchParams.get("page_size"), "25");
  assert.equal(
    await page.locator(".pager .range").innerText(),
    "Showing 51–75 of 300 results",
  );
  await assertPagerPages(page, [1, 2, 3, 4, 12], 1);

  async function jump(value, expectedPage, offset, pageSize, pages, gaps) {
    const before = searchRequests(option).length;
    const responsePromise = page.waitForResponse((response) => {
      const url = new URL(response.url());
      return (
        response.request().method() === "GET" &&
        url.pathname === searchPath &&
        url.searchParams.get("offset") === String(offset) &&
        url.searchParams.get("limit") === String(pageSize)
      );
    });
    await page.locator("#search-options-page-jump").fill(String(value));
    await page.getByRole("button", { name: "Go", exact: true }).click();
    assert.equal((await responsePromise).status(), 200);
    await page.waitForURL(
      (url) =>
        url.pathname === initialUrl.pathname &&
        url.searchParams.get("page") === String(expectedPage) &&
        url.searchParams.get("page_size") === String(pageSize),
    );
    const request = await waitForSearchRequestCount(
      option,
      before + 1,
      `Option ${option} page ${expectedPage} API request`,
    );
    assertPageRequest(request, offset, pageSize);
    assertUrlFilters(page, activeExpectedFilters);
    assert.equal(
      await page.locator(".pager .range").innerText(),
      `Showing ${Number(offset) + 1}–${Math.min(Number(offset) + Number(pageSize), 300)} of 300 results`,
    );
    await assertPagerPages(page, pages, gaps);
  }

  await jump(6, 6, 125, 25, [1, 5, 6, 7, 12], 2);
  await jump(999, 12, 275, 25, [1, 11, 12], 1);
  await jump(0, 1, 0, 25, [1, 2, 12], 1);

  const beforeSizeChange = searchRequests(option).length;
  const sizeResponse = page.waitForResponse((response) => {
    const url = new URL(response.url());
    return (
      response.request().method() === "GET" &&
      url.pathname === searchPath &&
      url.searchParams.get("offset") === "0" &&
      url.searchParams.get("limit") === "50"
    );
  });
  await page.locator(".pager select").selectOption("50");
  assert.equal((await sizeResponse).status(), 200);
  await page.waitForURL(
    (url) =>
      url.searchParams.get("page") === "1" &&
      url.searchParams.get("page_size") === "50",
  );
  const sizeRequest = await waitForSearchRequestCount(
    option,
    beforeSizeChange + 1,
    `Option ${option} page-size API request`,
  );
  assertPageRequest(sizeRequest, 0, 50);
  assertUrlFilters(page, activeExpectedFilters);

  await jump(3, 3, 100, 50, [1, 2, 3, 4, 5, 6], 0);
  return {
    initialWindow: [1, 2, 3, 4, "gap", 12],
    centeredWindow: [1, "gap", 5, 6, 7, "gap", 12],
    edgeWindows: {
      last: [1, "gap", 11, 12],
      first: [1, 2, "gap", 12],
    },
    jumpClampedToFirstAndLast: true,
    pageSizeChangePreservedFilters: true,
    finalPage: 3,
    finalPageSize: 50,
  };
}

async function openCreatedEditor(page, option, field = "from_date") {
  if (option === 1 || option === 2 || option === 2.5) {
    const trigger = page.getByRole("button", {
      name: "Filter Created",
      exact: true,
    });
    if ((await trigger.getAttribute("aria-expanded")) !== "true")
      await trigger.click();
    const editor = page.locator('[data-search-grid-menu="from_date"]');
    await editor.waitFor({ state: "visible" });
    return editor;
  }
  if (option === 3) {
    const trigger = page.locator(
      'button[aria-controls="search-option-3-filter-panel"]',
    );
    if ((await trigger.getAttribute("aria-expanded")) !== "true")
      await trigger.click();
    const editor = page.locator(
      '#search-option-3-filter-panel [data-search-grid-menu="from_date"]',
    );
    await editor.waitFor({ state: "visible" });
    return editor;
  }

  const bound = field === "from_date" ? "From" : "Until";
  await page.locator(`button[aria-label^="Edit Created — ${bound}:"]`).click();
  const editor = page.locator(`form[aria-label="Edit Created — ${bound}"]`);
  await editor.waitFor({ state: "visible" });
  return editor;
}

async function submitSearch(page, option) {
  if (option === 4) {
    const save = page.getByRole("button", {
      name: "Save changes",
      exact: true,
    });
    if (await save.isVisible()) await save.click();
  }
  if (option === 3)
    await page
      .locator("#search-option-3-filter-panel")
      .getByRole("button", { name: "Search", exact: true })
      .click();
  else await page.getByRole("button", { name: "Search", exact: true }).click();
}

async function applyDateChange(
  page,
  option,
  nextFilters,
  expectedFrom,
  expectedUntil,
) {
  const before = searchRequests(option).length;
  await submitSearch(page, option);
  const request = await waitForSearchRequestCount(
    option,
    before + 1,
    `Option ${option} corrected Created filter request`,
  );
  activeExpectedFilters = nextFilters;
  assertPageRequest(request, 0, 50, nextFilters);
  assertUrlFilters(page, nextFilters);
  const params = new URLSearchParams(request.search);
  assert.equal(params.get("from_date"), expectedFrom);
  assert.equal(params.get("until_date"), expectedUntil);
  if (option !== 1) {
    const url = new URL(page.url());
    assert.equal(url.searchParams.get("page"), "1");
    assert.equal(url.searchParams.get("page_size"), "50");
  }
  return request;
}

async function closeCreatedEditor(page, option, editor) {
  if (option === 4) {
    await editor.getByRole("button", { name: "Cancel", exact: true }).click();
  } else if (option === 3) {
    await page.getByRole("button", { name: "Close filters" }).click();
  } else {
    await page.keyboard.press("Escape");
  }
  await editor.waitFor({ state: "hidden" });
}

async function assertCreatedDateEditing(page, option) {
  const initialFrom = "2026-01-02T03:04:05Z";
  const initialUntil = "2026-01-03T03:04:05Z";
  const minutePickerFrom = "2026-01-02T04:05:00Z";
  const pickerSelector =
    option === 4
      ? 'input[type="datetime-local"][name="from_date-picker"]'
      : 'input[type="datetime-local"][data-search-grid-filter-picker="from_date"]';

  let editor = await openCreatedEditor(page, option);
  const picker = editor.locator(pickerSelector);
  assert.equal(await picker.inputValue(), "2026-01-02T03:04:05");
  assert.equal(await editor.locator('input[type="text"]').count(), 0);
  if (option === 4) {
    assert.equal(
      await editor.locator("h2").innerText(),
      "Created — From (UTC)",
    );
    const chipLabel = await page
      .locator('button[aria-label^="Edit Created — From:"]')
      .getAttribute("aria-label");
    assert.doesNotMatch(chipLabel ?? "", /\(UTC\)/);
  } else {
    assert.deepEqual(await editor.locator("h3.bound-label").allTextContents(), [
      "Created — From (UTC)",
      "Created — To (UTC)",
    ]);
    assert.equal(
      await editor.locator('input[type="datetime-local"]').count(),
      2,
    );
  }
  assert.equal(await picker.inputValue(), "2026-01-02T03:04:05");
  let next = { ...activeExpectedFilters, from_date: [minutePickerFrom] };
  await picker.fill("2026-01-02T04:05");
  await applyDateChange(page, option, next, minutePickerFrom, initialUntil);

  // Restore an accepted legacy offset/fraction query. The controls must remain
  // blank, and closing them must not rewrite either raw value or issue a request.
  const rawFrom = "2026-01-02T04:04:05.123456+01:00";
  const rawUntil = "2026-01-03T03:04:05.000000-04:00";
  const legacyUrl = new URL(page.url());
  legacyUrl.searchParams.set("from_date", rawFrom);
  legacyUrl.searchParams.set("until_date", rawUntil);
  const legacyExpected = {
    ...activeExpectedFilters,
    from_date: [rawFrom],
    until_date: [rawUntil],
  };
  const beforeLegacy = searchRequests(option).length;
  await page.goto(legacyUrl.href, { waitUntil: "domcontentloaded" });
  await page.locator("tbody [data-test-result-id]").first().waitFor();
  const legacyRequest = await waitForSearchRequestCount(
    option,
    beforeLegacy + 1,
    `Option ${option} restored legacy date request`,
  );
  assertPageRequest(legacyRequest, 0, 50, legacyExpected);
  activeExpectedFilters = legacyExpected;
  assertUrlFilters(page, legacyExpected);

  editor = await openCreatedEditor(page, option);
  if (option === 4) {
    assert.equal(
      await editor.locator("h2").innerText(),
      "Created — From (UTC)",
    );
    assert.equal(await editor.locator(pickerSelector).inputValue(), "");
    assert.equal(await editor.locator("[data-utc-picker-note]").count(), 1);
    await closeCreatedEditor(page, option, editor);
    editor = await openCreatedEditor(page, option, "until_date");
    assert.equal(await editor.locator("h2").innerText(), "Created — To (UTC)");
    assert.equal(
      await editor.locator('input[type="datetime-local"]').inputValue(),
      "",
    );
    assert.equal(await editor.locator("[data-utc-picker-note]").count(), 1);
  } else {
    assert.deepEqual(
      await editor
        .locator('input[type="datetime-local"]')
        .evaluateAll((items) => items.map((item) => item.value)),
      ["", ""],
    );
    assert.equal(await editor.locator("[data-utc-picker-note]").count(), 2);
    assert.equal(await editor.locator('input[type="text"]').count(), 0);
  }
  const beforeClose = searchRequests(option).length;
  await closeCreatedEditor(page, option, editor);
  assert.equal(searchRequests(option).length, beforeClose);
  assertUrlFilters(page, legacyExpected);

  const unrelated = await editStatusAndApply(page, option);
  assert.equal(unrelated.from_date[0], rawFrom);
  assert.equal(unrelated.until_date[0], rawUntil);

  editor = await openCreatedEditor(page, option);
  await editor.locator(pickerSelector).fill("2026-01-02T05:06:07");
  const selectedFrom = "2026-01-02T05:06:07Z";
  next = { ...activeExpectedFilters, from_date: [selectedFrom] };
  await applyDateChange(page, option, next, selectedFrom, rawUntil);

  editor = await openCreatedEditor(page, option);
  await editor.locator(pickerSelector).fill("");
  next = { ...activeExpectedFilters, from_date: [] };
  await applyDateChange(page, option, next, null, rawUntil);

  // A reversed legacy range remains blocked until a picker explicitly corrects
  // one bound. The other raw bound and page size survive the correction.
  const reversedFrom = "2026-01-04T00:00:00Z";
  const reversedUntil = "2026-01-03T00:00:00Z";
  const reversedUrl = new URL(page.url());
  reversedUrl.searchParams.set("from_date", reversedFrom);
  reversedUrl.searchParams.set("until_date", reversedUntil);
  const beforeReversed = searchRequests(option).length;
  await page.goto(reversedUrl.href, { waitUntil: "domcontentloaded" });
  await page
    .getByRole("alert")
    .filter({ hasText: "Invalid date range" })
    .waitFor({ state: "visible" });
  assert.equal(searchRequests(option).length, beforeReversed);
  const correctedFrom = "2026-01-02T23:59:59Z";
  editor = await openCreatedEditor(page, option);
  await editor.locator(pickerSelector).fill("2026-01-02T23:59:59");
  next = {
    ...activeExpectedFilters,
    from_date: [correctedFrom],
    until_date: [reversedUntil],
  };
  await applyDateChange(page, option, next, correctedFrom, reversedUntil);

  return {
    datetimeLocalOnly: true,
    restoredZuluWholeSeconds: initialFrom,
    minutePrecisionSerializedAsUtcWholeSeconds: minutePickerFrom,
    legacyOffsetAndFractionShownBlankAndPreserved: [rawFrom, rawUntil],
    noOpCloseAndUnrelatedSearchPreserveRawValues: true,
    pickerEditReplacesOnlyFrom: selectedFrom,
    clearingFromPreservesUntil: rawUntil,
    reversedLegacyRangeBlockedAndCorrected: true,
    unrelatedFiltersAndPageSizePreserved: true,
  };
}

async function assertOutOfRangeAndEmptyResults(
  page,
  option,
  routePath,
  pageOrigin,
) {
  const directParams = new URLSearchParams(filters);
  directParams.set("page", "99");
  directParams.set("page_size", "25");
  const directUrl = `${pageOrigin}${routePath}?${directParams}`;
  const beforeDirect = searchRequests(option).length;
  const directResponse = page.waitForResponse((response) => {
    const url = new URL(response.url());
    return (
      response.request().method() === "GET" &&
      url.pathname === searchPath &&
      url.searchParams.get("offset") === "2450" &&
      url.searchParams.get("limit") === "25"
    );
  });
  await page.goto(directUrl, { waitUntil: "domcontentloaded" });
  assert.equal((await directResponse).status(), 200);
  assertPageRequest(searchRequests(option).at(-1), 2450, 25, expectedFilters);
  await page.waitForURL(
    (url) =>
      url.pathname === routePath &&
      url.searchParams.get("page") === "12" &&
      url.searchParams.get("page_size") === "25",
  );
  await page.locator("tbody [data-test-result-id]").first().waitFor();
  await waitForSearchRequestCount(
    option,
    beforeDirect + 2,
    `Option ${option} canonical last-page request`,
  );
  let request = searchRequests(option).at(-1);
  assertPageRequest(request, 275, 25, expectedFilters);
  assertUrlFilters(page, expectedFilters);
  assert.equal(
    await page.locator(".pager .range").innerText(),
    "Showing 276–300 of 300 results",
  );
  await assertPagerPages(page, [1, 11, 12], 1);

  const emptyParams = new URLSearchParams(filters);
  emptyParams.set("test_cases", "empty-result");
  emptyParams.set("page", "99");
  emptyParams.set("page_size", "25");
  const emptyExpected = Object.fromEntries(
    filterKeys.map((key) => [
      key,
      key === "test_cases" ? ["empty-result"] : expectedFilters[key],
    ]),
  );
  const beforeEmpty = searchRequests(option).length;
  const emptyResponse = page.waitForResponse((response) => {
    const url = new URL(response.url());
    return (
      response.request().method() === "GET" &&
      url.pathname === searchPath &&
      url.searchParams.get("test_cases") === "empty-result" &&
      url.searchParams.get("offset") === "2450"
    );
  });
  await page.goto(`${pageOrigin}${routePath}?${emptyParams}`, {
    waitUntil: "domcontentloaded",
  });
  assert.equal((await emptyResponse).status(), 200);
  assertPageRequest(searchRequests(option).at(-1), 2450, 25, emptyExpected);
  await page.waitForURL(
    (url) =>
      url.pathname === routePath &&
      url.searchParams.get("page") === "1" &&
      url.searchParams.get("page_size") === "25" &&
      url.searchParams.get("test_cases") === "empty-result",
  );
  await page.locator(".pager").waitFor({ state: "visible" });
  await waitForSearchRequestCount(
    option,
    beforeEmpty + 2,
    `Option ${option} canonical empty page request`,
  );
  request = searchRequests(option).at(-1);
  assertPageRequest(request, 0, 25, emptyExpected);
  assertUrlFilters(page, emptyExpected);
  assert.equal(
    await page.locator(".pager .range").innerText(),
    "Showing 0–0 of 0 results",
  );
  assert.equal(await page.locator(".pager-jump").count(), 0);
  assert.deepEqual(
    await page
      .locator(".pager select option")
      .evaluateAll((items) => items.map((item) => item.value)),
    ["25", "50", "100"],
  );
  return {
    outOfRangePageCanonicalizedToLast: 12,
    emptyOutOfRangePageCanonicalizedToOne: true,
    emptyCountRangeAndPageSizeVisible: true,
    emptyPageJumpOmitted: true,
  };
}

async function assertNavigation(page, option) {
  const routes = [1, 2, 2.5, 3, 4].map((number) => ({
    option: number,
    path:
      number === 1
        ? `${basePath}/test-results`
        : `${basePath}/test-results/option-${number === 2.5 ? "2-5" : number}`,
  }));
  const states = await Promise.all(
    routes.map(async ({ path }) => {
      const link = page.locator(`a[href="${path}"]`);
      assert.equal(await link.count(), 1, `sidebar has route link ${path}`);
      return {
        path,
        selected: await link.evaluate((anchor) => {
          let current = anchor;
          for (let depth = 0; current && depth < 6; depth += 1) {
            if (
              current.classList.contains("selected") ||
              current.getAttribute("aria-current") === "page" ||
              current.getAttribute("aria-selected") === "true"
            )
              return true;
            current = current.parentElement;
          }
          return false;
        }),
      };
    }),
  );
  const selected = states.filter((state) => state.selected);
  assert.deepEqual(
    selected.map((state) => state.path),
    [routes.find((route) => route.option === option)?.path],
    `only Search (Option ${option}) is selected in the sidebar`,
  );
  return states;
}

function visibleResultIds(page) {
  return page
    .locator("tbody [data-test-result-id]")
    .evaluateAll((buttons) =>
      buttons.map((button) =>
        Number(button.getAttribute("data-test-result-id")),
      ),
    );
}

async function assertPrototypeUi(page, option) {
  if (option === 1) {
    const columnIds = await page
      .locator("th[data-svgrid-header-col]")
      .evaluateAll((headers) =>
        headers.map((header) => header.getAttribute("data-svgrid-header-col")),
      );
    assert.deepEqual(columnIds, [
      "run",
      "details",
      "createdAt",
      "family",
      "artefact",
      "stage",
      "archived",
      "testCase",
      "category",
      "execution",
      "executionStatus",
      "rerunRequested",
      "latestExecution",
      "status",
      "track",
      "version",
      "architecture",
      "environment",
      "testPlan",
      "templateId",
      "issues",
      "reviewers",
      "executionMetadata",
    ]);
    assert.equal(columnIds.length, 23);
    assert.equal(
      await page.locator("button.column-filter-trigger").count(),
      18,
    );
    assert.equal(await page.locator(".pager").count(), 0);
    assert.equal(await page.locator(".sv-grid-container").count(), 1);
    assert.equal(await page.locator('button[aria-label*="Sort"]').count(), 0);
    return { table: "SvGrid", columns: columnIds.length, filterControls: 18 };
  }

  const table = page.locator("table.search-option-table");
  const headers =
    option === 2 || option === 2.5
      ? await table
          .locator("thead tr:first-child th")
          .evaluateAll((items) =>
            items.map(
              (header) =>
                header
                  .querySelector(".header-content > span")
                  ?.textContent?.trim() ?? header.textContent.trim(),
            ),
          )
      : await table.locator("thead th").allTextContents();
  if (option === 2 || option === 2.5) {
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
    assert.equal(headers.length, 23);
    assert.equal(
      await table.locator("thead button.column-filter-trigger").count(),
      18,
    );
    if (option === 2.5) {
      const filterRows = table.locator("thead tr");
      assert.equal(await filterRows.count(), 2);
      assert.equal(await filterRows.nth(1).locator("th").count(), 23);
      const filterIndexes = await filterRows
        .nth(1)
        .locator("th")
        .evaluateAll((cells) =>
          cells.flatMap((cell, index) =>
            cell.querySelector("button.column-filter-trigger") ? [index] : [],
          ),
        );
      assert.deepEqual(
        filterIndexes,
        [2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21, 22],
      );
    } else assert.equal(await table.locator("thead tr").count(), 1);
    assert.equal(await page.locator('button[aria-label*="Sort"]').count(), 0);
    return {
      table: "Pragma Table",
      columns: headers.length,
      filterControls: 18,
      filterPlacement:
        option === 2.5 ? "aligned dedicated second thead row" : "column header",
    };
  }

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
  assert.equal(headers.length, 10);
  assert.equal(await page.locator('button[aria-label*="Sort"]').count(), 0);
  if (option === 3) {
    assert.equal(
      await page
        .locator('button[aria-controls="search-option-3-filter-panel"]')
        .count(),
      1,
      "Option 3 exposes the SidePanel filter trigger",
    );
    return { table: "compact Pragma Table + SidePanel", columns: 10 };
  }

  assert.equal(
    await page
      .locator('[aria-label="Confirmed search filters"] .condition')
      .count(),
    19,
    "Option 4 shows the active historical-style filter chips",
  );
  assert.equal(
    await page.getByRole("button", { name: /Add filter/ }).count(),
    1,
  );
  return { table: "compact Pragma Table + editable filter chips", columns: 10 };
}

async function editStatusAndApply(page, option) {
  const pageSize =
    option === 1 ? null : new URL(page.url()).searchParams.get("page_size");
  if (option === 1 || option === 2 || option === 2.5) {
    await page
      .getByRole("button", { name: "Filter Result status", exact: true })
      .click();
    const menu = page.getByRole("dialog", {
      name: "Result status column filter",
    });
    await menu.waitFor({ state: "visible" });
    await menu.locator('input[value="PASSED"]').uncheck();
    await menu.locator('input[value="FAILED"]').check();
  } else if (option === 3) {
    await page
      .locator('button[aria-controls="search-option-3-filter-panel"]')
      .click();
    const panel = page.locator("#search-option-3-filter-panel");
    await panel.waitFor({ state: "visible" });
    await panel
      .locator(
        'input[data-search-grid-filter="test_result_statuses"][value="PASSED"]',
      )
      .uncheck();
    await panel
      .locator(
        'input[data-search-grid-filter="test_result_statuses"][value="FAILED"]',
      )
      .check();
  } else {
    await page.locator('button[aria-label^="Edit Result status:"]').click();
    const editor = page.locator(
      '.condition-popover[aria-label="Edit Result status"] form[aria-label="Edit Result status"]',
    );
    await editor.waitFor({ state: "visible" });
    await editor.locator('input[value="PASSED"]').uncheck();
    await editor.locator('input[value="FAILED"]').check();
    await editor
      .getByRole("button", { name: "Save changes", exact: true })
      .click();
  }

  const nextFilters = Object.fromEntries(
    filterKeys.map((key) => [
      key,
      key === "test_result_statuses" ? ["FAILED"] : activeExpectedFilters[key],
    ]),
  );
  const responsePromise = page.waitForResponse((response) => {
    const url = new URL(response.url());
    return (
      response.request().method() === "GET" &&
      url.pathname === searchPath &&
      url.searchParams.get("test_result_statuses") === "FAILED"
    );
  });
  if (option === 3) {
    await page
      .locator("#search-option-3-filter-panel")
      .getByRole("button", { name: "Search", exact: true })
      .click();
  } else {
    await page.getByRole("button", { name: "Search", exact: true }).click();
  }
  const response = await responsePromise;
  assert.equal(response.status(), 200);
  await page.waitForURL((url) => {
    if (url.searchParams.get("test_result_statuses") !== "FAILED") return false;
    return option === 1
      ? !url.searchParams.has("limit") && !url.searchParams.has("offset")
      : url.searchParams.get("page") === "1" &&
          url.searchParams.get("page_size") === pageSize;
  });
  await page.locator("tbody [data-test-result-id]").first().waitFor();
  assertUrlFilters(page, nextFilters);
  activeExpectedFilters = nextFilters;
  return nextFilters;
}

async function assertRunAndLazyDetails(page, option, requestLog) {
  const searchApiRequests = searchRequests(option);
  const detailRequestsBefore = detailGetRequests(option, requestLog).length;
  assert.equal(
    detailRequestsBefore,
    0,
    "Details GET is not sent while rendering rows",
  );

  const run = page.locator('tbody a[aria-label^="View Run for "]').first();
  await run.waitFor();
  const runUrl = new URL(await run.getAttribute("href"), page.url());
  const rowId = Number((await visibleResultIds(page))[0]);
  assert.equal(runUrl.pathname, `${basePath}/snaps/${rowId + 20000}`);
  assert.equal(
    runUrl.searchParams.get("testExecutionId"),
    String(rowId + 10000),
  );
  assert.equal(runUrl.searchParams.get("testResultId"), String(rowId));

  const details = page
    .locator('tbody button[aria-label^="View details for "]')
    .first();
  await details.click();
  await waitForNode(
    () =>
      detailGetRequests(option, requestLog).length === detailRequestsBefore + 1,
    `Option ${option} on-demand Details GET`,
  );
  const detailsGet = detailGetRequests(option, requestLog).at(-1);
  assert.ok(detailsGet);
  assert.equal(detailsGet.method, "GET");
  assert.equal(detailsGet.pathname, `${detailPath}${rowId}`);
  const dialog = page.locator("dialog.search-result-details[open]");
  await dialog.waitFor({ state: "visible" });
  assert.match(await dialog.innerText(), /Synthetic Details fixture/);
  await page.keyboard.press("Escape");
  await dialog.waitFor({ state: "hidden" });
  assert.equal(
    detailGetRequests(option, requestLog).length,
    detailRequestsBefore + 1,
    "closing Details does not issue another GET; CORS preflights are not counted",
  );
  assert.ok(searchApiRequests.length > 0);
  return { runHref: runUrl.href, detailsGetFetchedOnOpenOnly: true };
}

async function assertOptionTableScrolling(page, option) {
  const tableRegion = page.locator(".table-scroll");
  const pager = page.locator(".pager");
  const dimensions = await page.evaluate(() => {
    const region = document.querySelector(".table-scroll");
    const main = document.querySelector("main.main-content");
    if (!(region instanceof HTMLElement) || !(main instanceof HTMLElement))
      throw new Error("Search table region or main content is missing");
    return {
      viewportHeight: window.innerHeight,
      viewportWidth: window.innerWidth,
      documentHeight: document.documentElement.scrollHeight,
      documentWidth: document.documentElement.scrollWidth,
      documentScrollTop: document.scrollingElement?.scrollTop ?? 0,
      mainHeight: main.clientHeight,
      mainWidth: main.clientWidth,
      mainScrollHeight: main.scrollHeight,
      mainScrollWidth: main.scrollWidth,
      mainScrollTop: main.scrollTop,
      tableClientHeight: region.clientHeight,
      tableScrollHeight: region.scrollHeight,
      tableClientWidth: region.clientWidth,
      tableScrollWidth: region.scrollWidth,
    };
  });
  assert.ok(
    dimensions.tableScrollHeight > dimensions.tableClientHeight,
    `Option ${option} fixture overflows vertically in the table region`,
  );
  assert.ok(
    dimensions.tableScrollWidth > dimensions.tableClientWidth,
    `Option ${option} fixture overflows horizontally in the table region`,
  );
  assert.ok(
    Number(dimensions.documentHeight) <= Number(dimensions.viewportHeight) + 1,
    `Option ${option} does not require document scrolling`,
  );
  assert.ok(
    Number(dimensions.mainScrollHeight) <= Number(dimensions.mainHeight) + 1,
    `Option ${option} does not require main-content scrolling`,
  );
  assert.ok(
    Number(dimensions.documentWidth) <= Number(dimensions.viewportWidth) + 1,
    `Option ${option} does not require document horizontal scrolling`,
  );
  assert.ok(
    Number(dimensions.mainScrollWidth) <= Number(dimensions.mainWidth) + 1,
    `Option ${option} does not require main-content horizontal scrolling`,
  );
  assert.equal(dimensions.documentScrollTop, 0);
  assert.equal(dimensions.mainScrollTop, 0);

  const bounds = await tableRegion.boundingBox();
  assert.ok(bounds, `Option ${option} table region is visible`);
  await page.mouse.move(
    Number(bounds.x) + Number(bounds.width) / 2,
    Number(bounds.y) + Number(bounds.height) / 2,
  );
  await page.mouse.wheel(0, 480);
  await page.waitForFunction(
    () => document.querySelector(".table-scroll")?.scrollTop > 0,
  );
  const afterVerticalWheel = await page.evaluate(() => ({
    tableScrollTop: document.querySelector(".table-scroll")?.scrollTop ?? 0,
    documentScrollTop: document.scrollingElement?.scrollTop ?? 0,
    mainScrollTop: document.querySelector("main.main-content")?.scrollTop ?? 0,
  }));
  assert.ok(
    afterVerticalWheel.tableScrollTop > 0,
    `Option ${option} real vertical wheel input scrolls the table region`,
  );
  assert.equal(afterVerticalWheel.documentScrollTop, 0);
  assert.equal(afterVerticalWheel.mainScrollTop, 0);

  await page.mouse.wheel(480, 0);
  await page.waitForFunction(
    () => document.querySelector(".table-scroll")?.scrollLeft > 0,
  );
  const afterHorizontalWheel = await page.evaluate(() => ({
    tableScrollLeft: document.querySelector(".table-scroll")?.scrollLeft ?? 0,
    documentScrollTop: document.scrollingElement?.scrollTop ?? 0,
    mainScrollTop: document.querySelector("main.main-content")?.scrollTop ?? 0,
  }));
  assert.ok(
    afterHorizontalWheel.tableScrollLeft > 0,
    `Option ${option} real horizontal wheel input scrolls the table region`,
  );
  assert.equal(afterHorizontalWheel.documentScrollTop, 0);
  assert.equal(afterHorizontalWheel.mainScrollTop, 0);

  const pagerBounds = await pager.boundingBox();
  assert.ok(pagerBounds, `Option ${option} pager is visible`);
  assert.ok(
    Number(pagerBounds.y) >= 0 &&
      Number(pagerBounds.y) + Number(pagerBounds.height) <=
        Number(dimensions.viewportHeight),
    `Option ${option} pager remains within the viewport while table scrolls`,
  );
  return {
    verticalWheelScrollTop: afterVerticalWheel.tableScrollTop,
    horizontalWheelScrollLeft: afterHorizontalWheel.tableScrollLeft,
    documentScrollingRequired: false,
    mainScrollingRequired: false,
    horizontalPageScrollingRequired: false,
    pagerVisible: true,
  };
}

async function testOption(page, option, pageOrigin) {
  activeRoute = option;
  activeExpectedFilters = expectedFilters;
  const routePath =
    option === 1
      ? `${basePath}/test-results`
      : `${basePath}/test-results/option-${option === 2.5 ? "2-5" : option}`;
  const params = new URLSearchParams(filters);
  let scrolling = null;
  if (option === 1) {
    // These are legacy pagination URL fields; the original infinite Search
    // route removes them and continues to use SvGrid's own range requests.
    params.set("offset", "777");
    params.set("limit", "17");
  } else {
    params.set("page", "3");
    params.set("page_size", "25");
  }
  const routeUrl = `${pageOrigin}${routePath}?${params}`;
  await page.goto(routeUrl, { waitUntil: "domcontentloaded" });
  await page.locator("tbody [data-test-result-id]").first().waitFor();
  assert.equal(new URL(page.url()).pathname, routePath);
  const nav = await assertNavigation(page, option);
  const ui = await assertPrototypeUi(page, option);
  const firstSearch = searchRequests(option)[0];
  assert.ok(firstSearch, `Option ${option} made a mocked Search request`);
  assertCanonicalFilters(firstSearch);

  const initialParams = new URLSearchParams(firstSearch.search);
  const expectedFirstIndex = option === 1 ? 0 : 50;
  const initialRowIds = await visibleResultIds(page);
  assert.deepEqual(
    initialRowIds.slice(0, 3),
    [0, 1, 2].map((index) => rows[expectedFirstIndex + index].test_result.id),
    "initial rows retain the API response order without local sorting",
  );
  if (option === 1)
    assert.match(
      await page.locator('tbody td[data-col-id="status"]').first().innerText(),
      /FAILED/,
      "the server-returned row is not locally removed by the PASSED URL filter",
    );
  else
    assert.match(
      await page
        .locator("tbody tr")
        .first()
        .locator(
          option === 2 || option === 2.5
            ? "td:nth-child(14)"
            : "td:nth-child(5)",
        )
        .innerText(),
      /FAILED/,
      "the server-returned row is not locally removed by the PASSED URL filter",
    );

  if (option === 1) {
    assert.equal(initialParams.get("offset"), "0");
    assert.equal(initialParams.get("limit"), "50");
    assert.equal(initialParams.get("include_count"), "true");
    await page.waitForFunction(
      () =>
        !new URL(location.href).searchParams.has("offset") &&
        !new URL(location.href).searchParams.has("limit"),
    );
    assert.equal(new URL(page.url()).searchParams.has("offset"), false);
    assert.equal(new URL(page.url()).searchParams.has("limit"), false);
    const grid = page.locator(".sv-grid-container");
    await grid.evaluate((element) => {
      element.scrollTop = element.scrollHeight;
    });
    await waitForNode(
      () =>
        searchRequests(option).some(
          (request) =>
            Number(new URLSearchParams(request.search).get("offset")) > 0,
        ),
      "Option 1's next infinite server range",
    );
    const nextBlock = searchRequests(option).find(
      (request) =>
        Number(new URLSearchParams(request.search).get("offset")) > 0,
    );
    assert.ok(nextBlock);
    const nextRange = new URLSearchParams(nextBlock.search);
    assert.equal(nextRange.get("limit"), "50");
    assert.equal(nextRange.get("include_count"), "false");
    assertCanonicalFilters(nextBlock);
    await grid.evaluate((element) => {
      element.scrollTop = 0;
    });
  } else {
    assert.equal(initialParams.get("offset"), "50");
    assert.equal(initialParams.get("limit"), "25");
    assert.equal(initialParams.get("include_count"), "true");
    assert.equal(new URL(page.url()).searchParams.get("page"), "3");
    assert.equal(new URL(page.url()).searchParams.get("page_size"), "25");
    assert.deepEqual(
      await page
        .locator(".pager select option")
        .evaluateAll((items) => items.map((item) => item.value)),
      ["25", "50", "100"],
    );
    scrolling = await assertOptionTableScrolling(page, option);
  }

  const pager = option === 1 ? null : await assertPagerNavigation(page, option);
  const dates = await assertCreatedDateEditing(page, option);
  const updatedFilters = activeExpectedFilters;
  const appliedRequests = searchRequests(option);
  const appliedRequest = appliedRequests.at(-1);
  assert.ok(appliedRequest);
  assertCanonicalFilters(appliedRequest, updatedFilters);
  const appliedParams = new URLSearchParams(appliedRequest.search);
  assert.equal(appliedParams.get("offset"), "0");
  assert.equal(appliedParams.get("limit"), "50");
  if (option === 1) {
    assert.equal(appliedParams.get("include_count"), "true");
  } else {
    assert.equal(appliedParams.get("include_count"), "true");
    assert.equal(new URL(page.url()).searchParams.get("page"), "1");
    assert.equal(new URL(page.url()).searchParams.get("page_size"), "50");
  }
  const afterApplyIds = await visibleResultIds(page);
  assert.deepEqual(
    afterApplyIds.slice(0, 3),
    rows.slice(0, 3).map((row) => row.test_result.id),
    "the mocked unchanged response remains in its server order after Apply",
  );

  const actions = await assertRunAndLazyDetails(page, option, requests);
  const pagingEdges =
    option === 1
      ? null
      : await assertOutOfRangeAndEmptyResults(
          page,
          option,
          routePath,
          pageOrigin,
        );
  assert.equal(
    pageErrors.length,
    0,
    `Option ${option} has no uncaught page errors: ${pageErrors.join(" | ")}`,
  );
  return {
    option,
    route: routePath,
    sidebar: nav,
    presentation: ui,
    initialRange: {
      offset: initialParams.get("offset"),
      limit: initialParams.get("limit"),
      includeCount: initialParams.get("include_count"),
    },
    filterApply: {
      pageResetToOne: option !== 1,
      retainedPageSize: option === 1 ? null : "25",
      canonicalFilterKeys: filterKeys.length,
      serverResponseOrderRetained: true,
    },
    pager,
    dates,
    pagingEdges,
    scrolling,
    actions,
    pageErrors: [],
  };
}

try {
  await server.listen();
  const address = server.httpServer.address();
  assert.ok(address && typeof address !== "string");
  const appOrigin = `http://127.0.0.1:${address.port}`;
  browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox"],
    ...(process.env.CHROMIUM_EXECUTABLE
      ? { executablePath: process.env.CHROMIUM_EXECUTABLE }
      : {}),
  });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 1000 },
    timezoneId: "America/Los_Angeles",
  });
  await context.route("**/*", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (url.origin === appOrigin) {
      await route.continue();
      return;
    }
    if (url.origin !== apiOrigin) {
      await route.abort();
      return;
    }

    const cors = {
      "access-control-allow-origin": appOrigin,
      "access-control-allow-credentials": "true",
      "access-control-allow-methods": "GET, OPTIONS",
      "access-control-allow-headers": "content-type, x-csrf-token",
    };
    const record = {
      route: activeRoute,
      method: request.method(),
      pathname: url.pathname,
      search: url.search,
    };
    requests.push(record);
    if (request.method() === "OPTIONS") {
      await route.fulfill({ status: 204, headers: cors });
      return;
    }

    let body;
    if (url.pathname === "/v1/users/me") {
      body = null;
    } else if (url.pathname === searchPath) {
      const offset = Number(url.searchParams.get("offset") ?? 0);
      const limit = Number(url.searchParams.get("limit") ?? 50);
      const count =
        url.searchParams.get("test_cases") === "empty-result" ? 0 : rows.length;
      body = {
        count,
        offset,
        limit,
        rows: count === 0 ? [] : rows.slice(offset, offset + limit),
      };
    } else if (url.pathname.startsWith(detailPath)) {
      const id = Number(url.pathname.slice(detailPath.length));
      if (
        Number.isSafeInteger(id) &&
        rows.some((row) => row.test_result.id === id)
      )
        body = detailsFor(id);
    } else if (url.pathname === "/v1/issues/42") {
      body = {
        id: 42,
        source: "launchpad",
        project: "synthetic/qa",
        key: "QA-42",
        title: "Synthetic issue",
      };
    } else if (url.pathname === "/v1/users/43") {
      body = { id: 43, name: "Synthetic reviewer", launchpad_handle: "qa" };
    } else if (url.pathname === "/v1/execution-metadata") {
      body = { execution_metadata: { category: ["value"] } };
    }

    if (body === undefined) {
      unmockedApiRequests.push(record);
      await route.fulfill({
        status: 404,
        headers: cors,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Unmocked cross-option QA endpoint" }),
      });
      return;
    }
    await route.fulfill({
      status: 200,
      headers: cors,
      contentType: "application/json",
      body: JSON.stringify(body),
    });
  });

  const page = await context.newPage();
  page.setDefaultTimeout(20000);
  page.on("pageerror", (error) => pageErrors.push(String(error)));
  for (const option of [1, 2, 2.5, 3, 4])
    routeResults.push(await testOption(page, option, appOrigin));

  assert.deepEqual(
    unmockedApiRequests,
    [],
    "all API requests must have an explicit synthetic response",
  );
  assert.equal(
    pageErrors.length,
    0,
    `uncaught page errors: ${pageErrors.join(" | ")}`,
  );
  passed = true;
  process.stdout.write(
    `Mocked cross-option Search browser QA: PASS (${reportPath})\n`,
  );
} catch (error) {
  failureMessage = String(error);
  throw error;
} finally {
  if (browser) await browser.close();
  await server.close();
  await writeFile(
    reportPath,
    JSON.stringify(
      {
        passed,
        failure: failureMessage,
        basePath,
        fixture: {
          rows: rows.length,
          sourceOrder: "descending result ID",
          requestedResultStatus: "PASSED",
          returnedResultStatus: "FAILED",
          canonicalFilterKeys: filterKeys,
          noCredentialsOrLiveApi: true,
        },
        checks: routeResults,
        mockedApiRequests: requests,
        unmockedApiRequests,
        pageErrors,
        artifacts: {
          report: reportPath,
          viteCache: resolve(artifacts, "vite-cache"),
        },
        limitations: [
          "Every Test Observer API request is intercepted and receives a synthetic fixture response; this is not live API, authentication, or backend integration evidence.",
          "The synthetic Search endpoint deliberately returns the same rows regardless of filter values so local filtering or reordering is observable.",
          "UI equivalence is not expected: Option 1 is infinite SvGrid, Option 2 is the wide table with filters in column headers, Option 2.5 is the wide table with a dedicated second filter row, and Options 3–4 are distinct compact filter presentations.",
        ],
      },
      null,
      2,
    ),
  );
  if (!passed)
    process.stderr.write(
      `Mocked cross-option Search browser QA did not pass; report: ${reportPath}\n`,
    );
}
