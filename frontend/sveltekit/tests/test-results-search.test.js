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
const ORIGINAL_LIST_FILTERS = [
  "test_result_statuses",
  "artefacts",
  "artefact_versions",
  "artefact_tracks",
  "environments",
  "test_plans",
  "test_cases",
];

const families = [
  {
    name: "configured-route",
    api_name: "snap",
    stages: ["alpha", "shared"],
    columns: [],
    filters: [],
  },
  {
    name: "another-route",
    api_name: "another-api-family",
    stages: ["beta", "shared"],
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

/** @param {number} [id] */
function mountedIssueResults(id = 73) {
  const target = browser.document.createElement("div");
  browser.document.body.append(target);
  const handle = app.mountIssueResults(
    /** @type {HTMLElement} */ (/** @type {unknown} */ (target)),
    id,
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

void test("issue results pin an immutable single issue and fail closed for invalid IDs", () => {
  const query = app.issueResultsQuery(73);
  assert.deepEqual(query.filters.issues, [73]);
  assert.throws(() => {
    query.filters.issues = [80];
  }, TypeError);
  const pinned = query.filters.issues;
  assert.ok(Array.isArray(pinned));
  assert.throws(() => pinned.push(80), TypeError);
  for (const id of [0, -1, 1.5, NaN, Number.MAX_SAFE_INTEGER + 1])
    assert.ok(app.issueResultsQuery(id).problems.length);
});

void test("issue results bounded loader reaches beyond 100 and keeps total when count is null", async () => {
  /** @type {URL[]} */
  const requests = [];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    requests.push(request);
    const offset = Number(request.searchParams.get("offset"));
    const ids = Array.from(
      { length: Math.min(50, 625 - offset) },
      (_, n) => offset + n + 1,
    );
    return Promise.resolve(
      response(ids, offset === 0 ? 625 : null, 50, offset),
    );
  };
  const store = new app.TestResultsSearchStore();
  try {
    await store.search(app.issueResultsQuery(73), families, "/custom/base");
    const controller = store.controller;
    assert.ok(controller);
    for (let offset = 50; offset <= 600; offset += 50) {
      controller.setViewport(offset, offset + 24);
      await flush();
    }
    assert.equal(store.state.rowCount, 625);
    assert.equal(store.response.count, null);
    assert.ok(controller.getRows().some((row) => row.id === 625));
    assert.ok(
      controller.getCacheState().filter((block) => block.status === "loaded")
        .length <= app.SEARCH_MAX_BLOCKS,
    );
    assert.ok(
      requests.some((r) => Number(r.searchParams.get("offset")) >= 100),
    );
    for (const request of requests) {
      assert.deepEqual(request.searchParams.getAll("issues"), ["73"]);
      if (request.searchParams.get("offset") !== "0")
        assert.equal(request.searchParams.get("include_count"), "false");
    }
  } finally {
    store.cancel();
  }
});

void test("issue results use a separate read-only grid, configured Run route and lazy full Details", async () => {
  /** @type {URL[]} */
  const requests = [];
  const details = detailedResult(1);
  const log =
    '<script>alert("literal")</script>\n  indented 🧪\n' +
    "long-token".repeat(500);
  details.test_result.io_log = log;
  details.test_result.issues = [
    {
      issue: {
        id: 80,
        source: "github",
        project: "qa",
        key: "Q-80",
        title: "Attached issue",
        status: "open",
      },
    },
  ];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    requests.push(request);
    return Promise.resolve(
      request.pathname.endsWith("/1") ? detailsResponse(details) : response(),
    );
  };
  const ui = mountedIssueResults();
  try {
    await flush();
    assert.match(
      ui.target.textContent,
      /1 matching test results on the server/,
    );
    const headers = [...ui.target.querySelectorAll("thead tr th")].map((n) =>
      n.textContent.trim(),
    );
    assert.deepEqual(headers, [
      "Run",
      "Details",
      "Artefact",
      "Test case",
      "Category",
      "Execution ID",
      "Execution status",
      "Result status",
      "Track",
      "Version",
      "Architecture",
      "Environment",
      "Test plan",
    ]);
    assert.equal(
      ui.target.querySelectorAll(
        'input[type="checkbox"], [data-search-grid-menu]',
      ).length,
      0,
    );
    const run = ui.target.querySelector('a[aria-label="View Run for case 1"]');
    assert.equal(
      run?.getAttribute("href"),
      "/custom/base/configured-route/42?testExecutionId=7&testResultId=1",
    );
    assert.equal(requests.length, 1, "no eager Details requests");
    const trigger = detailsButton(ui.target, 1);
    trigger.click();
    await flush();
    const dialog = detailsDialog();
    assert.equal(dialog.getAttribute("open"), "");
    assert.equal(dialog.querySelector("pre")?.textContent, log);
    assert.equal(dialog.querySelector("script"), null);
    assert.match(dialog.textContent, /ζ Unicode 🐧/);
    assert.equal(
      dialog
        .querySelector('a[aria-label="View issue Q-80"]')
        ?.getAttribute("href"),
      "/custom/base/issues/80",
    );
    button(dialog, "Close").click();
    await flush();
    assert.equal(browser.document.activeElement, trigger);
    assert.equal(requests.length, 2, "closing does not fetch");
    trigger.click();
    await flush();
    // Simulate a virtualized cell reused for another row while Details is open.
    trigger.dataset.testResultId = "999";
    button(detailsDialog(), "Close").click();
    await flush();
    assert.equal(
      browser.document.activeElement,
      ui.target.querySelector(".issue-results-grid"),
    );
  } finally {
    await ui.destroy();
  }
});

void test("issue results ignore late parsed A bodies and close obsolete Details on navigation and session change", async () => {
  let releaseBody = () => undefined;
  const body = new Promise((resolve) => {
    releaseBody = resolve;
  });
  let holdDetails = false;
  const lateDetails = deferred();
  /** @type {URL[]} */
  const requests = [];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    requests.push(request);
    if (/search-page\/\d+$/.test(request.pathname))
      return holdDetails
        ? lateDetails.promise
        : Promise.resolve(detailsResponse(detailedResult(2)));
    if (request.searchParams.get("issues") === "73") {
      const held = response([1]);
      held.json = () => body;
      return Promise.resolve(held);
    }
    return Promise.resolve(response([2]));
  };
  const ui = mountedIssueResults();
  try {
    await flush();
    assert.match(ui.target.textContent, /Loading test results/);
    ui.handle.changeIssue(80);
    await flush();
    assert.ok(detailsButton(ui.target, 2));
    releaseBody({ count: 1, limit: 50, offset: 0, rows: [tableResult(1)] });
    await flush();
    assert.equal(
      ui.target.querySelector('button[data-test-result-id="1"]'),
      null,
    );
    detailsButton(ui.target, 2).click();
    await flush();
    assert.equal(detailsDialog().getAttribute("open"), "");
    // Relevant session changes invalidate both Details and result cache.
    app.userStore.current = null;
    globalThis.fetch = (input) => {
      const request = new URL(input instanceof Request ? input.url : input);
      requests.push(request);
      if (request.pathname === "/v1/users/me")
        return Promise.resolve(json({ id: 945, teams: [], is_admin: false }));
      return Promise.resolve(response([2]));
    };
    await app.userStore.refresh(globalThis.fetch);
    await flush();
    assert.equal(detailsDialog().getAttribute("open"), null);
    holdDetails = true;
    globalThis.fetch = (input) => {
      const request = new URL(input instanceof Request ? input.url : input);
      if (/search-page\/\d+$/.test(request.pathname))
        return lateDetails.promise;
      return Promise.resolve(response([2]));
    };
    detailsButton(ui.target, 2).click();
    await flush();
    ui.handle.changeIssue(81);
    await flush();
    lateDetails.resolve(detailsResponse(detailedResult(2)));
    await flush();
    assert.equal(detailsDialog().getAttribute("open"), null);
    for (const request of requests.filter((r) =>
      r.pathname.endsWith("search-page"),
    ))
      assert.equal(request.searchParams.getAll("issues").length, 1);
  } finally {
    await ui.destroy();
    app.userStore.current = null;
  }
});

void test("issue results cover empty, error/retry and authoritative 401/403/session-check states", async () => {
  for (const scenario of ["empty", "error", "login", "forbidden", "unknown"]) {
    app.userStore.current = null;
    const profile = { id: 946, teams: [], is_admin: false };
    if (scenario === "forbidden") {
      globalThis.fetch = () => Promise.resolve(json(profile));
      await app.userStore.refresh(globalThis.fetch);
    }
    let recover = false;
    globalThis.fetch = (input) => {
      const request = new URL(input instanceof Request ? input.url : input);
      if (request.pathname === "/v1/users/me")
        return Promise.resolve(
          scenario === "unknown"
            ? json({}, 503)
            : json(scenario === "forbidden" ? profile : null),
        );
      if (recover) return Promise.resolve(response([3]));
      if (scenario === "empty") return Promise.resolve(response([]));
      return Promise.resolve(
        json(
          {},
          scenario === "login"
            ? 401
            : scenario === "forbidden" || scenario === "unknown"
              ? 403
              : 503,
        ),
      );
    };
    const ui = mountedIssueResults();
    try {
      await flush();
      const expected = {
        empty: /No test results are attached/,
        error: /Could not load test results/,
        login: /need to be logged in/,
        forbidden: /don't have permission/,
        unknown: /couldn't verify your session/,
      }[scenario];
      assert.match(ui.target.textContent, expected);
      if (scenario === "empty") {
        assert.match(ui.target.textContent, /0 matching test results/);
      } else {
        if (scenario === "login")
          assert.ok(ui.target.querySelector('a[href*="auth/saml/login"]'));
        recover = true;
        button(ui.target, "Retry results").click();
        await flush();
        assert.ok(detailsButton(ui.target, 3));
      }
    } finally {
      await ui.destroy();
    }
  }
  app.userStore.current = null;
});

void test("issue results ignore late access failures, Details errors and unmounted range responses", async () => {
  const lateAccess = deferred();
  const lateDetails = deferred();
  let sessionStarted = false;
  let holdRange = false;
  const lateRange = deferred();
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    if (request.pathname === "/v1/users/me") {
      sessionStarted = true;
      return lateAccess.promise;
    }
    if (request.pathname.endsWith("/2")) return lateDetails.promise;
    if (request.searchParams.get("issues") === "73")
      return Promise.resolve(json({}, 403));
    return holdRange ? lateRange.promise : Promise.resolve(response([2]));
  };
  app.userStore.current = null;
  const ui = mountedIssueResults();
  try {
    await flush();
    assert.ok(sessionStarted);
    ui.handle.changeIssue(80);
    await flush();
    lateAccess.resolve(json(null, 401));
    await flush();
    assert.ok(detailsButton(ui.target, 2));
    assert.doesNotMatch(
      ui.target.textContent,
      /need to be logged in|permission/,
    );
    detailsButton(ui.target, 2).click();
    await flush();
    holdRange = true;
    ui.handle.changeIssue(81);
    await flush();
    lateDetails.resolve(json({ detail: "Late failure from issue A" }, 503));
    await flush();
    assert.equal(detailsDialog().getAttribute("open"), null);
    assert.doesNotMatch(
      ui.target.textContent,
      /Could not load result details|Late failure/,
    );
  } finally {
    await ui.destroy();
  }
  lateRange.resolve(response([999]));
  await flush();
  assert.equal(browser.document.querySelector(".issue-test-results"), null);
});

void test("issue results Details failures retry, missing-family routes stay unavailable, and unmount ignores pending bodies", async () => {
  let retry = false;
  const row = tableResult(1);
  row.artefact.family = "unconfigured";
  const details = detailedResult(1);
  details.artefact.family = "unconfigured";
  const held = deferred();
  let pending = false;
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    if (request.pathname.endsWith("/1"))
      return pending
        ? held.promise
        : Promise.resolve(retry ? detailsResponse(details) : json({}, 403));
    return Promise.resolve(
      json({ count: 1, limit: 50, offset: 0, rows: [row] }),
    );
  };
  const ui = mountedIssueResults();
  try {
    await flush();
    assert.match(ui.target.textContent, /Run unavailable/);
    detailsButton(ui.target, 1).click();
    await flush();
    assert.match(detailsDialog().textContent, /don't have permission/);
    retry = true;
    button(detailsDialog(), "Retry").click();
    await flush();
    assert.match(detailsDialog().textContent, /unconfigured/);
    assert.equal(
      detailsDialog().querySelector('a[href*="testExecutionId"]'),
      null,
    );
    button(detailsDialog(), "Close").click();
    await flush();
    pending = true;
    detailsButton(ui.target, 1).click();
    await flush();
    assert.match(detailsDialog().textContent, /Loading/);
  } finally {
    await ui.destroy();
  }
  held.resolve(detailsResponse(details));
  await flush();
  assert.equal(
    browser.document.querySelector("dialog.search-result-details[open]"),
    null,
  );
});

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

/**
 * @typedef {{
 *   test_result: { id: number; name: string; category: string; status: string; created_at: string; template_id: string; io_log?: string; issues: { issue: { id: number; source: string; project: string; key: string; title: string; status: string } }[] };
 *   artefact: { id: number; name: string; version: string; track: string; stage: string | null; archived: boolean; family: string; reviewers: { id: number; name: string; launchpad_handle?: string | null }[] };
 *   artefact_build: { id: number; architecture: string; revision: number | null };
 *   test_execution: { id: number; status: string; is_rerun_requested: boolean; rerun_is_requested: boolean; execution_is_latest: boolean; environment: { id: number; name: string; architecture: string }; test_plan: string; created_at?: string; execution_metadata: Record<string, string[]> };
 * }} SearchFixtureResult
 */

/** @returns {SearchFixtureResult} */
function result(id = 1) {
  return {
    test_result: {
      id,
      name: `case ${id}`,
      category: `category ${id}`,
      status: "FAILED",
      created_at: "2026-01-01T00:00:00Z",
      template_id: `template ${id}`,
      issues: [],
    },
    artefact: {
      id: 42,
      name: "example artefact",
      version: "1.2",
      track: "stable",
      stage: "alpha",
      archived: false,
      family: "snap",
      reviewers: [],
    },
    artefact_build: { id: 3, architecture: "amd64", revision: 1 },
    test_execution: {
      id: 7,
      status: "FAILED",
      is_rerun_requested: false,
      rerun_is_requested: false,
      execution_is_latest: true,
      environment: { id: 5, name: "test lab", architecture: "amd64" },
      test_plan: "smoke",
      execution_metadata: {},
    },
  };
}
/** @param {number} [id] @param {SearchFixtureResult} [source] */
function tableResult(id = 1, source = result(id)) {
  return {
    test_result: {
      id: source.test_result.id,
      name: source.test_result.name,
      category: source.test_result.category,
      created_at: source.test_result.created_at,
      template_id: source.test_result.template_id,
      status: source.test_result.status,
      issues: source.test_result.issues.map(({ issue }) => ({
        id: issue.id,
        key: issue.key,
        title: issue.title,
      })),
    },
    test_execution: {
      id: source.test_execution.id,
      status: source.test_execution.status,
      environment: { name: source.test_execution.environment.name },
      test_plan: source.test_execution.test_plan,
      rerun_is_requested: source.test_execution.rerun_is_requested,
      execution_is_latest: source.test_execution.execution_is_latest,
      execution_metadata: Object.entries(
        source.test_execution.execution_metadata,
      ).flatMap(([category, values]) =>
        values.map((value) => ({ category, value })),
      ),
    },
    artefact: {
      id: source.artefact.id,
      name: source.artefact.name,
      version: source.artefact.version,
      track: source.artefact.track,
      family: source.artefact.family,
      stage: source.artefact.stage,
      archived: source.artefact.archived,
      reviewers: source.artefact.reviewers.map((reviewer) => ({
        id: reviewer.id,
        name: reviewer.name,
        launchpad_handle: reviewer.launchpad_handle ?? null,
      })),
    },
    artefact_build: { architecture: source.artefact_build.architecture },
  };
}
const response = (ids = [1], count = ids.length, limit = 50, offset = 0) =>
  json({ count, limit, offset, rows: ids.map((id) => tableResult(id)) });

/** @returns {SearchFixtureResult} */
function detailedResult(id = 1) {
  const row = result(id);
  return {
    ...row,
    test_result: {
      ...row.test_result,
      category: `category ${id}`,
      template_id: `template ${id}`,
      io_log: "",
      issues: [],
    },
    test_execution: {
      ...row.test_execution,
      created_at: "2026-02-03T12:34:56+05:30",
      execution_metadata: { "ζ Unicode 🐧": ["二", "一"], Alpha: ["z", "a"] },
    },
  };
}

function detailsResponse(result = detailedResult()) {
  return json({
    test_result: {
      id: result.test_result.id,
      name: result.test_result.name,
      category: result.test_result.category,
      template_id: result.test_result.template_id,
      status: result.test_result.status,
      io_log: result.test_result.io_log ?? "",
      issues: result.test_result.issues.map(({ issue }) => ({
        issue: {
          id: issue.id,
          source: issue.source,
          project: issue.project,
          key: issue.key,
          title: issue.title,
          status: issue.status,
        },
      })),
    },
    test_execution: {
      id: result.test_execution.id,
      status: result.test_execution.status,
      environment: { name: result.test_execution.environment.name },
      test_plan: result.test_execution.test_plan,
      created_at: result.test_execution.created_at ?? "",
      execution_metadata: result.test_execution.execution_metadata,
    },
    artefact: {
      id: result.artefact.id,
      name: result.artefact.name,
      version: result.artefact.version,
      track: result.artefact.track,
      family: result.artefact.family,
    },
    artefact_build: { architecture: result.artefact_build.architecture },
  });
}

/** @param {import('happy-dom').HTMLElement} target @param {number} id */
function detailsButton(target, id) {
  const found = target.querySelector(
    `button[aria-label="View details for case ${id}"]`,
  );
  assert.ok(found);
  return /** @type {import('happy-dom').HTMLButtonElement} */ (found);
}

function detailsDialog() {
  const dialog = browser.document.querySelector("dialog.search-result-details");
  assert.ok(dialog);
  return dialog;
}

function gridValueDialog() {
  const dialog = browser.document.querySelector(
    "dialog.search-grid-value-dialog",
  );
  assert.ok(dialog);
  return dialog;
}

void test("unfiltered read-only grid loads recent results with Run and Details", async () => {
  /** @type {URL[]} */
  const requests = [];
  const newest = detailedResult(20);
  newest.test_result.created_at = "2026-01-02T00:34:05.987654+01:00";
  const rows = [newest, detailedResult(3), detailedResult(11)];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    requests.push(request);
    if (request.pathname === "/v1/test-results/search-page")
      return Promise.resolve(
        json({
          count: 3,
          limit: 50,
          offset: 0,
          rows: rows.map((row) => tableResult(row.test_result.id, row)),
        }),
      );
    const id = Number(request.pathname.split("/").at(-1));
    return Promise.resolve(
      detailsResponse(rows.find((row) => row.test_result.id === id)),
    );
  };
  const ui = mounted();
  try {
    await flush();
    const headers = [...ui.target.querySelectorAll("thead tr th")];
    assert.equal(requests.length, 1);
    assert.equal(requests[0]?.pathname, "/v1/test-results/search-page");
    assert.equal(requests[0]?.searchParams.get("limit"), "50");
    assert.equal(
      requests[0]?.searchParams.get("offset"),
      "0",
      "the initial block starts at zero",
    );
    assert.deepEqual(
      [...requests[0].searchParams.keys()],
      ["offset", "limit", "include_count"],
      "initial search has no frontend filter parameters",
    );
    const visibleColumnIds = headers.map((header) =>
      header.getAttribute("data-svgrid-header-col"),
    );
    assert.deepEqual(visibleColumnIds, [
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
    assert.equal(
      ui.target
        .querySelector('tbody td[data-col-id="createdAt"]')
        ?.textContent.trim(),
      "2026-01-01 23:34:05",
      "created time is formatted as UTC seconds without fractional precision",
    );
    assert.equal(
      ui.target
        .querySelector('tbody td[data-col-id="category"]')
        ?.textContent.trim(),
      "category 20",
      "category is displayed separately beside the test case",
    );
    assert.deepEqual(visibleColumnIds.slice(16, 18), [
      "architecture",
      "environment",
    ]);
    assert.equal(
      headers[0].classList.contains("sv-grid-selection-column"),
      false,
    );
    assert.equal(!!headers[2].querySelector(".sv-grid-filter-button"), false);
    assert.equal(
      ui.target.querySelector(".sv-grid-selection-column"),
      null,
      "external filter checkboxes do not add row selection",
    );
    assert.equal(ui.target.textContent.includes("Bulk actions"), false);
    assert.equal(
      ui.target.textContent.includes("Create Attachment Rule"),
      false,
    );
    assert.equal(
      browser.document.querySelectorAll("dialog.search-result-details").length,
      1,
    );
    assert.equal(ui.target.querySelector(".sv-grid-header-icon-hint"), null);
    assert.equal(ui.target.querySelector(".sv-grid-filter-button"), null);
    assert.equal(ui.target.querySelector(".sv-grid-global-filter"), null);
    assert.equal(
      [...ui.target.querySelectorAll("button")].some((button) =>
        /^(Previous|Next) page$/.test(button.textContent.trim()),
      ),
      false,
      "infinite loading replaces explicit page navigation",
    );
    const renderedIds = [
      ...ui.target.querySelectorAll("tbody button[data-test-result-id]"),
    ].map((button) => button.getAttribute("data-test-result-id"));
    assert.equal(
      new Set(renderedIds).size,
      renderedIds.length,
      "no duplicate row artifacts after sorting",
    );
    const before = ui.handle.currentUrl.href;
    const writes = ui.handle.replacements.length;
    const rowsBeforeHeaderActivation = [...renderedIds];
    const testCaseHeader =
      /** @type {import('happy-dom').HTMLElement | null} */ (
        ui.target.querySelector(
          'th[data-svgrid-header-col="testCase"] .sv-grid-header-custom',
        )
      );
    assert.ok(testCaseHeader);
    testCaseHeader.click();
    await flush();
    assert.deepEqual(
      [...ui.target.querySelectorAll("tbody button[data-test-result-id]")].map(
        (button) => button.getAttribute("data-test-result-id"),
      ),
      rowsBeforeHeaderActivation,
      "header activation cannot locally sort cached server blocks",
    );
    const trigger = detailsButton(ui.target, 11);
    assert.ok(trigger.classList.contains("details-button"));
    assert.ok(
      trigger.querySelector(".icon.left svg"),
      "Details has an always-visible icon in Pragma's icon slot",
    );
    assert.ok(
      trigger.querySelector('.details-icon[aria-hidden="true"]'),
      "the decorative eye has its own non-shrinking size container",
    );
    assert.equal(trigger.querySelector(".text")?.textContent.trim(), "Details");
    trigger.dispatchEvent(
      new browser.MouseEvent("pointerdown", { bubbles: true, shiftKey: true }),
    );
    trigger.dispatchEvent(
      new browser.KeyboardEvent("keydown", { key: "Enter", bubbles: true }),
    );
    await flush();
    const dialog = detailsDialog();
    assert.equal(dialog.open, true);
    assert.match(dialog.textContent, /category 11/);
    assert.match(dialog.textContent, /template 11/);
    assert.equal(
      dialog
        .querySelector('a[aria-label="View Run for case 11"]')
        ?.getAttribute("href"),
      "/custom/base/configured-route/42?testExecutionId=7&testResultId=11",
    );
    assert.equal(ui.handle.currentUrl.href, before);
    assert.equal(ui.handle.replacements.length, writes);
    assert.equal(ui.target.querySelector(".selection-summary"), null);
    assert.equal(ui.target.querySelector(".sv-grid-cell-selected"), null);
    button(dialog, "Close").click();
    await flush();
    assert.equal(browser.document.activeElement, trigger);
    assert.equal(
      requests.filter(
        (request) => request.pathname === "/v1/test-results/search-page",
      ).length,
      1,
      "opening details does not fetch another table block",
    );
    assert.equal(
      requests.filter((request) =>
        request.pathname.startsWith("/v1/test-results/search-page/"),
      ).length,
      1,
      "details are fetched through their dedicated endpoint",
    );
  } finally {
    await ui.destroy();
  }
});

void test("loaded details show every Flutter-functional section, sorted Unicode metadata, execution timestamp and all future internal issues; logs stay literal and complete", async () => {
  const row = detailedResult(1);
  const log = `<script>globalThis.pwned=true</script>\n<img src=x onerror=alert(1)> & Ω\n  indented\n${"x".repeat(100_000)}\nEND`;
  const populated = {
    ...row,
    test_result: {
      ...row.test_result,
      io_log: log,
      issues: [
        {
          issue: {
            id: 123,
            source: "github",
            project: "org/project",
            key: "#123",
            title: "First <b>literal</b>",
            status: "open",
            url: "https://tracker.invalid/not-used",
          },
        },
        {
          issue: {
            id: 456,
            source: "jira",
            project: "Team",
            key: "TEAM-456",
            title: "Second 🐧",
            status: "closed",
            url: "javascript:alert(1)",
          },
        },
      ],
    },
  };
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    return Promise.resolve(
      request.pathname === "/v1/test-results/search-page"
        ? json({
            count: 1,
            limit: 50,
            offset: 0,
            rows: [tableResult(1, populated)],
          })
        : detailsResponse(populated),
    );
  };
  const ui = mounted("artefacts=one");
  try {
    await flush();
    detailsButton(ui.target, 1).click();
    await flush();
    const dialog = detailsDialog();
    assert.equal(
      dialog.querySelector("h2")?.textContent,
      "Test result details",
    );
    assert.deepEqual(
      [...dialog.querySelectorAll("h3")].map((heading) => heading.textContent),
      ["Test Case", "Artefact", "Test Execution", "Issues", "IO Log"],
    );
    for (const text of [
      "category 1",
      "template 1",
      "Configured-route",
      "example artefact",
      "1.2",
      "stable",
      "amd64",
      "smoke",
      "test lab",
      "org/project",
      "TEAM-456",
      "Second 🐧",
      "github",
      "jira",
      "open",
      "closed",
    ])
      assert.ok(dialog.textContent.includes(text), text);
    assert.deepEqual(
      [
        ...dialog.querySelectorAll(".execution-metadata tbody th[scope=row]"),
      ].map((node) => node.textContent),
      ["Alpha", "ζ Unicode 🐧"],
    );
    assert.deepEqual(
      [...dialog.querySelectorAll(".execution-metadata li")].map(
        (node) => node.textContent,
      ),
      ["a", "z", "一", "二"],
    );
    const table = dialog.querySelector("table.execution-metadata");
    assert.ok(table, "Metadata is a real table, not scalar description items");
    assert.equal(
      table.closest("dd"),
      null,
      "Metadata uses the section's full width",
    );
    assert.deepEqual(
      [...table.querySelectorAll("thead th[scope=col]")].map(
        (node) => node.textContent,
      ),
      ["Category", "Values"],
    );
    assert.deepEqual(
      [...dialog.querySelectorAll("section > .description-list-container")].map(
        (container) =>
          [...container.querySelectorAll("dt")].map((node) => node.textContent),
      ),
      [
        ["Name", "Category", "Template ID", "Status"],
        ["Family", "Name", "Version", "Track", "Architecture"],
        ["Execution ID", "Test Plan", "Environment", "Status", "Created"],
      ],
    );
    for (const list of dialog.querySelectorAll("dl")) {
      assert.ok(list.classList.contains("list"));
      for (const item of list.children) {
        assert.deepEqual(
          [...item.children].map((node) => node.tagName),
          ["DT", "DD"],
          "Each semantic scalar row pairs one label with one value",
        );
      }
    }
    const time = dialog.querySelector("time");
    assert.equal(time?.getAttribute("datetime"), "2026-02-03T07:04:56.000Z");
    assert.equal(time.getAttribute("title"), row.test_execution.created_at);
    assert.equal(
      time.textContent,
      new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "long",
      }).format(new Date(row.test_execution.created_at)),
    );
    const links = [...dialog.querySelectorAll(".issues a")];
    assert.deepEqual(
      links.map((link) => link.getAttribute("href")),
      ["/custom/base/issues/123", "/custom/base/issues/456"],
    );
    for (const link of links) {
      assert.equal(link.getAttribute("target"), "_blank");
      assert.equal(link.getAttribute("rel"), "noopener noreferrer");
      assert.match(link.getAttribute("aria-label") ?? "", /View issue/);
    }
    assert.equal(dialog.querySelector("pre")?.textContent, log);
    assert.equal(dialog.querySelector("pre")?.hasAttribute("tabindex"), false);
    assert.equal(dialog.querySelector("pre")?.hasAttribute("role"), false);
    assert.equal(dialog.querySelector("script, img, b"), null);
    assert.ok(dialog.querySelector("header, .dialog-content-header"));
    assert.ok(dialog.querySelector("footer, .dialog-content-footer"));
    assert.equal(dialog.querySelectorAll(".issues > li").length, 2);
  } finally {
    await ui.destroy();
  }
});

void test("empty optional details use em dashes and explicit metadata empty state; unconfigured family still opens without guessed Run", async () => {
  const row = detailedResult(1);
  const empty = {
    ...row,
    artefact: {
      ...row.artefact,
      family: "unconfigured",
      track: "",
      version: "",
    },
    test_execution: {
      ...row.test_execution,
      execution_metadata: {},
      created_at: "",
      test_plan: "",
    },
    test_result: { ...row.test_result, category: "", template_id: "" },
  };
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    return Promise.resolve(
      request.pathname === "/v1/test-results/search-page"
        ? json({
            count: 1,
            limit: 50,
            offset: 0,
            rows: [tableResult(1, empty)],
          })
        : detailsResponse(empty),
    );
  };
  const ui = mounted("artefacts=one");
  try {
    await flush();
    detailsButton(ui.target, 1).click();
    await flush();
    const dialog = detailsDialog();
    assert.match(dialog.textContent, /No execution metadata available\./);
    assert.equal(dialog.querySelector("pre, time, .issues, a"), null);
    assert.match(dialog.textContent, /Run unavailable/);
    assert.equal(
      [...dialog.querySelectorAll("dd")].filter(
        (node) => node.textContent === "—",
      ).length,
      6,
    );
    assert.deepEqual(
      [...dialog.querySelectorAll("h3")].map((node) => node.textContent),
      ["Test Case", "Artefact", "Test Execution"],
    );
  } finally {
    await ui.destroy();
  }
});

void test("server-backed grid filter drafts remain stable across opening Details", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    calls.push(request);
    return Promise.resolve(
      request.pathname === "/v1/test-results/search-page"
        ? json({ count: 1, limit: 50, offset: 0, rows: [tableResult(1)] })
        : detailsResponse(),
    );
  };
  const ui = mounted("test_cases=confirmed-A&artefacts=confirmed-B");
  try {
    await flush();
    const filters = ui.target.querySelector(
      '[data-testid="search-grid-filters"]',
    );
    assert.ok(filters);
    filters.querySelector("summary")?.click();
    await flush();
    const input = await enter(
      filters,
      '[data-search-grid-filter="test_cases"]',
      "unconfirmed-A 🐧",
    );
    await enter(filters, '[data-search-grid-filter="artefacts"]', "");
    const trigger = detailsButton(ui.target, 1);
    trigger.dispatchEvent(
      new browser.MouseEvent("pointerdown", { bubbles: true }),
    );
    trigger.click();
    await flush();
    button(detailsDialog(), "Close").click();
    await flush();
    assert.equal(
      filters.querySelector('[data-search-grid-filter="test_cases"]'),
      input,
    );
    assert.deepEqual(selectedValues(filters, "test_cases"), [
      "unconfirmed-A 🐧",
    ]);
    assert.equal(selectedValues(filters, "artefacts").length, 0);
    assert.equal(
      calls.filter((call) => call.pathname === "/v1/test-results/search-page")
        .length,
      1,
      "Details, removing B and saving A do not search",
    );
    assert.equal(
      calls.filter((call) =>
        call.pathname.startsWith("/v1/test-results/search-page/"),
      ).length,
      1,
    );
    assert.equal(
      ui.handle.currentUrl.searchParams.get("artefacts"),
      "confirmed-B",
      "applied URL stays unchanged until Search",
    );
    button(ui.target, "Search").click();
    await flush();
    const searches = calls.filter(
      (call) => call.pathname === "/v1/test-results/search-page",
    );
    assert.equal(searches.length, 2);
    assert.equal(
      searches[1].searchParams.get("test_cases"),
      "unconfirmed-A 🐧",
    );
    assert.equal(searches[1].searchParams.has("artefacts"), false);
    assert.equal(ui.handle.currentUrl.searchParams.has("artefacts"), false);
  } finally {
    await ui.destroy();
  }
});

void test("inclusive result-created date bounds remain stable while Details is open", async () => {
  let searchCalls = 0;
  let detailCalls = 0;
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    if (request.pathname === "/v1/test-results/search-page") {
      searchCalls++;
      return Promise.resolve(
        json({ count: 1, limit: 50, offset: 0, rows: [tableResult(1)] }),
      );
    }
    detailCalls++;
    return Promise.resolve(detailsResponse());
  };
  const ui = mounted(
    "from_date=2026-01-01T00:00:00Z&until_date=2026-01-10T00:00:00Z",
  );
  try {
    await flush();
    const filters = ui.target.querySelector(
      '[data-testid="search-grid-filters"]',
    );
    assert.ok(filters);
    filters.querySelector("summary")?.click();
    await flush();
    assert.equal(
      filters.querySelector('[data-search-grid-filter="from_date"]').value,
      "2026-01-01T00:00:00Z",
    );
    const trigger = detailsButton(ui.target, 1);
    trigger.dispatchEvent(
      new browser.MouseEvent("pointerdown", { bubbles: true }),
    );
    trigger.click();
    await flush();
    button(detailsDialog(), "Close").click();
    await flush();
    assert.equal(searchCalls, 1, "opening and closing Details does not search");
    assert.equal(
      detailCalls,
      1,
      "opening Details fetches only its detail record",
    );
    assert.equal(
      filters.querySelector('[data-search-grid-filter="from_date"]').value,
      "2026-01-01T00:00:00Z",
    );
    assert.equal(
      ui.handle.currentUrl.searchParams.get("until_date"),
      "2026-01-10T00:00:00Z",
    );
  } finally {
    await ui.destroy();
  }
});

void test("grid exposes all 23 columns and renders compact issues, reviewers, and literal metadata", async () => {
  const populated = result(1);
  populated.test_result.issues = [
    {
      issue: {
        id: 801,
        source: "github",
        project: "project",
        key: "BUG-801",
        title: "Unicode issue 🐛 with punctuation: %/—",
        status: "Open",
      },
    },
  ];
  populated.artefact.reviewers = [
    { id: 802, name: "Zoë Reviewer", launchpad_handle: "zoe-reviewer" },
  ];
  const longLiteral = `literal Unicode 🐧, punctuation: []{}! ${"unbroken-token-".repeat(24)}`;
  populated.test_execution.execution_metadata = {
    "pipeline:workflow_hash": [longLiteral],
    "failure:charm:component:status": ["值 🚀; colon: comma, percent%"],
  };
  const plural = result(3);
  plural.test_result.issues = [
    {
      issue: {
        id: 803,
        source: "github",
        project: "project",
        key: "BUG-803",
        title: "Another issue",
        status: "Open",
      },
    },
    {
      issue: {
        id: 804,
        source: "github",
        project: "project",
        key: "BUG-804",
        title: "One more issue",
        status: "Closed",
      },
    },
  ];
  plural.artefact.reviewers = [
    { id: 805, name: "First Reviewer" },
    { id: 806, name: "Second Reviewer" },
  ];
  plural.test_execution.execution_metadata = {
    one: ["first", "second"],
    two: ["third"],
  };
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    calls.push(request);
    return Promise.resolve(
      json({
        count: 3,
        limit: 50,
        offset: 0,
        rows: [
          tableResult(1, populated),
          tableResult(2),
          tableResult(3, plural),
        ],
      }),
    );
  };
  const ui = mounted();
  try {
    await flush();
    const headers = [...ui.target.querySelectorAll("thead tr th")].map(
      (header) => header.getAttribute("data-svgrid-header-col"),
    );
    assert.deepEqual(headers, [
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
    assert.equal(headers.length, 23);
    assert.equal(
      ui.target.querySelectorAll("th button.column-filter-trigger").length,
      18,
      "18 filter groups include Created's two date bounds",
    );
    assert.equal(
      browser.document.querySelectorAll("dialog.search-grid-value-dialog")
        .length,
      1,
      "one shared design-system modal serves every virtualized value cell",
    );
    assert.equal(
      ui.target
        .querySelector('tbody td[data-col-id="category"]')
        ?.textContent.trim(),
      "category 1",
    );
    const issues = ui.target.querySelector('td[data-col-id="issues"]');
    const reviewers = ui.target.querySelector('td[data-col-id="reviewers"]');
    const metadata = ui.target.querySelector(
      'td[data-col-id="executionMetadata"]',
    );
    /** @type {[HTMLElement | null, string][]} */
    const summaryCases = [
      [issues, "1 issue"],
      [reviewers, "1 reviewer"],
      [metadata, "2 metadata pairs"],
    ];
    for (const [cell, label] of summaryCases) {
      assert.ok(cell);
      const summary = cell.querySelector("button.summary");
      assert.ok(summary);
      assert.equal(summary.textContent.trim(), label);
      assert.equal(cell.querySelector(".preview"), null);
    }

    /** @type {[string, string, string[]][]} */
    const valueDialogCases = [
      [
        "issues",
        "1 issue",
        ["#801 · BUG-801", "Unicode issue 🐛 with punctuation"],
      ],
      ["reviewers", "1 reviewer", ["Zoë Reviewer", "@zoe-reviewer"]],
      [
        "executionMetadata",
        "2 metadata pairs",
        [
          "pipeline:workflow_hash",
          longLiteral,
          "failure:charm:component:status",
          "值 🚀; colon: comma, percent%",
        ],
      ],
    ];
    for (const [column, summaryText, rawValues] of valueDialogCases) {
      const cell = ui.target.querySelector(`td[data-col-id="${column}"]`);
      const summary = /** @type {HTMLButtonElement | null} */ (
        cell?.querySelector("button.summary")
      );
      assert.ok(cell);
      assert.ok(summary);
      assert.equal(summary.textContent.trim(), summaryText);
      summary.focus();
      summary.dispatchEvent(
        new browser.KeyboardEvent("keydown", { key: "Enter", bubbles: true }),
      );
      await flush();
      const valueDialog = gridValueDialog();
      assert.ok(valueDialog);
      assert.equal(valueDialog.closest("td"), null);
      assert.equal(valueDialog.open, true);
      assert.ok(valueDialog.querySelector(".dialog-content-header, header"));
      assert.ok(valueDialog.querySelector(".dialog-content-footer, footer"));
      assert.equal(
        valueDialog.querySelector('[role="region"][tabindex="0"]') !== null,
        true,
        "the complete list has a keyboard scroll region",
      );
      for (const rawValue of rawValues)
        assert.ok(valueDialog.textContent.includes(rawValue), rawValue);
      if (column === "issues") {
        const issueLink = valueDialog.querySelector("a.issue-link");
        assert.ok(issueLink);
        assert.equal(issueLink.getAttribute("href"), "/custom/base/issues/801");
        assert.equal(issueLink.getAttribute("target"), "_blank");
        assert.equal(issueLink.getAttribute("rel"), "noopener noreferrer");
        assert.equal(
          issueLink.getAttribute("aria-label"),
          "View issue BUG-801",
        );
        assert.match(issueLink.textContent, /BUG-801/);
        assert.match(
          issueLink.textContent,
          /Unicode issue 🐛 with punctuation/,
        );
      }
      if (column === "executionMetadata") {
        const table = valueDialog.querySelector("table.metadata-table");
        assert.ok(table, "metadata summary uses a semantic table");
        assert.deepEqual(
          [...table.querySelectorAll("thead th[scope=col]")].map(
            (header) => header.textContent,
          ),
          ["Category", "Value"],
        );
        assert.deepEqual(
          [...table.querySelectorAll("tbody tr")].map((row) => [
            row.querySelector('th[scope="row"]')?.textContent,
            row.querySelector("td")?.textContent,
          ]),
          [
            ["pipeline:workflow_hash", longLiteral],
            ["failure:charm:component:status", "值 🚀; colon: comma, percent%"],
          ],
        );
      }
      button(valueDialog, "Close").click();
      await flush();
      assert.equal(
        browser.document.activeElement,
        summary,
        "closing restores focus to the activated value summary",
      );
    }

    /** @type {[string, string, string][]} */
    const emptyDialogCases = [
      ["issues", "0 issues", "No issues available."],
      ["reviewers", "0 reviewers", "No reviewers available."],
      [
        "executionMetadata",
        "0 metadata pairs",
        "No execution metadata available.",
      ],
    ];
    for (const [column, label, emptyMessage] of emptyDialogCases) {
      const emptyCell = ui.target.querySelectorAll(
        `td[data-col-id="${column}"]`,
      )[1];
      assert.ok(emptyCell, `${column} renders the empty row`);
      const summary = /** @type {HTMLButtonElement | null} */ (
        emptyCell.querySelector("button.summary")
      );
      assert.ok(summary);
      assert.equal(summary.textContent.trim(), label);
      summary.click();
      await flush();
      const emptyDialog = gridValueDialog();
      assert.ok(emptyDialog);
      assert.equal(emptyDialog.open, true);
      assert.match(emptyDialog.textContent, new RegExp(emptyMessage));
      button(emptyDialog, "Close").click();
      await flush();
    }

    const recycledCell = ui.target.querySelector('td[data-col-id="issues"]');
    const recycledTrigger = /** @type {HTMLButtonElement | null} */ (
      recycledCell?.querySelector("button.summary")
    );
    assert.ok(recycledTrigger);
    recycledTrigger.focus();
    recycledTrigger.click();
    await flush();
    // Model SvGrid reusing a still-connected cell for a different result.
    recycledTrigger.dataset.searchGridValueOwner = "recycled:issues";
    button(gridValueDialog(), "Close").click();
    await flush();
    assert.equal(
      browser.document.activeElement,
      ui.target.querySelector(".results-grid"),
      "a recycled virtual cell returns focus to the grid region, not another record",
    );

    /** @type {[string, string][]} */
    const pluralSummaryCases = [
      ["issues", "2 issues"],
      ["reviewers", "2 reviewers"],
      ["executionMetadata", "3 metadata pairs"],
    ];
    for (const [column, label] of pluralSummaryCases) {
      const pluralCell = ui.target.querySelectorAll(
        `td[data-col-id="${column}"]`,
      )[2];
      assert.equal(
        pluralCell.querySelector("button.summary").textContent.trim(),
        label,
      );
    }

    assert.equal(
      calls.filter((request) =>
        request.pathname.startsWith("/v1/test-results/search-page/"),
      ).length,
      0,
      "table values and full-value affordances do not fetch Details",
    );
    assert.equal(
      calls.filter((request) => request.pathname.endsWith("/search-page"))
        .length,
      1,
    );
  } finally {
    await ui.destroy();
  }
});

void test("native close and query replacement invalidate stale Details callbacks", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    calls.push(request);
    const id = request.searchParams.get("artefacts") === "two" ? 2 : 1;
    return Promise.resolve(
      request.pathname === "/v1/test-results/search-page"
        ? json({ count: 1, limit: 50, offset: 0, rows: [tableResult(id)] })
        : detailsResponse(detailedResult(id)),
    );
  };
  const ui = mounted("artefacts=one");
  try {
    await flush();
    const oldTrigger = detailsButton(ui.target, 1);
    oldTrigger.click();
    await flush();
    const dialog = detailsDialog();
    dialog
      .querySelector("button")
      ?.dispatchEvent(
        new browser.KeyboardEvent("keydown", { key: "Escape", bubbles: true }),
      );
    await flush();
    assert.equal(dialog.open, false);
    assert.equal(browser.document.activeElement, oldTrigger);
    oldTrigger.click();
    await flush();
    ui.handle.restore(url("artefacts=two"));
    await flush();
    assert.equal(dialog.open, false);
    oldTrigger.click();
    await flush();
    assert.equal(dialog.open, false);
    const currentTrigger = detailsButton(ui.target, 2);
    currentTrigger.click();
    await flush();
    assert.equal(dialog.open, true);
    button(dialog, "Close").click();
    await flush();
    assert.equal(
      calls.filter((call) => call.pathname === "/v1/test-results/search-page")
        .length,
      2,
      "only initial/query requests load table blocks",
    );
  } finally {
    await ui.destroy();
  }
  assert.equal(
    browser.document.querySelector("dialog.search-result-details"),
    null,
  );
});

void test.skip("deferred: issue suggestion responses do not disturb Details", async () => {
  const pending = deferred();
  const pendingLabel = deferred();
  let suggestions = 0;
  let calls = 0;
  globalThis.fetch = (input) => {
    calls++;
    const request = new URL(input instanceof Request ? input.url : input);
    if (request.pathname.endsWith("/issues/990019"))
      return pendingLabel.promise;
    if (request.pathname.endsWith("/issues") && request.searchParams.has("q")) {
      suggestions++;
      return pending.promise;
    }
    if (request.pathname === "/v1/test-results/search-page")
      return Promise.resolve(
        json({ count: 1, limit: 50, offset: 0, rows: [tableResult(1)] }),
      );
    return Promise.resolve(detailsResponse());
  };
  const ui = mounted("issues=990019");
  try {
    await flush();
    chip(ui.target, "Issues").click();
    await flush();
    const input = await enter(
      ui.target,
      'input[name="issues"]',
      "pending text",
    );
    await new Promise((resolve) => setTimeout(resolve, 280));
    assert.equal(suggestions, 1);
    const trigger = detailsButton(ui.target, 1);
    trigger.dispatchEvent(
      new browser.MouseEvent("pointerdown", { bubbles: true }),
    );
    trigger.click();
    await flush();
    const focused = browser.document.activeElement;
    pending.resolve(
      json({
        issues: [
          {
            id: 990020,
            source: "github",
            project: "org",
            key: "990020",
            title: "Pending issue suggestion",
          },
        ],
      }),
    );
    pendingLabel.resolve(
      json({
        id: 990019,
        source: "github",
        project: "org",
        key: "990019",
        title: "Hydrated behind modal",
      }),
    );
    await new Promise((resolve) => setTimeout(resolve, 280));
    assert.equal(detailsDialog().open, true);
    assert.equal(browser.document.activeElement, focused);
    button(detailsDialog(), "Close").click();
    await flush();
    chip(ui.target, "Issues").click();
    await flush();
    assert.match(panel(ui.target).textContent, /Hydrated behind modal/);
    assert.equal(ui.target.querySelector('input[name="issues"]'), input);
    assert.equal(input.value, "pending text");
    assert.equal(suggestions, 1);
    assert.equal(
      calls,
      4,
      "table results, details, pending label and pending suggestion are isolated requests",
    );
  } finally {
    await ui.destroy();
  }
});

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
    if (selector === ":modal") return this.hasAttribute("data-test-modal");
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
  // Happy DOM has no native dialog/Invoker Commands implementation. Model only
  // open/close/toggle/focus restoration; actual top-layer, Tab containment,
  // backdrop and layout are covered by the opt-in Chromium regression.
  /** @type {WeakMap<import('happy-dom').HTMLDialogElement, import('happy-dom').HTMLElement | null>} */
  const invokers = new WeakMap();
  browser.HTMLDialogElement.prototype.showModal = function () {
    if (this.open) return;
    invokers.set(
      this,
      /** @type {import('happy-dom').HTMLElement | null} */ (
        browser.document.activeElement
      ),
    );
    for (const popover of openPopovers) hidePopover(popover);
    this.open = true;
    this.setAttribute("data-test-modal", "");
    this.querySelector("button")?.focus();
    this.dispatchEvent(toggleEvent("toggle", "closed", "open"));
  };
  browser.HTMLDialogElement.prototype.close = function () {
    if (!this.open) return;
    this.open = false;
    this.removeAttribute("data-test-modal");
    const invoker = invokers.get(this);
    if (invoker?.isConnected) invoker.focus();
    this.dispatchEvent(toggleEvent("toggle", "open", "closed"));
    setTimeout(() => this.dispatchEvent(new browser.Event("close")));
  };
  browser.document.addEventListener("click", (event) => {
    const target = /** @type {import('happy-dom').Element} */ (event.target);
    const command = target.closest('button[command="close"]');
    if (command) {
      const dialog = browser.document.getElementById(
        command.getAttribute("commandfor") ?? "",
      );
      if (dialog instanceof browser.HTMLDialogElement) dialog.close();
    }
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
  // Model the browser's default Enter activation for native buttons.
  browser.document.addEventListener(
    "keydown",
    (event) => {
      const target = /** @type {import('happy-dom').HTMLButtonElement} */ (
        event.target
      );
      queueMicrotask(() => {
        if (
          event.key === "Enter" &&
          !event.defaultPrevented &&
          target.matches("button")
        )
          target.click();
        if (event.key === "Escape" && !event.defaultPrevented) {
          const dialog =
            /** @type {import('happy-dom').HTMLDialogElement | null} */ (
              browser.document.querySelector("dialog[open]")
            );
          dialog?.close();
        }
      });
    },
    true,
  );
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

void test("grid rows map the compact API contract including category and Created", () => {
  const row = app.toSearchGridRow(tableResult(17), families, "/base");
  assert.equal(row.artefact, "example artefact");
  assert.equal(row.testCase, "case 17");
  assert.equal(row.category, "category 17");
  assert.equal(row.createdAt, "2026-01-01T00:00:00Z");
  assert.equal(row.environment, "test lab");
  assert.equal(row.architecture, "amd64");
  assert.equal(row.family, "snap");
  assert.equal(row.stage, "alpha");
  assert.equal(row.archived, false);
  assert.equal(row.executionStatus, "FAILED");
  assert.equal(row.rerunRequested, false);
  assert.equal(row.latestExecution, true);
  assert.equal(row.templateId, "template 17");
});

void test("grid renders compact issue/reviewer/metadata columns and still loads full Details on demand", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    calls.push(request);
    return Promise.resolve(
      request.pathname === "/v1/test-results/search-page"
        ? json({ count: 1, limit: 50, offset: 0, rows: [tableResult(17)] })
        : detailsResponse(detailedResult(17)),
    );
  };
  const ui = mounted();
  try {
    await flush();
    assert.deepEqual(
      [...ui.target.querySelectorAll("thead tr th")].map((header) =>
        header.getAttribute("data-svgrid-header-col"),
      ),
      [
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
      ],
    );
    assert.equal(
      ui.target
        .querySelector('tbody td[data-col-id="execution"]')
        ?.textContent.trim(),
      "7",
      "Execution ID remains display-only",
    );
    assert.equal(
      ui.target
        .querySelector('tbody td[data-col-id="architecture"]')
        ?.textContent.trim(),
      "amd64",
      "Architecture remains display-only",
    );
    assert.equal(
      ui.target
        .querySelector('tbody td[data-col-id="category"]')
        ?.textContent.trim(),
      "category 17",
    );
    assert.equal(calls.length, 1, "compact row values do not fetch Details");
    for (const column of ["execution", "architecture", "run", "details"])
      assert.equal(
        ui.target.querySelector(
          `th[data-svgrid-header-col="${column}"] button[aria-label^="Filter"]`,
        ),
        null,
        `${column} has no filter control`,
      );
    assert.equal(
      ui.target
        .querySelector(
          'th[data-svgrid-header-col="latestExecution"] button[aria-label="Filter Latest Execution"]',
        )
        ?.getAttribute("aria-label"),
      "Filter Latest Execution",
    );
    assert.equal(ui.target.querySelector(".sv-grid-selection-column"), null);
    detailsButton(ui.target, 17).click();
    await flush();
    assert.equal(calls.length, 2);
    assert.ok(detailsDialog().textContent.includes("Execution Metadata"));
  } finally {
    await ui.destroy();
  }
});

void test("active grid filter drafts apply only on Search as exact repeated API conditions", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    calls.push(request);
    return Promise.resolve(response([1], 1));
  };
  const ui = mounted();
  try {
    await flush();
    assert.equal(calls.length, 1);
    assert.equal(ui.target.querySelector(".sv-grid-filter-menu"), null);
    assert.equal(ui.target.querySelector(".sv-grid-menu-filter"), null);
    let gridFilters = ui.target.querySelector(
      '[data-testid="search-grid-filters"]',
    );
    assert.ok(gridFilters);
    assert.equal(gridFilters.querySelector(".filter-panel"), null);
    assert.equal(gridFilters.querySelector("details"), null);
    for (const [column, label, field] of [
      ["createdAt", "Created", "from_date"],
      ["artefact", "Artefact", "artefacts"],
      ["family", "Family", "families"],
      ["stage", "Stage", "artefact_stages"],
      ["archived", "Archived", "artefact_is_archived"],
      ["testCase", "Test case", "test_cases"],
      ["executionStatus", "Execution Status", "test_execution_statuses"],
      ["rerunRequested", "Rerun Requested", "rerun_is_requested"],
      ["latestExecution", "Latest Execution", "execution_is_latest"],
      ["status", "Result status", "test_result_statuses"],
      ["track", "Track", "artefact_tracks"],
      ["version", "Version", "artefact_versions"],
      ["environment", "Environment", "environments"],
      ["testPlan", "Test plan", "test_plans"],
      ["templateId", "Template ID", "template_ids"],
    ]) {
      const trigger = /** @type {HTMLButtonElement | null} */ (
        ui.target.querySelector(
          `th[data-svgrid-header-col="${column}"] button[aria-label="Filter ${label}"]`,
        )
      );
      assert.ok(trigger, `SvGrid ${label} column exposes its filter control`);
      trigger.dispatchEvent(
        new browser.MouseEvent("pointerdown", { bubbles: true }),
      );
      trigger.click();
      await flush();
      const menu = trigger.closest("th")?.querySelector('[role="dialog"]');
      assert.ok(menu && !menu.hidden, `${label} opens its anchored menu`);
      assert.equal(menu.closest("th"), trigger.closest("th"));
      assert.equal(menu.querySelector(".sv-grid-filter-menu"), null);
      assert.doesNotMatch(
        menu.textContent,
        /Contains|Starts with|Regex|Not contains|Greater than|Less than/,
      );
      assert.ok(
        menu.querySelector(`[data-search-grid-filter="${field}"]`),
        `${label} menu owns its filter input`,
      );
      if (
        ["artefacts", "environments", "test_cases", "test_plans"].includes(
          field,
        )
      ) {
        const suggestionInput = /** @type {HTMLInputElement | null} */ (
          menu.querySelector(`[data-search-grid-filter="${field}"]`)
        );
        assert.equal(
          suggestionInput?.type,
          "search",
          `${label} uses the shared lookup editor`,
        );
        assert.ok(
          [...menu.querySelectorAll("button")].some((button) =>
            button.textContent.includes("Add exact value"),
          ),
        );
      }
    }
    const dateFilterButton = /** @type {HTMLButtonElement | null} */ (
      ui.target.querySelector(
        'th[data-svgrid-header-col="createdAt"] button[aria-label="Filter Created"]',
      )
    );
    assert.ok(dateFilterButton);
    dateFilterButton.click();
    await flush();
    assert.equal(dateFilterButton.getAttribute("aria-expanded"), "true");
    assert.ok(
      dateFilterButton
        .closest("th")
        ?.querySelector('[data-search-grid-filter="until_date"]'),
      "From and Until share the Created column menu",
    );

    chip(ui.target, "Result status").click();
    await flush();
    for (const status of ["PASSED", "FAILED"]) {
      const choice = /** @type {HTMLInputElement | null} */ (
        gridFilters.querySelector(
          `input[data-search-grid-filter="test_result_statuses"][value="${status}"]`,
        )
      );
      assert.ok(choice);
      choice.click();
    }
    assert.deepEqual(
      /** @type {HTMLInputElement[]} */ ([
        ...gridFilters.querySelectorAll(
          'input[data-search-grid-filter="test_result_statuses"]:checked',
        ),
      ]).map((input) => input.value),
      ["PASSED", "FAILED"],
    );
    for (const [label, key, value] of [
      ["Artefact", "artefacts", "alpha, beta,alpha"],
      ["Version", "artefact_versions", "1.0, 2.0"],
      ["Track", "artefact_tracks", "stable"],
      ["Environment", "environments", "lab one, lab two"],
      ["Test case", "test_cases", "case one, case two"],
      ["Test plan", "test_plans", "smoke"],
    ]) {
      chip(ui.target, label).click();
      await flush();
      await enter(gridFilters, `[data-search-grid-filter="${key}"]`, value);
    }
    chip(ui.target, "Created").click();
    await flush();
    await enter(
      gridFilters,
      '[data-search-grid-filter="from_date"]',
      "2026-01-01T00:00:00.123456Z",
    );
    await enter(
      gridFilters,
      '[data-search-grid-filter="until_date"]',
      "2026-01-31T23:59:59Z",
    );

    assert.equal(
      calls.length,
      1,
      "draft filters never fetch or filter loaded rows",
    );
    assert.match(ui.target.textContent, /case 1/);
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls.length, 2);
    const params = calls[1].searchParams;
    assert.equal(params.get("offset"), "0");
    assert.deepEqual(params.getAll("test_result_statuses"), [
      "PASSED",
      "FAILED",
    ]);
    assert.deepEqual(params.getAll("artefacts"), ["alpha", "beta"]);
    assert.deepEqual(params.getAll("artefact_versions"), ["1.0", "2.0"]);
    assert.deepEqual(params.getAll("environments"), ["lab one", "lab two"]);
    assert.deepEqual(params.getAll("test_cases"), ["case one", "case two"]);
    assert.equal(params.get("test_plans"), "smoke");
    assert.equal(params.get("from_date"), "2026-01-01T00:00:00.123456Z");
    assert.equal(params.get("until_date"), "2026-01-31T23:59:59Z");
    assert.equal(ui.handle.currentUrl.searchParams.get("offset"), null);
  } finally {
    await ui.destroy();
  }
});

void test("new column editors share a draft and serialize only canonical API keys", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    calls.push(request);
    return Promise.resolve(response([1], 1));
  };
  const ui = mounted();
  try {
    await flush();
    let grid = ui.target.querySelector('[data-testid="search-grid-filters"]');
    assert.ok(grid);

    chip(ui.target, "Family").click();
    await flush();
    assert.equal(grid.querySelector('input[value="snap"]')?.value, "snap");
    assert.match(panel(ui.target).textContent, /Configured-route/);
    const snapFamily = /** @type {HTMLInputElement | null} */ (
      grid.querySelector(
        'input[data-search-grid-filter="families"][value="snap"]',
      )
    );
    assert.ok(snapFamily);
    snapFamily.click();

    chip(ui.target, "Stage").click();
    await flush();
    const noStage = /** @type {HTMLInputElement | null} */ (
      grid.querySelector(
        'input[data-search-grid-filter="artefact_stages"][value=""]',
      )
    );
    assert.ok(noStage?.parentElement?.textContent.includes("(none)"));
    noStage.click();

    chip(ui.target, "Archived").click();
    await flush();
    const archived = /** @type {HTMLSelectElement | null} */ (
      grid.querySelector(
        'select[data-search-grid-filter="artefact_is_archived"]',
      )
    );
    assert.ok(archived);
    assert.deepEqual(
      [...archived.options].map((option) => [option.value, option.textContent]),
      [
        ["", "Any"],
        ["false", "No"],
        ["true", "Yes"],
      ],
    );
    archived.value = "true";
    archived.dispatchEvent(new browser.Event("change", { bubbles: true }));

    chip(ui.target, "Execution Status").click();
    await flush();
    for (const status of app.EXECUTION_STATUSES)
      assert.ok(grid.querySelector(`input[value="${status}"]`), status);
    const executionStatus = /** @type {HTMLInputElement | null} */ (
      grid.querySelector(
        'input[data-search-grid-filter="test_execution_statuses"][value="IN_PROGRESS"]',
      )
    );
    assert.ok(executionStatus);
    executionStatus.click();

    chip(ui.target, "Rerun Requested").click();
    await flush();
    const rerun = /** @type {HTMLSelectElement | null} */ (
      grid.querySelector('select[data-search-grid-filter="rerun_is_requested"]')
    );
    assert.ok(rerun);
    rerun.value = "false";
    rerun.dispatchEvent(new browser.Event("change", { bubbles: true }));

    chip(ui.target, "Latest Execution").click();
    await flush();
    const latest = /** @type {HTMLSelectElement | null} */ (
      grid.querySelector(
        'select[data-search-grid-filter="execution_is_latest"]',
      )
    );
    assert.ok(latest);
    latest.value = "false";
    latest.dispatchEvent(new browser.Event("change", { bubbles: true }));
    await flush();
    assert.equal(
      grid
        .querySelector(
          'th[data-svgrid-header-col="latestExecution"] .column-filter-trigger',
        )
        ?.classList.contains("active"),
      true,
      "false remains an active latest-execution condition",
    );

    chip(ui.target, "Template ID").click();
    await flush();
    await enter(
      grid,
      '[data-search-grid-filter="template_ids"]',
      "template:exact = v2",
    );

    assert.equal(calls.length, 1, "column edits do not search independently");
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls.length, 2);
    const params = calls[1].searchParams;
    assert.deepEqual(params.getAll("families"), ["snap"]);
    assert.deepEqual(params.getAll("artefact_stages"), [""]);
    assert.equal(params.get("artefact_is_archived"), "true");
    assert.deepEqual(params.getAll("test_execution_statuses"), ["IN_PROGRESS"]);
    assert.equal(params.get("rerun_is_requested"), "false");
    assert.equal(params.get("execution_is_latest"), "false");
    assert.deepEqual(params.getAll("template_ids"), ["template:exact = v2"]);

    // Each nullable boolean menu exposes a true unrestricted state.
    grid = ui.target.querySelector('[data-testid="search-grid-filters"]');
    assert.ok(grid);
    for (const [label, key] of [
      ["Archived", "artefact_is_archived"],
      ["Rerun Requested", "rerun_is_requested"],
      ["Latest Execution", "execution_is_latest"],
    ]) {
      chip(ui.target, label).click();
      await flush();
      const select = /** @type {HTMLSelectElement | null} */ (
        grid.querySelector(`select[data-search-grid-filter="${key}"]`)
      );
      assert.ok(select);
      assert.ok([...select.options].some((option) => option.value === ""));
      select.value = "";
      select.dispatchEvent(new browser.Event("change", { bubbles: true }));
    }
    button(ui.target, "Search").click();
    await flush();
    for (const key of [
      "artefact_is_archived",
      "rerun_is_requested",
      "execution_is_latest",
    ])
      assert.equal(calls[2].searchParams.has(key), false, key);
  } finally {
    await ui.destroy();
  }
});

void test("compact row columns use configured family labels and distinguish empty from missing stages", async () => {
  const configured = result(1);
  configured.artefact.stage = "";
  configured.artefact.archived = true;
  configured.test_execution.rerun_is_requested = true;
  configured.test_execution.execution_is_latest = false;
  configured.test_result.template_id = "template:exact = v2";
  const unknown = result(2);
  unknown.artefact.family = "unconfigured-family";
  unknown.artefact.stage = null;
  unknown.artefact.archived = false;
  unknown.test_execution.rerun_is_requested = false;
  unknown.test_execution.execution_is_latest = true;
  globalThis.fetch = () =>
    Promise.resolve(
      json({
        count: 2,
        limit: 50,
        offset: 0,
        rows: [tableResult(1, configured), tableResult(2, unknown)],
      }),
    );
  const ui = mounted();
  try {
    await flush();
    const cells = (column) =>
      [...ui.target.querySelectorAll(`tbody td[data-col-id="${column}"]`)].map(
        (cell) => cell.textContent.trim(),
      );
    assert.deepEqual(cells("family"), [
      "Configured-route",
      "unconfigured-family",
    ]);
    assert.deepEqual(cells("stage"), ["(none)", "—"]);
    assert.deepEqual(cells("archived"), ["Yes", "No"]);
    assert.deepEqual(cells("executionStatus"), ["FAILED", "FAILED"]);
    assert.deepEqual(cells("rerunRequested"), ["Yes", "No"]);
    assert.deepEqual(cells("latestExecution"), ["No", "Yes"]);
    assert.deepEqual(cells("templateId"), [
      "template:exact = v2",
      "template 2",
    ]);
  } finally {
    await ui.destroy();
  }
});

void test("visible grid filters match OpenAPI names, repeated parameters, and exact-match contracts", async () => {
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
  for (const key of ORIGINAL_LIST_FILTERS) {
    assert.ok(
      parameters
        .find((parameter) => parameter.name === key)
        ?.schema.anyOf?.some((type) => type.type === "array"),
      key,
    );
    assert.match(matching, new RegExp(`\\.in_\\(filters\\.${key}\\)`));
  }
  const params = new URLSearchParams(
    "test_result_statuses=FAILED,PASSED&test_result_statuses=SKIPPED&artefacts=alpha, beta&artefacts=alpha&artefact_versions=1%2B2&artefact_tracks=stable&environments=lab&test_plans=smoke&test_cases=case",
  );
  const query = app.parseSearchPage(params, families);
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
  assert.deepEqual(
    app.parseSearchPage(apiParams, families).filters,
    query.filters,
  );
  const rangeParams = app.searchRangeParams(query.filters, 125, 225);
  assert.equal(rangeParams.get("offset"), "125");
  assert.equal(rangeParams.get("limit"), "100");
  assert.deepEqual(rangeParams.getAll("artefacts"), ["alpha", "beta"]);
  assert.throws(
    () => app.searchRangeParams(query.filters, 0, 1001),
    RangeError,
  );
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
      ["alpha"],
      "",
    ),
    null,
  );
});

void test("invalid conditions block while legacy page parameters are ignored and start at the recent range", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(response());
  };
  /** @type {import("../src/lib/stores/test-results-search.svelte").TestResultsSearchStore} */
  const store = new app.TestResultsSearchStore();
  for (const query of [
    "artefacts=ok&test_execution_statuses=INVALID",
    "families=unknown",
    "test_result_statuses=UNKNOWN",
  ]) {
    const applied = app.parseSearchPage(url(query).searchParams, families);
    assert.ok(applied.problems.length, query);
    await store.search(applied);
    assert.equal(store.response, null);
    assert.equal(store.loading, false);
  }
  assert.equal(calls.length, 0, "invalid conditions never broaden the query");
  for (const query of ["", "view=invalid"]) {
    await store.search(app.parseSearchPage(url(query).searchParams, families));
    assert.equal(store.response?.limit, 50);
    assert.equal(store.response.offset, 0);
  }
  for (const query of [
    "limit=2&offset=3",
    "artefacts= , ",
    "view=invalid&limit=2&offset=3",
  ]) {
    await store.search(app.parseSearchPage(url(query).searchParams, families));
    assert.ok(store.response);
  }
  assert.equal(calls.length, 5);
  assert.equal(calls[0]?.pathname, "/v1/test-results/search-page");
  assert.equal(calls[0]?.searchParams.get("limit"), "50");
  assert.equal(calls[0]?.searchParams.get("offset"), "0");
  assert.equal(calls[1]?.searchParams.get("limit"), "50");
  assert.equal(calls[1]?.searchParams.get("offset"), "0");
  assert.equal(calls[2]?.searchParams.get("limit"), "50");
  assert.equal(calls[2]?.searchParams.get("offset"), "0");
});

void test("infinite search uses exact first-block ranges, keeps server count, and preserves API request defaults", async () => {
  /** @type {{url: URL; options: RequestInit}[]} */
  const calls = [];
  const replies = [response([1, 2], 9), response([1, 2], 9)];
  globalThis.fetch = (input, options = {}) => {
    calls.push({
      url: new URL(input instanceof Request ? input.url : input),
      options,
    });
    return Promise.resolve(replies.shift() ?? response());
  };
  /** @type {import("../src/lib/stores/test-results-search.svelte").TestResultsSearchStore} */
  const store = new app.TestResultsSearchStore();
  await store.search(
    app.parseSearchPage(
      url("artefacts=one,two&test_cases=case&limit=2&offset=99").searchParams,
      families,
    ),
  );
  const state = store.state;
  assert.ok(state);
  assert.equal(state.rowCount, 9);
  assert.equal(state.lastRowKnown, true);
  assert.deepEqual(
    state.rows.slice(0, 2).map((row) => row.id),
    [1, 2],
  );
  await store.search(
    app.parseSearchPage(
      url("artefacts=one,two&test_cases=case").searchParams,
      families,
    ),
  );
  assert.equal(calls.length, 2);
  for (const call of calls) {
    assert.equal(call.url.pathname, "/v1/test-results/search-page");
    assert.equal(call.url.searchParams.get("offset"), "0");
    assert.equal(call.url.searchParams.get("limit"), "50");
    assert.deepEqual(call.url.searchParams.getAll("artefacts"), ["one", "two"]);
    assert.equal(call.options.credentials, "include");
    assert.equal(new Headers(call.options.headers).get("X-CSRF-Token"), "1");
    assert.equal(call.options.method ?? "GET", "GET");
  }
});

void test("Search block requests serialize all canonical filter parameters", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(response());
  };
  const metadata = `${Buffer.from("build").toString("base64")}:${Buffer.from("stable").toString("base64")}`;
  const source = new URLSearchParams([
    ["families", "snap"],
    ["test_result_statuses", "FAILED,PASSED"],
    ["test_execution_statuses", "IN_PROGRESS"],
    ["artefacts", "one,two"],
    ["artefact_versions", "1"],
    ["artefact_tracks", "stable"],
    ["environments", "lab"],
    ["test_plans", "smoke"],
    ["test_cases", "case"],
    ["artefact_stages", ""],
    ["artefact_is_archived", "false"],
    ["rerun_is_requested", "true"],
    ["execution_is_latest", "false"],
    ["issues", "1,2"],
    ["reviewer_ids", "none"],
    ["execution_metadata", metadata],
    ["from_date", "2026-01-01T00:00:00Z"],
    ["until_date", "2026-01-31T23:59:59Z"],
    ["template_ids", "template-a,template-b"],
  ]);
  const store = new app.TestResultsSearchStore();
  await store.search(app.parseSearchPage(source, families));

  assert.equal(calls.length, 1);
  const request = calls[0];
  assert.equal(request.pathname, "/v1/test-results/search-page");
  for (const key of app.SEARCH_FILTERS)
    assert.ok(request.searchParams.has(key), key);
  assert.deepEqual(request.searchParams.getAll("artefacts"), ["one", "two"]);
  assert.deepEqual(request.searchParams.getAll("test_result_statuses"), [
    "FAILED",
    "PASSED",
  ]);
  assert.deepEqual(request.searchParams.getAll("issues"), ["1", "2"]);
  assert.deepEqual(request.searchParams.getAll("reviewer_ids"), ["none"]);
  assert.deepEqual(request.searchParams.getAll("execution_metadata"), [
    metadata,
  ]);
  assert.deepEqual(request.searchParams.getAll("artefact_stages"), [""]);
  assert.equal(request.searchParams.get("artefact_is_archived"), "false");
  assert.equal(request.searchParams.get("rerun_is_requested"), "true");
  assert.equal(request.searchParams.get("execution_is_latest"), "false");
  assert.deepEqual(request.searchParams.getAll("template_ids"), [
    "template-a",
    "template-b",
  ]);
  assert.equal(request.searchParams.get("offset"), "0");
  assert.equal(request.searchParams.get("limit"), "50");
  assert.equal(request.searchParams.get("include_count"), "true");
  assert.equal(request.searchParams.has("assignee_ids"), false);
});

void test("Search accepts every canonical filter type; malformed values still block the store", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(response());
  };
  const store = new app.TestResultsSearchStore();
  for (const input of [
    "from_date=2026-01-01T00:00:00Z",
    "until_date=2026-01-01T00:00:00Z",
    "artefacts=example",
    "test_cases=case-one",
    "test_result_statuses=FAILED",
    "families=snap",
    "artefact_stages=",
    "artefact_is_archived=false",
    "rerun_is_requested=true",
    "execution_is_latest=false",
    "issues=none",
    "reviewer_ids=1,2",
    `execution_metadata=${Buffer.from("build").toString("base64")}:${Buffer.from("stable").toString("base64")}`,
    "template_ids=template",
    "test_execution_statuses=IN_PROGRESS",
  ]) {
    await store.search(app.parseSearchPage(url(input).searchParams, families));
    assert.ok(store.response, input);
  }
  assert.equal(calls.length, 15);
  for (const input of [
    "execution_metadata=broken",
    "families=unknown",
    "execution_is_latest=null",
    "issues=1,any",
    "reviewer_ids=9007199254740992",
    "from_date=2026-02-30T00:00:00Z",
    "until_date=2026-01-01",
    "from_date=2026-02-01T00:00:00Z&until_date=2026-01-01T00:00:00Z",
  ]) {
    await store.search(
      app.parseSearchPage(
        url(`artefacts=valid&${input}`).searchParams,
        families,
      ),
    );
    assert.equal(store.response, null, input);
    assert.equal(store.loading, false, input);
  }
  assert.equal(
    calls.length,
    15,
    "partial valid filters never make an invalid search eligible",
  );
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
      app.parseSearchPage(url("artefacts=old").searchParams, families),
    );
    await store.search(
      app.parseSearchPage(url("artefacts=new").searchParams, families),
    );
    old.resolve(oldStatus === 200 ? response([1]) : json({}, oldStatus));
    await older;
    assert.equal(store.response?.rows[0]?.test_result.id, 2);
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
    return request.searchParams.get("artefacts") === "old"
      ? Promise.resolve(json({}, 403))
      : Promise.resolve(response([2]));
  };
  const store = new app.TestResultsSearchStore();
  const older = store.search(
    app.parseSearchPage(url("artefacts=old").searchParams, families),
  );
  await flush();
  assert.equal(checking, true);
  await store.search(app.parseSearchPage(url().searchParams, families));
  session.resolve(json({ id: 5, teams: [], is_admin: false }));
  await older;
  assert.equal(store.response?.rows[0]?.test_result.id, 2);
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
      app.parseSearchPage(url("artefacts=one").searchParams, families),
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
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    if (request.pathname.endsWith("/users/me"))
      return Promise.resolve(oldResponse);
    return request.searchParams.get("artefacts") === "old"
      ? Promise.resolve(json({}, 403))
      : Promise.resolve(response([2]));
  };
  const store = new app.TestResultsSearchStore();
  const older = store.search(
    app.parseSearchPage(url("artefacts=old").searchParams, families),
  );
  await flush();
  assert.equal(readingBody, true);
  await store.search(app.parseSearchPage(url().searchParams, families));
  session.resolve(json(null));
  await older;
  assert.equal(app.userStore.current?.id, user.id);
  assert.equal(store.accessError, null);
});

/**
 * @param {string} [query]
 * @param {(next: URL) => Promise<unknown>} [navigatePending]
 */
function mounted(query = "", navigatePending) {
  const target = browser.document.createElement("div");
  browser.document.body.append(target);
  const handle = app.mountSearch(
    /** @type {HTMLElement} */ (/** @type {unknown} */ (target)),
    url(query),
    families,
    navigatePending,
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
  const found = [...target.querySelectorAll("[data-search-grid-menu]")].find(
    (menu) => !menu.closest("[hidden]"),
  );
  assert.ok(found, "A column-header filter menu must be open");
  return /** @type {import('happy-dom').HTMLElement} */ (found);
}

/** @param {import('happy-dom').HTMLElement} target @param {string} field */
function selectedValues(target, field) {
  const input = target.querySelector(`[data-search-grid-filter="${field}"]`);
  const picker = input?.closest('[id$="-picker"]');
  return Array.from(picker?.querySelectorAll(".selected li > span") ?? []).map(
    (item) => item.textContent,
  );
}

/** @param {import('happy-dom').HTMLElement} target @param {string} selector @param {string} value */
async function enter(target, selector, value) {
  const input = /** @type {import('happy-dom').HTMLInputElement | null} */ (
    target.querySelector(selector)
  );
  assert.ok(input);
  const field = input.getAttribute("data-search-grid-filter");
  if (
    ["artefacts", "environments", "test_cases", "test_plans"].includes(
      field ?? "",
    )
  ) {
    const editor = input.closest("[data-search-grid-menu]") ?? target;
    for (const remove of editor.querySelectorAll("button"))
      if (remove.getAttribute("aria-label")?.startsWith("Remove selected "))
        remove.click();
    for (const part of value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean)) {
      await typeOnly(input, part);
      button(editor, "Add exact value").click();
      await flush();
    }
    if (!value.trim()) await flush();
    return input;
  }
  await typeOnly(input, value);
  return input;
}

/** @param {import('happy-dom').HTMLInputElement} input @param {string} value */
async function typeOnly(input, value) {
  input.value = value;
  input.dispatchEvent(new browser.Event("input", { bubbles: true }));
  await flush();
}

/** Use the explicit manual path when these tests are about confirmed exact
 * conditions, rather than unconfirmed suggestion query text. Existing comma
 * links still restore; new lookup values are added one at a time deliberately.
 * @param {import('happy-dom').HTMLElement} target
 * @param {string} selector @param {string} value
 */
async function replaceExact(target, selector, value) {
  const editor =
    target.closest(".panel") ?? target.querySelector(".panel") ?? target;
  const exact = Array.from(editor.querySelectorAll("button")).find((b) =>
    b.textContent.includes("Add exact"),
  );
  if (!exact) return enter(target, selector, value);
  for (const remove of editor.querySelectorAll("button"))
    if (remove.getAttribute("aria-label")?.startsWith("Remove selected "))
      remove.click();
  await flush();
  let input;
  for (const part of value
    .split(",")
    .map((v) => v.trim())
    .filter(Boolean)) {
    input = await enter(target, selector, part);
    exact.click();
    await flush();
  }
  assert.ok(input);
  return input;
}

/** @param {import('happy-dom').HTMLElement} target @param {string} label */
async function chooseFilter(target, label) {
  const headerLabel =
    label === "Metadata"
      ? "Execution Metadata"
      : label === "Reviewers"
        ? "Reviewers"
        : label;
  const trigger = /** @type {import('happy-dom').HTMLButtonElement | null} */ (
    target.querySelector(`button[aria-label="Filter ${headerLabel}"]`)
  );
  assert.ok(trigger, `Missing ${label} column filter`);
  trigger.click();
  await flush();
}

async function flushColumnDraft() {
  // Header menus write their confirmed draft directly; there is no detached
  // Add-filter editor or intermediate confirmation step.
  await flush();
}

/** @param {import('happy-dom').HTMLElement} target @param {string} label */
function chip(target, label) {
  const headerLabel =
    label === "Metadata"
      ? "Execution Metadata"
      : label === "Reviewers"
        ? "Reviewers"
        : label;
  const found = target.querySelector(
    `button[aria-label="Filter ${headerLabel}"]`,
  );
  assert.ok(found, `Missing ${label} column filter`);
  return /** @type {import('happy-dom').HTMLButtonElement} */ (found);
}

/** @param {import('happy-dom').HTMLElement} target @param {"issues" | "reviewer_ids"} field */
function hydratedSelection(target, field) {
  return (
    target.querySelector(
      `[data-search-grid-menu="${field}"] [aria-label="Selected details"]`,
    )?.textContent ?? ""
  );
}

void test("mounted column filters restore from repeated URLs, survive view changes and clear", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    calls.push(request);
    const limit = Number(request.searchParams.get("limit") ?? 50);
    return Promise.resolve(
      response(
        Array.from({ length: limit }, (_, i) => i + 1),
        200,
        limit,
      ),
    );
  };
  const params = new URLSearchParams({
    artefacts: "old",
    test_cases: "case-one",
    test_result_statuses: "FAILED",
    artefact_versions: "1.0",
    artefact_tracks: "stable",
    environments: "lab",
    test_plans: "smoke",
    from_date: "2024-02-29T00:00:00.123456Z",
    until_date: "2026-10-20T00:00:00+01:00",
    limit: "2",
  });
  params.append("test_cases", "case-two");
  const ui = mounted(params.toString());
  try {
    await flush();
    assert.equal(calls.length, 1);
    assert.doesNotMatch(
      ui.target.textContent,
      /Additional URL filters|not available yet/,
    );
    assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 0);
    assert.doesNotMatch(
      ui.target.textContent,
      /\+ Add filter|Edit Issues:|Edit Metadata:/,
    );
    for (const label of ["Issues", "Reviewers", "Execution Metadata"])
      assert.ok(
        ui.target.querySelector(`button[aria-label="Filter ${label}"]`),
      );
    let gridFilters = ui.target.querySelector(
      '[data-testid="search-grid-filters"]',
    );
    assert.ok(gridFilters);
    gridFilters.querySelector("summary")?.click();
    await flush();
    assert.deepEqual(selectedValues(gridFilters, "artefacts"), ["old"]);
    assert.deepEqual(selectedValues(gridFilters, "test_cases"), [
      "case-one",
      "case-two",
    ]);
    await enter(gridFilters, '[data-search-grid-filter="artefacts"]', "new");
    const viewOnly = new URL(ui.handle.currentUrl);
    viewOnly.searchParams.set("view", "invalid-view");
    ui.handle.restore(viewOnly);
    await flush();
    assert.equal(
      calls.length,
      1,
      "view-only replacement cannot refetch or discard drafts",
    );
    assert.deepEqual(selectedValues(gridFilters, "artefacts"), ["new"]);
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls.length, 2);
    assert.equal(calls[1].searchParams.get("artefacts"), "new");
    assert.equal(calls[1].searchParams.has("view"), false);
    for (const key of [
      "test_cases",
      "test_result_statuses",
      "artefact_versions",
      "artefact_tracks",
      "environments",
      "test_plans",
      "from_date",
      "until_date",
    ])
      assert.deepEqual(
        calls[1].searchParams.getAll(key),
        params.getAll(key),
        key,
      );
    ui.handle.restore(url(params.toString()));
    await flush();
    gridFilters = ui.target.querySelector(
      '[data-testid="search-grid-filters"]',
    );
    assert.ok(gridFilters);
    assert.equal(calls.length, 3);
    assert.deepEqual(selectedValues(gridFilters, "artefacts"), ["old"]);
    // A date alone is a meaningful Flutter search, not an unfiltered request.
    ui.handle.restore(url("until_date=2026-01-01T00:00:00Z"));
    await flush();
    gridFilters = ui.target.querySelector(
      '[data-testid="search-grid-filters"]',
    );
    assert.ok(gridFilters);
    assert.equal(calls.length, 4);
    assert.equal(
      gridFilters.querySelector('[data-search-grid-filter="until_date"]').value,
      "2026-01-01T00:00:00Z",
    );
    button(ui.target, "Clear all").click();
    await flush();
    assert.equal(ui.handle.currentUrl.search, "");
    assert.equal(calls.length, 5);
    assert.equal(calls[4]?.searchParams.get("limit"), "50");
    assert.equal(calls[4]?.searchParams.get("offset"), "0");
    assert.equal(calls[4]?.searchParams.has("until_date"), false);
    assert.doesNotMatch(ui.target.textContent, /Additional URL filters/);
  } finally {
    await ui.destroy();
  }
});

void test("mounted malformed and unsupported URL conditions block Search until Clear all", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(response());
  };
  for (const invalid of [
    "issues=any,1",
    "reviewer_ids=bad",
    "execution_metadata=broken",
    "from_date=2026-02-30T00:00:00Z",
    "from_date=2026-01-01T00:00:00.0000001Z",
    "artefact_is_archived=bad",
    "test_result_statuses=BAD",
    "test_execution_statuses=BAD",
    "families=unknown",
    "execution_is_latest=maybe",
    "unknown=blocked",
  ]) {
    const callsBefore = calls.length;
    const ui = mounted(invalid);
    try {
      await flush();
      assert.match(
        ui.target.querySelector('[role="alert"]')?.textContent ?? "",
        /Search not applied/,
      );
      button(ui.target, "Search").click();
      await flush();
      assert.match(
        ui.target.querySelector('[role="alert"]')?.textContent ?? "",
        /No request was sent/,
      );
      const original = new URLSearchParams(invalid);
      for (const [key, value] of original)
        assert.equal(ui.handle.currentUrl.searchParams.get(key), value);
      assert.equal(calls.length, callsBefore, invalid);
      button(ui.target, "Clear all").click();
      await flush();
      assert.equal(ui.target.querySelector('[role="alert"]'), null);
      assert.equal(calls.length, callsBefore + 1);
      assert.equal(calls.at(-1)?.searchParams.get("limit"), "50");
      assert.equal(calls.at(-1)?.searchParams.has("artefacts"), false);
    } finally {
      await ui.destroy();
    }
  }
});

void test("Latest boolean URL filters validate and reach the Search API", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(response());
  };
  const ui = mounted("execution_is_latest=false");
  try {
    await flush();
    assert.equal(ui.target.querySelector('[role="alert"]'), null);
    assert.equal(calls.length, 1);
    assert.equal(calls[0]?.searchParams.get("execution_is_latest"), "false");
    assert.equal(
      ui.handle.currentUrl.searchParams.get("execution_is_latest"),
      "false",
    );

    ui.handle.restore(url("execution_is_latest=maybe"));
    await flush();
    assert.match(
      ui.target.querySelector('[role="alert"]')?.textContent ?? "",
      /Invalid execution_is_latest/,
    );
    assert.equal(calls.length, 1, "malformed latest values do not fetch");

    button(ui.target, "Clear all").click();
    await flush();
    assert.equal(
      ui.handle.currentUrl.searchParams.has("execution_is_latest"),
      false,
    );
    assert.equal(
      calls.length,
      2,
      "Clear all starts the unfiltered recent query",
    );
    assert.equal(calls[1]?.searchParams.get("offset"), "0");
    assert.equal(calls[1]?.searchParams.get("limit"), "50");
  } finally {
    await ui.destroy();
  }
});

void test("mounted sub-microsecond lower bounds visibly block without fetching, and representable bounds retain exact microsecond ordering", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(response());
  };
  const unrepresentable = "2026-01-01T00:00:00.0000001Z";
  const ui = mounted(`from_date=${unrepresentable}`);
  try {
    await flush();
    const alert = ui.target.querySelector('[role="alert"]');
    assert.match(alert?.textContent ?? "", /Invalid from_date:.*microsecond/);
    assert.match(alert?.textContent ?? "", /No request was sent/);
    assert.equal(calls.length, 0);
    button(ui.target, "Search").click();
    await flush();
    assert.equal(
      ui.handle.currentUrl.searchParams.get("from_date"),
      unrepresentable,
    );
    assert.equal(
      calls.length,
      0,
      "Search cannot replace an invalid lower bound with a truncated or unfiltered request",
    );

    ui.handle.restore(
      url(
        "from_date=2026-01-01T00:00:00.000001Z&until_date=2026-01-01T00:00:00.000000Z",
      ),
    );
    await flush();
    assert.match(
      ui.target.querySelector('[role="alert"]')?.textContent ?? "",
      /Invalid date range/,
    );
    assert.equal(
      calls.length,
      0,
      "six-digit inverted bounds must not collapse to the same millisecond",
    );

    ui.handle.restore(
      url(
        "from_date=2026-01-01T00:00:00.000001Z&until_date=2026-01-01T00:00:00.000002000Z",
      ),
    );
    await flush();
    assert.equal(ui.target.querySelector('[role="alert"]'), null);
    assert.equal(calls.length, 1);
    assert.equal(
      calls[0].searchParams.get("from_date"),
      "2026-01-01T00:00:00.000001Z",
    );
    assert.equal(
      calls[0].searchParams.get("until_date"),
      "2026-01-01T00:00:00.000002000Z",
    );
  } finally {
    await ui.destroy();
  }
});

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
    for (const label of ["Search", "Clear all", "Reset table view"])
      assert.ok(button(ui.target, label).classList.contains("dense"), label);
    assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 0);
    assert.doesNotMatch(ui.target.textContent, /\+ Add filter/);
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
    assert.match(
      ui.target.textContent,
      /1 matching test results on the server/,
    );
    assert.equal(
      calls.length,
      1,
      "the initial recent page is loaded unfiltered",
    );
    assert.equal(calls[0].pathname, "/v1/test-results/search-page");
    assert.equal(calls[0].searchParams.get("limit"), "50");
    assert.equal(calls[0].searchParams.get("offset"), "0");
    let gridFilters = ui.target.querySelector(
      '[data-testid="search-grid-filters"]',
    );
    assert.ok(gridFilters);
    gridFilters.querySelector("summary")?.click();
    await flush();
    await enter(
      gridFilters,
      '[data-search-grid-filter="artefacts"]',
      "one, two",
    );
    assert.equal(calls.length, 1, "draft edits do not fetch before applying");
    assert.match(ui.target.textContent, /Changes not applied/);
    button(ui.target, "Search").click();
    await flush();
    assert.deepEqual(calls[1]?.searchParams.getAll("artefacts"), [
      "one",
      "two",
    ]);
    assert.equal(ui.handle.history.length, 2);
    assert.ok(
      ui.target.querySelector(".sv-grid-root"),
      "actual SvGrid must mount",
    );
    assert.match(
      ui.target.textContent,
      /1 matching test results on the server/,
    );
    assert.match(ui.target.textContent, /Scroll to load\s+more/);
    for (const text of [
      "example artefact",
      "Configured-route",
      "alpha",
      "No",
      "FAILED",
      "Yes",
      "case 1",
      "category 1",
      "FAILED",
      "1.2",
      "stable",
      "test lab",
      "smoke",
      "template 1",
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
    assert.match(
      gridFilters.querySelector('[aria-label="Selected details"]')
        ?.textContent ?? "",
      /one.*two/,
    );
    assert.deepEqual(calls.at(-1)?.searchParams.getAll("artefacts"), [
      "one",
      "two",
    ]);
    button(ui.target, "Clear all").click();
    await flush();
    assert.ok(ui.target.querySelector(".sv-grid-root"));
    assert.doesNotMatch(ui.target.textContent, /Choose at least one filter/);
    assert.equal(
      calls.length,
      5,
      "Clear all reloads unfiltered recent results",
    );
    assert.equal(calls[4]?.searchParams.get("limit"), "50");
    assert.equal(calls[4]?.searchParams.has("artefacts"), false);
  } finally {
    await ui.destroy();
  }
});

void test("dynamic list editors keep typed queries pending until exact values are explicitly added", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(response([1]));
  };
  const ui = mounted();
  try {
    await flush();
    let gridFilters = ui.target.querySelector(
      '[data-testid="search-grid-filters"]',
    );
    assert.ok(gridFilters);
    gridFilters.querySelector("summary")?.click();
    await flush();
    let input = /** @type {import('happy-dom').HTMLInputElement | null} */ (
      gridFilters.querySelector('[data-search-grid-filter="artefacts"]')
    );
    assert.ok(input);

    await typeOnly(input, "one, two");
    assert.equal(
      input.value,
      "one, two",
      "the suggestion query stays editable",
    );
    assert.deepEqual(selectedValues(gridFilters, "artefacts"), []);
    assert.deepEqual(ui.handle.currentUrl.searchParams.getAll("artefacts"), []);
    assert.equal(calls.length, 1, "typing does not select or search values");

    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls.at(-1)?.searchParams.has("artefacts"), false);
    gridFilters = ui.target.querySelector(
      '[data-testid="search-grid-filters"]',
    );
    assert.ok(gridFilters);
    chip(ui.target, "Artefact").click();
    await flush();
    input = gridFilters.querySelector('[data-search-grid-filter="artefacts"]');
    assert.ok(input);
    for (const value of ["one", "two"]) {
      await typeOnly(input, value);
      button(panel(ui.target), "Add exact value").click();
      await flush();
    }
    assert.deepEqual(selectedValues(gridFilters, "artefacts"), ["one", "two"]);
    button(ui.target, "Search").click();
    await flush();
    assert.deepEqual(ui.handle.currentUrl.searchParams.getAll("artefacts"), [
      "one",
      "two",
    ]);
    assert.deepEqual(calls.at(-1)?.searchParams.getAll("artefacts"), [
      "one",
      "two",
    ]);
    assert.equal(
      gridFilters.querySelector("datalist"),
      null,
      "lookup editor selections are not populated from local result blocks",
    );
  } finally {
    await ui.destroy();
  }
});

void test("active column-header menus open with focus and Escape returns to each filter trigger", async () => {
  globalThis.fetch = () => Promise.resolve(response());
  for (const label of ["Created", "Artefact", "Test case"]) {
    for (const mode of ["pointer", "Enter"]) {
      const ui = mounted();
      try {
        await flush();
        const trigger = chip(ui.target, label);
        trigger.focus();
        // Native button activation by Enter produces the same click as pointer.
        if (mode === "Enter") {
          trigger.dispatchEvent(
            new browser.KeyboardEvent("keydown", {
              key: "Enter",
              bubbles: true,
              cancelable: true,
            }),
          );
          await flush();
        }
        if (trigger.getAttribute("aria-expanded") !== "true") trigger.click();
        await flush();
        const input = panel(ui.target).querySelector("input");
        assert.ok(input);
        assert.ok(
          browser.document.activeElement === input,
          `${mode} must focus ${label} after opening`,
        );
        browser.document.dispatchEvent(
          new browser.KeyboardEvent("keydown", {
            key: "Escape",
            bubbles: true,
            cancelable: true,
          }),
        );
        await flush();
        assert.equal(
          ui.target.querySelector(".menu-anchor:not([hidden])"),
          null,
        );
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
    const trigger = chip(ui.target, "Result status");
    trigger.click();
    await flush();
    const content = panel(ui.target);
    const overlay = /** @type {import('happy-dom').HTMLElement | null} */ (
      content.parentElement
    );
    assert.ok(overlay);
    // Happy DOM has no layout; supply the real QA geometry and verify the
    // resulting viewport constraints, leaving scrollbar reachability to browser QA.
    content.getBoundingClientRect = () => new browser.DOMRect(0, 0, 320, 375);
    overlay.getBoundingClientRect = () => new browser.DOMRect(0, 0, 320, 375);
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
        top >= 8 && top + Math.min(375, maxHeight) <= height - 8,
        `${width}x${height} overlay must fit vertically`,
      );
      assert.ok(
        left >= 8 && left + 320 <= width - 8,
        `${width}x${height} overlay must fit horizontally`,
      );
      assert.ok(
        maxHeight <= height - 16,
        "menu height is constrained to the visible viewport",
      );
    }
    browser.happyDOM.setViewport({ width: 800, height: 720 });
    anchorY = 600;
    browser.dispatchEvent(new browser.Event("resize"));
    await flush();
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

void test("every supported filter opens from its own column header with no condition picker or chips", async () => {
  await app.userStore.refresh(() =>
    Promise.resolve(json({ id: 419, teams: [], is_admin: false })),
  );
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    calls.push(request);
    if (request.pathname.endsWith("/execution-metadata"))
      return Promise.resolve(json({ execution_metadata: {} }));
    return Promise.resolve(response());
  };
  const ui = mounted();
  try {
    await flush();
    const headers = [
      ["Created", "from_date"],
      ["Family", "families"],
      ["Artefact", "artefacts"],
      ["Stage", "artefact_stages"],
      ["Archived", "artefact_is_archived"],
      ["Test case", "test_cases"],
      ["Execution Status", "test_execution_statuses"],
      ["Rerun Requested", "rerun_is_requested"],
      ["Latest Execution", "execution_is_latest"],
      ["Result status", "test_result_statuses"],
      ["Track", "artefact_tracks"],
      ["Version", "artefact_versions"],
      ["Environment", "environments"],
      ["Test plan", "test_plans"],
      ["Template ID", "template_ids"],
      ["Issues", "issues"],
      ["Reviewers", "reviewer_ids"],
      ["Execution Metadata", "execution_metadata"],
    ];
    assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 0);
    assert.equal(ui.target.querySelector(".condition-popover"), null);
    assert.doesNotMatch(ui.target.textContent, /\+ Add filter/);
    for (const [label, field] of headers) {
      const trigger = chip(ui.target, label);
      trigger.click();
      await flush();
      assert.equal(panel(ui.target).dataset.searchGridMenu, field);
      assert.equal(trigger.getAttribute("aria-expanded"), "true");
      trigger.click();
      await flush();
    }
    const dateMenu = ui.target.querySelector(
      '[data-search-grid-menu="from_date"]',
    );
    assert.ok(
      dateMenu?.querySelector('[data-search-grid-filter="until_date"]'),
    );
    assert.ok(
      ui.target.querySelector('button[aria-label="Filter Latest Execution"]'),
    );
    assert.equal(
      calls.filter((call) =>
        call.pathname.endsWith("/test-results/search-page"),
      ).length,
      1,
    );
    assert.equal(
      calls.filter((call) => call.pathname.endsWith("/execution-metadata"))
        .length,
      1,
      "metadata suggestions load when that column menu opens",
    );
  } finally {
    await ui.destroy();
    await app.userStore.refresh(() => Promise.resolve(json(null)));
  }
});

void test("high-cardinality grid fields can add exact values without waiting for lookup suggestions", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(response());
  };
  const ui = mounted();
  try {
    await flush();
    const gridFilters = ui.target.querySelector(
      '[data-testid="search-grid-filters"]',
    );
    assert.ok(gridFilters);
    gridFilters.querySelector("summary")?.click();
    await flush();
    await enter(
      gridFilters,
      '[data-search-grid-filter="artefacts"]',
      " first artefact, second+artefact, first artefact, ",
    );
    await enter(
      gridFilters,
      '[data-search-grid-filter="environments"]',
      " first environment, second+environment ",
    );
    await new Promise((resolve) => setTimeout(resolve, 300));
    assert.equal(
      calls.length,
      1,
      "explicit exact-value additions cancel pending lookup queries",
    );
    assert.match(ui.target.textContent, /Changes not applied/);
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls.length, 2);
    assert.deepEqual(calls[1].searchParams.getAll("artefacts"), [
      "first artefact",
      "second+artefact",
    ]);
    assert.deepEqual(calls[1].searchParams.getAll("environments"), [
      "first environment",
      "second+environment",
    ]);
    assert.doesNotMatch(ui.target.textContent, /Changes not applied/);
    assert.match(ui.target.textContent, /Results for applied query/);
  } finally {
    await ui.destroy();
  }
});

void test("grid filter drafts never filter loaded blocks; Search replaces the query and restarts at row zero", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(response([1, 2], 20, 2, 2));
  };
  const ui = mounted("artefacts=old&test_cases=applied&limit=2&offset=2");
  try {
    await flush();
    let gridFilters = ui.target.querySelector(
      '[data-testid="search-grid-filters"]',
    );
    assert.ok(gridFilters);
    gridFilters.querySelector("summary")?.click();
    await flush();
    await enter(
      gridFilters,
      '[data-search-grid-filter="artefacts"]',
      "new, second",
    );
    await enter(gridFilters, '[data-search-grid-filter="test_cases"]', "");
    await enter(gridFilters, '[data-search-grid-filter="environments"]', "lab");
    assert.equal(calls.length, 1);
    assert.equal(ui.handle.history.length, 1);
    assert.match(ui.target.textContent, /Changes not applied/);
    assert.match(ui.target.textContent, /Results for previous query/);
    assert.match(ui.target.textContent, /case 1/);
    assert.deepEqual(selectedValues(gridFilters, "artefacts"), [
      "new",
      "second",
    ]);
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls.length, 2);
    assert.deepEqual(calls[1].searchParams.getAll("artefacts"), [
      "new",
      "second",
    ]);
    assert.equal(calls[1].searchParams.get("environments"), "lab");
    assert.equal(calls[1].searchParams.has("test_cases"), false);
    assert.equal(calls[1].searchParams.get("offset"), "0");
    assert.doesNotMatch(ui.target.textContent, /Changes not applied/);
    ui.handle.restore(url("artefacts=old&test_cases=applied&limit=2&offset=2"));
    await flush();
    gridFilters = ui.target.querySelector(
      '[data-testid="search-grid-filters"]',
    );
    assert.ok(gridFilters);
    assert.deepEqual(selectedValues(gridFilters, "artefacts"), ["old"]);
    assert.doesNotMatch(ui.target.textContent, /Changes not applied/);
    assert.equal(ui.handle.currentUrl.searchParams.has("offset"), false);
  } finally {
    await ui.destroy();
  }
});

void test.skip("deferred: issue lookup menus preserve pending selection drafts", async () => {
  let resultCalls = 0;
  globalThis.fetch = (input) => {
    if (
      new URL(input instanceof Request ? input.url : input).pathname.endsWith(
        "/test-results/search-page",
      )
    )
      resultCalls++;
    return Promise.resolve(response());
  };
  const ui = mounted("issues=41");
  const outside = browser.document.createElement("button");
  outside.textContent = "Outside control";
  browser.document.body.append(outside);
  try {
    await flush();
    const trigger = chip(ui.target, "Issues");
    trigger.click();
    await flush();
    const input = await enter(ui.target, 'input[name="issues"]', "pending");
    assert.doesNotMatch(ui.target.textContent, /Changes not applied/);
    outside.focus();
    outside.click();
    await flush();
    assert.equal(ui.target.querySelector(".menu-anchor:not([hidden])"), null);
    assert.equal(browser.document.activeElement, outside);
    trigger.click();
    await flush();
    assert.equal(ui.target.querySelector('input[name="issues"]'), input);
    assert.equal(input.value, "pending", "dismissal preserves lookup text");
    assert.match(hydratedSelection(ui.target, "issues"), /#41/);
    assert.equal(resultCalls, 1);
  } finally {
    outside.remove();
    await ui.destroy();
  }
});

void test("issue/reviewer/metadata editors share the draft and preserve pending input", async () => {
  globalThis.fetch = (input) => {
    const path = new URL(input instanceof Request ? input.url : input).pathname;
    if (path.endsWith("/execution-metadata"))
      return Promise.resolve(json({ category: ["value"], next: ["value"] }));
    return Promise.resolve(response());
  };

  const issueNavigation = deferred();
  /** @type {URL | undefined} */
  let issueTarget;
  const issueUi = mounted("issues=41", (next) => {
    issueTarget = next;
    return issueNavigation.promise;
  });
  try {
    await flush();
    await chooseFilter(issueUi.target, "Issues");
    await enter(issueUi.target, 'input[name="issues"]', "42");
    button(panel(issueUi.target), "Add exact IDs").click();
    await flush();
    await enter(issueUi.target, 'input[name="issues"]', "99");
    button(issueUi.target, "Search").click();
    await flush();

    const issueMenu = panel(issueUi.target);
    const issueQuery = issueMenu.querySelector('input[name="issues"]');
    assert.equal(issueUi.handle.currentUrl.searchParams.get("issues"), "41");
    assert.deepEqual(issueTarget?.searchParams.getAll("issues"), ["41", "42"]);
    assert.equal(issueQuery?.disabled, true);
    assert.equal(button(issueMenu, "Add exact IDs").disabled, true);
    assert.equal(
      issueMenu.querySelector('button[aria-label="Remove selected 41"]')
        ?.disabled,
      true,
    );
    assert.equal(
      issueMenu.querySelector('input[type="radio"][value="any"]')?.disabled,
      true,
    );
    issueQuery.value = "100";
    issueQuery.dispatchEvent(new browser.Event("input", { bubbles: true }));
    button(issueMenu, "Add exact IDs").click();
    await flush();
    assert.ok(issueTarget);
    assert.deepEqual(issueTarget.searchParams.getAll("issues"), ["41", "42"]);
  } finally {
    issueNavigation.resolve(response());
    await flush();
    await issueUi.destroy();
  }
  assert.deepEqual(issueUi.handle.currentUrl.searchParams.getAll("issues"), [
    "41",
    "42",
  ]);

  const metadata = `${Buffer.from("category").toString("base64")}:${Buffer.from("value").toString("base64")}`;
  const metadataNavigation = deferred();
  /** @type {URL | undefined} */
  let metadataTarget;
  const metadataUi = mounted(`execution_metadata=${metadata}`, (next) => {
    metadataTarget = next;
    return metadataNavigation.promise;
  });
  try {
    await flush();
    await chooseFilter(metadataUi.target, "Metadata");
    await enter(metadataUi.target, 'input[name="metadata-category"]', "next");
    await enter(metadataUi.target, 'input[name="metadata-value"]', "value");
    button(panel(metadataUi.target), "Add pair").click();
    await flush();
    button(metadataUi.target, "Search").click();
    await flush();

    const metadataMenu = panel(metadataUi.target);
    assert.equal(
      metadataUi.handle.currentUrl.searchParams.getAll("execution_metadata")
        .length,
      1,
    );
    assert.equal(
      metadataTarget?.searchParams.getAll("execution_metadata").length,
      2,
    );
    assert.equal(
      metadataMenu.querySelector('input[name="metadata-category"]')?.disabled,
      true,
    );
    assert.equal(
      metadataMenu.querySelector('input[name="metadata-value"]')?.disabled,
      true,
    );
    assert.equal(button(metadataMenu, "Add pair").disabled, true);
    assert.equal(
      metadataMenu.querySelector('button[aria-label^="Remove metadata"]')
        ?.disabled,
      true,
    );
  } finally {
    metadataNavigation.resolve(response());
    await flush();
    await metadataUi.destroy();
  }
  assert.equal(
    metadataUi.handle.currentUrl.searchParams.getAll("execution_metadata")
      .length,
    2,
  );

  const blockedUi = mounted("issues=any,41");
  try {
    await flush();
    await chooseFilter(blockedUi.target, "Issues");
    const anyMode = /** @type {import('happy-dom').HTMLInputElement | null} */ (
      blockedUi.target.querySelector('input[type="radio"][value="any"]')
    );
    assert.ok(anyMode);
    assert.equal(anyMode.disabled, false);
    anyMode.click();
    await flush();
    assert.match(blockedUi.target.textContent, /Changes not applied/);
    button(blockedUi.target, "Search").click();
    await flush();
    assert.equal(blockedUi.handle.currentUrl.searchParams.get("issues"), "any");
    assert.doesNotMatch(blockedUi.target.textContent, /Search not applied/);
  } finally {
    await blockedUi.destroy();
  }
});

void test("repeated URL values hydrate grid filters and Clear all restarts recent results", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(response());
  };
  const long = "long-exact-artefact-name-".repeat(8);
  const applied = url(`artefacts=${long},second&artefacts=third`);
  const ui = mounted(applied.search.slice(1));
  try {
    await flush();
    let gridFilters = ui.target.querySelector(
      '[data-testid="search-grid-filters"]',
    );
    assert.ok(gridFilters);
    gridFilters.querySelector("summary")?.click();
    await flush();
    assert.deepEqual(selectedValues(gridFilters, "artefacts"), [
      long,
      "second",
      "third",
    ]);
    await enter(
      gridFilters,
      '[data-search-grid-filter="artefacts"]',
      "transient",
    );
    ui.handle.restore(url("test_cases=restored"));
    await flush();
    gridFilters = ui.target.querySelector(
      '[data-testid="search-grid-filters"]',
    );
    assert.ok(gridFilters);
    assert.deepEqual(selectedValues(gridFilters, "test_cases"), ["restored"]);
    ui.handle.restore(applied);
    await flush();
    gridFilters = ui.target.querySelector(
      '[data-testid="search-grid-filters"]',
    );
    assert.ok(gridFilters);
    assert.deepEqual(selectedValues(gridFilters, "artefacts"), [
      long,
      "second",
      "third",
    ]);
    assert.equal(calls.length, 3);
    button(ui.target, "Clear all").click();
    await flush();
    gridFilters = ui.target.querySelector(
      '[data-testid="search-grid-filters"]',
    );
    assert.ok(gridFilters);
    assert.equal(ui.handle.history.at(-1)?.search, "");
    assert.equal(calls.length, 4);
    assert.equal(calls[3]?.searchParams.get("limit"), "50");
    assert.equal(calls[3]?.searchParams.has("artefacts"), false);
    await enter(gridFilters, '[data-search-grid-filter="test_cases"]', "one");
    button(ui.target, "Search").click();
    await flush();
    gridFilters = ui.target.querySelector(
      '[data-testid="search-grid-filters"]',
    );
    assert.ok(gridFilters);
    await enter(gridFilters, '[data-search-grid-filter="test_cases"]', "");
    assert.match(ui.target.textContent, /clear the previous query/);
    assert.match(ui.target.textContent, /Results for previous query/);
    assert.equal(calls.length, 5);
    button(ui.target, "Search").click();
    await flush();
    gridFilters = ui.target.querySelector(
      '[data-testid="search-grid-filters"]',
    );
    assert.ok(gridFilters);
    assert.equal(ui.handle.history.at(-1)?.search, "");
    assert.ok(ui.target.querySelector(".sv-grid-root"));
    assert.equal(calls.length, 6);
    assert.equal(calls[5]?.searchParams.get("limit"), "50");
    assert.equal(calls[5]?.searchParams.has("artefacts"), false);
    await enter(
      gridFilters,
      '[data-search-grid-filter="test_cases"]',
      "draft only",
    );
    button(ui.target, "Clear all").click();
    await flush();
    assert.equal(
      calls.length,
      7,
      "clearing drafts on an already-empty URL reapplies the recent page too",
    );
  } finally {
    await ui.destroy();
  }
});

void test("infinite blocks map exact ranges and repeat canonical filters while count settles the end", async () => {
  /** @type {{url: URL; options: RequestInit}[]} */
  const calls = [];
  globalThis.fetch = (input, options = {}) => {
    const request = new URL(input instanceof Request ? input.url : input);
    calls.push({ url: request, options });
    const offset = Number(request.searchParams.get("offset"));
    const limit = Number(request.searchParams.get("limit"));
    return Promise.resolve(
      json({
        count:
          request.searchParams.get("include_count") === "true" ? 125 : null,
        limit,
        offset,
        rows: Array.from(
          { length: Math.min(limit, 125 - offset) },
          (_, index) => tableResult(offset + index + 1),
        ),
      }),
    );
  };
  /** @type {import("../src/lib/stores/test-results-search.svelte").TestResultsSearchStore} */
  const store = new app.TestResultsSearchStore();
  const metadata = `${Buffer.from("build").toString("base64")}:${Buffer.from("stable").toString("base64")}`;
  const fullQuery = new URLSearchParams([
    ["families", "snap"],
    ["test_result_statuses", "FAILED"],
    ["test_execution_statuses", "IN_PROGRESS"],
    ["artefacts", "one,two"],
    ["artefact_versions", "1,2"],
    ["artefact_tracks", "stable"],
    ["environments", "lab"],
    ["test_cases", "case"],
    ["test_plans", "plan"],
    ["artefact_stages", ""],
    ["artefact_is_archived", "false"],
    ["rerun_is_requested", "true"],
    ["execution_is_latest", "false"],
    ["issues", "41,42"],
    ["reviewer_ids", "none"],
    ["execution_metadata", metadata],
    ["template_ids", "template"],
    ["from_date", "2026-01-01T00:00:00Z"],
    ["until_date", "2026-01-31T23:59:59Z"],
  ]);
  try {
    await store.search(
      app.parseSearchPage(fullQuery, families),
      families,
      "/custom/base",
    );
    const controller = store.controller;
    assert.ok(controller);
    const initialState = controller.getState();
    assert.equal(calls[0]?.url.searchParams.get("offset"), "0");
    assert.equal(calls[0]?.url.searchParams.get("limit"), "50");
    assert.equal(calls[0]?.url.searchParams.get("include_count"), "true");
    assert.deepEqual(calls[0]?.url.searchParams.getAll("artefacts"), [
      "one",
      "two",
    ]);
    assert.equal(
      calls[0]?.url.searchParams.get("test_result_statuses"),
      "FAILED",
    );
    assert.equal(initialState.rowCount, 125);
    assert.equal(initialState.lastRowKnown, true);

    controller.setViewport(50, 99);
    await flush();
    controller.setViewport(100, 124);
    await flush();
    const loadedState = controller.getState();
    assert.deepEqual(
      calls.map(({ url: request }) => [
        request.searchParams.get("offset"),
        request.searchParams.get("limit"),
      ]),
      [
        ["0", "50"],
        ["50", "50"],
        ["100", "50"],
      ],
    );
    assert.deepEqual(
      calls.map(({ url: request }) =>
        request.searchParams.get("include_count"),
      ),
      ["true", "false", "false"],
    );
    assert.ok(
      calls.every(
        ({ url: request }) =>
          request.searchParams.getAll("artefacts").join(",") === "one,two" &&
          request.searchParams.get("test_result_statuses") === "FAILED" &&
          request.searchParams.getAll("artefact_versions").join(",") ===
            "1,2" &&
          request.searchParams.get("artefact_tracks") === "stable" &&
          request.searchParams.get("environments") === "lab" &&
          request.searchParams.get("test_cases") === "case" &&
          request.searchParams.get("test_plans") === "plan" &&
          request.searchParams.get("families") === "snap" &&
          request.searchParams.get("test_execution_statuses") ===
            "IN_PROGRESS" &&
          request.searchParams.getAll("artefact_stages").join(",") === "" &&
          request.searchParams.get("artefact_is_archived") === "false" &&
          request.searchParams.get("rerun_is_requested") === "true" &&
          request.searchParams.get("execution_is_latest") === "false" &&
          request.searchParams.getAll("issues").join(",") === "41,42" &&
          request.searchParams.get("reviewer_ids") === "none" &&
          request.searchParams.get("execution_metadata") === metadata &&
          request.searchParams.get("template_ids") === "template" &&
          request.searchParams.get("from_date") === "2026-01-01T00:00:00Z" &&
          request.searchParams.get("until_date") === "2026-01-31T23:59:59Z",
      ),
      "every block carries all applied column conditions",
    );
    assert.equal(loadedState.rows.length, 125);
    assert.equal(loadedState.rows[124]?.id, 125);
    assert.equal(controller.getCacheState().length, 3);
    assert.equal(store.rowModel && "setFilter" in store.rowModel, false);
    assert.equal(store.rowModel && "setSort" in store.rowModel, false);
  } finally {
    store.cancel();
  }
});

void test("infinite search bounds its cache, aborts old blocks, and ignores stale replies", async () => {
  const stale = deferred();
  /** @type {AbortSignal | undefined} */
  let staleSignal;
  globalThis.fetch = (input, options = {}) => {
    const request = new URL(input instanceof Request ? input.url : input);
    if (
      request.pathname.endsWith("/test-results/search-page") &&
      request.searchParams.get("artefacts") === "old" &&
      request.searchParams.get("offset") === "50"
    ) {
      staleSignal = options.signal;
      return stale.promise;
    }
    const offset = Number(request.searchParams.get("offset"));
    const limit = Number(request.searchParams.get("limit"));
    const id =
      request.searchParams.get("artefacts") === "new" ? 900 : offset + 1;
    return Promise.resolve(
      json({
        count:
          request.searchParams.get("include_count") === "true" ? 5000 : null,
        limit,
        offset,
        rows: Array.from({ length: limit }, (_, index) =>
          tableResult(id + index),
        ),
      }),
    );
  };
  /** @type {import("../src/lib/stores/test-results-search.svelte").TestResultsSearchStore} */
  const store = new app.TestResultsSearchStore();
  try {
    await store.search(
      app.parseSearchPage(url("artefacts=old").searchParams, families),
      families,
      "/custom/base",
    );
    const previous = store.controller;
    assert.ok(previous);
    previous.setViewport(50, 99);
    await flush();
    assert.ok(staleSignal);
    assert.equal(staleSignal.aborted, false);

    await store.search(
      app.parseSearchPage(url("artefacts=new").searchParams, families),
      families,
      "/custom/base",
    );
    assert.equal(staleSignal.aborted, true);
    stale.resolve(response([2], 5000));
    await flush();
    assert.equal(store.responseQuery?.filters.artefacts[0], "new");
    assert.equal(store.controller?.getRows()[0]?.id, 900);

    const activeController = store.controller;
    assert.ok(activeController);
    for (const start of [50, 100, 150, 200, 250, 300, 350, 400, 450, 500]) {
      activeController.setViewport(start, start + 49);
      await flush();
    }
    assert.ok(
      activeController
        .getCacheState()
        .filter((block) => block.status === "loaded").length <=
        app.SEARCH_MAX_BLOCKS,
      "visited blocks stay under the configured cache bound",
    );
  } finally {
    store.cancel();
  }
});

void test("legacy page URLs normalize without losing filters and history changes restart at offset zero", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    calls.push(request);
    const id = request.searchParams.get("artefacts") === "two" ? 2 : 1;
    return Promise.resolve(response([id], 1, 50, 0));
  };
  const ui = mounted("artefacts=one&limit=2&offset=80");
  try {
    await flush();
    assert.equal(ui.handle.currentUrl.searchParams.get("artefacts"), "one");
    assert.equal(ui.handle.currentUrl.searchParams.has("limit"), false);
    assert.equal(ui.handle.currentUrl.searchParams.has("offset"), false);
    assert.equal(calls.length, 1);
    assert.equal(calls[0]?.searchParams.get("offset"), "0");
    assert.equal(calls[0]?.searchParams.get("limit"), "50");
    assert.deepEqual(gridCases(ui.target), ["case 1"]);

    ui.handle.restore(url("artefacts=two&limit=3&offset=900"));
    await flush();
    assert.equal(calls.length, 2);
    assert.equal(calls[1]?.searchParams.get("artefacts"), "two");
    assert.equal(calls[1]?.searchParams.get("offset"), "0");
    assert.deepEqual(gridCases(ui.target), ["case 2"]);

    // Back/forward restoration reuses filters but not a stale grid range.
    ui.handle.restore(url("artefacts=one&limit=1&offset=7"));
    await flush();
    assert.equal(calls.length, 3);
    assert.equal(calls[2]?.searchParams.get("artefacts"), "one");
    assert.equal(calls[2]?.searchParams.get("offset"), "0");
    assert.deepEqual(gridCases(ui.target), ["case 1"]);
  } finally {
    await ui.destroy();
  }
});

void test("view is presentation-only in query identity and never appears in API parameters", () => {
  const params = url(
    "artefacts=one&artefacts=two&limit=2&offset=2&view=invalid",
  ).searchParams;
  const applied = app.parseSearchPage(params, families);
  assert.deepEqual(applied.problems, []);
  assert.equal(
    app
      .searchParams(applied.filters, applied.limit, applied.offset)
      .has("view"),
    false,
  );
  assert.equal(app.searchQueryString(params), "artefacts=one&artefacts=two");
  params.set("view", "different");
  assert.equal(app.searchQueryString(params), "artefacts=one&artefacts=two");
  params.append("unsupported", "still blocks");
  assert.match(
    app.parseSearchPage(params, families).problems[0],
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

void test("shared URL preserves column visibility but ignores local sort/filter state", async () => {
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
    assert.deepEqual(gridCases(ui.target), ["case 3", "case 2", "case 1"]);
    assert.equal(
      ui.target.querySelector('th[data-svgrid-header-col="version"]'),
      null,
    );
    assert.equal(ui.target.querySelector(".sv-grid-global-filter"), null);
    assert.equal(ui.target.querySelector(".sv-grid-filter-button"), null);
    assert.equal(ui.target.querySelector(".sv-grid-header-icon-hint"), null);
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
    assert.equal(calls, 1);
    assert.equal(ui.handle.replacements.length, 0);
  } finally {
    await ui.destroy();
  }
});

void test("view-only history changes preserve grid-filter drafts and grid identity", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(response([2, 1]));
  };
  const ui = mounted("artefacts=one&artefacts=two");
  try {
    await flush();
    const filters = ui.target.querySelector(
      '[data-testid="search-grid-filters"]',
    );
    assert.ok(filters);
    filters.querySelector("summary")?.click();
    await flush();
    await enter(filters, '[data-search-grid-filter="test_cases"]', "confirmed");
    const editor = /** @type {HTMLInputElement | null} */ (
      filters.querySelector('[data-search-grid-filter="artefacts"]')
    );
    assert.ok(editor);
    await typeOnly(editor, "unconfirmed");
    editor.focus();
    assert.ok(browser.document.activeElement === editor);
    const grid = ui.target.querySelector(".sv-grid-root");
    const view = app.encodeView({
      hiddenColumns: ["track"],
    });
    ui.handle.restore(url(`artefacts=one&artefacts=two&view=${view}`));
    await flush();
    assert.equal(
      filters.querySelector('[data-search-grid-filter="artefacts"]'),
      editor,
    );
    assert.equal(editor.value, "unconfirmed");
    assert.ok(
      browser.document.activeElement === editor,
      "view-only navigation preserves focus in the draft editor",
    );
    assert.deepEqual(selectedValues(filters, "test_cases"), ["confirmed"]);
    assert.match(ui.target.textContent, /Changes not applied/);
    assert.equal(ui.target.querySelector(".sv-grid-root"), grid);
    assert.deepEqual(gridCases(ui.target), ["case 2", "case 1"]);
    ui.handle.restore(url("artefacts=one&artefacts=two"));
    await flush();
    assert.ok(browser.document.activeElement === editor);
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
      const view = app.encodeView({ hiddenColumns: ["track"] });
      ui.handle.restore(url(`artefacts=one&view=${view}`));
      await flush();
      assert.equal(calls, before);
      assert.ok(signals.length);
      assert.ok(signals.every((signal) => !signal.aborted));
      pending.resolve(auth ? json(null) : response([2, 1]));
      await flush();
      if (auth) assert.match(ui.target.textContent, /need to be logged in/);
      else assert.deepEqual(gridCases(ui.target), ["case 2", "case 1"]);
    } finally {
      await ui.destroy();
    }
  }
});

void test("history filter changes restart at row zero without stale rows while view-only changes reuse blocks", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    calls.push(request);
    const id = request.searchParams.get("artefacts") === "new" ? 9 : 1;
    return Promise.resolve(response([id], 1, 50, 0));
  };
  const ui = mounted("artefacts=old");
  try {
    await flush();
    assert.deepEqual(gridCases(ui.target), ["case 1"]);
    ui.handle.restore(
      url(`artefacts=old&view=${app.encodeView({ hiddenColumns: ["track"] })}`),
    );
    await flush();
    assert.equal(
      calls.length,
      1,
      "presentation history does not refetch blocks",
    );
    ui.handle.restore(url("artefacts=new"));
    await flush();
    assert.equal(calls.length, 2);
    assert.equal(ui.handle.currentUrl.search, "?artefacts=new");
    assert.equal(ui.handle.replacements.length, 0);
    assert.equal(calls[1]?.searchParams.get("offset"), "0");
    assert.deepEqual(gridCases(ui.target), ["case 9"]);
    assert.equal(ui.target.textContent.includes("case 1"), false);
    button(ui.target, "Clear all").click();
    await flush();
    assert.equal(ui.handle.currentUrl.search, "");
    assert.equal(calls.length, 3);
    assert.equal(calls[2]?.searchParams.get("offset"), "0");
    assert.equal(calls[2]?.searchParams.get("limit"), "50");
    assert.equal(calls[2]?.searchParams.has("artefacts"), false);
  } finally {
    await ui.destroy();
  }
});

void test("column visibility survives Search and retry; Reset table view and Clear all remain independent", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(response([2, 1], 12, 2));
  };
  const view = app.encodeView({
    hiddenColumns: ["version"],
  });
  const ui = mounted(`artefacts=one&limit=2&view=${view}`);
  try {
    await flush();
    assert.deepEqual(gridCases(ui.target), ["case 2", "case 1"]);
    assert.equal(
      ui.target.querySelector('th[data-svgrid-header-col="version"]'),
      null,
    );
    const filters = ui.target.querySelector(
      '[data-testid="search-grid-filters"]',
    );
    assert.ok(filters);
    filters.querySelector("summary")?.click();
    await flush();
    await enter(filters, '[data-search-grid-filter="artefacts"]', "changed");
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls.length, 2);
    assert.equal(calls[1].searchParams.get("artefacts"), "changed");
    assert.equal(ui.handle.history.at(-1)?.searchParams.get("view"), view);
    assert.deepEqual(gridCases(ui.target), ["case 2", "case 1"]);
    // Identical explicit Search still re-applies the same server query.
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls.length, 3);
    assert.equal(calls[2].searchParams.get("artefacts"), "changed");
    assert.equal(ui.handle.history.at(-1)?.searchParams.get("view"), view);
    const grid = ui.target.querySelector(".sv-grid-root");
    button(ui.target, "Reset table view").click();
    await flush();
    assert.equal(calls.length, 3);
    assert.equal(ui.target.querySelector(".sv-grid-root"), grid);
    assert.equal(ui.handle.history.at(-1)?.searchParams.has("view"), false);
    assert.deepEqual(gridCases(ui.target), ["case 2", "case 1"]);
    assert.ok(ui.target.querySelector('th[data-svgrid-header-col="version"]'));
    ui.handle.restore(url(`artefacts=changed&view=${view}`));
    await flush();
    const beforeClear = calls.length;
    button(ui.target, "Clear all").click();
    await flush();
    assert.ok(calls.length > beforeClear);
    assert.equal(calls.at(-1)?.searchParams.get("limit"), "50");
    assert.equal(calls.at(-1)?.searchParams.has("artefacts"), false);
    assert.equal(ui.handle.history.at(-1)?.search, "");
    assert.ok(ui.target.querySelector(".sv-grid-root"));
    assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 0);
    assert.ok(calls.every((request) => !request.searchParams.has("view")));
  } finally {
    await ui.destroy();
  }
});

void test("malformed/oversized views and inapplicable column refs remain usable, and view-only URLs never fetch", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
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
      const before = calls.length;
      ui.handle.restore(url(`view=${view}&limit=2&offset=2`));
      await flush();
      assert.equal(calls.length, before + 1);
      assert.equal(calls.at(-1)?.searchParams.get("limit"), "50");
      assert.equal(calls.at(-1)?.searchParams.get("offset"), "0");
      assert.equal(calls.at(-1)?.searchParams.has("artefacts"), false);
      assert.equal(ui.handle.currentUrl.searchParams.has("limit"), false);
      assert.equal(ui.handle.currentUrl.searchParams.has("offset"), false);
      assert.doesNotMatch(ui.target.textContent, /Choose at least one filter/);
      const filters = ui.target.querySelector(
        '[data-testid="search-grid-filters"]',
      );
      assert.ok(filters);
      filters.querySelector("summary")?.click();
      await flush();
      await enter(filters, '[data-search-grid-filter="artefacts"]', "draft");
      button(ui.target, "Clear all").click();
      await flush();
      assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 0);
      assert.equal(
        filters.querySelector('[data-search-grid-filter="artefacts"]')?.value,
        "",
      );
    } finally {
      await ui.destroy();
    }
  }
});

void test("grid sorting/filter/search controls are absent while column visibility remains shareable", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(response([2, 1]));
  };
  const ui = mounted("artefacts=one&artefacts=two");
  try {
    await flush();
    assert.equal(ui.target.querySelector(".sv-grid-filter-button"), null);
    assert.equal(ui.target.querySelector(".sv-grid-header-icon-hint"), null);
    assert.equal(ui.target.querySelector(".sv-grid-global-filter"), null);
    assert.deepEqual(gridCases(ui.target), ["case 2", "case 1"]);
    const menu = /** @type {import('happy-dom').HTMLButtonElement | null} */ (
      ui.target.querySelector('button[aria-label="Execution ID column menu"]')
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
    ).find((option) => option.textContent.trim() === "version");
    assert.ok(version);
    version.dispatchEvent(new browser.MouseEvent("click", { bubbles: true }));
    await new Promise((resolve) => setTimeout(resolve, 300));
    let shared = app.decodeView(
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
    ).find((option) => option.textContent.trim() === "track");
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

void test("mounted initial recent/pagination-only/invalid, no-match, retry and access states render accurately", async () => {
  /** @type {{query: string; status?: number; session?: Response; text: RegExp; noFetch?: boolean}[]} */
  const cases = [
    {
      query: "limit=2&offset=2",
      text: /No test results match/,
      noFetch: false,
    },
    {
      query: "artefacts=one&issues=any,1",
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

/** @param {import('happy-dom').HTMLElement} target @param {string} selector */
async function clickInput(target, selector) {
  const input = /** @type {import('happy-dom').HTMLInputElement | null} */ (
    target.querySelector(selector)
  );
  assert.ok(input, selector);
  input.click();
  await flush();
  return input;
}

void test("all 18 filter groups are column-header controls without extra page filters", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(response());
  };
  const ui = mounted();
  try {
    await flush();
    const filters = ui.target.querySelector(
      '[data-testid="search-grid-filters"]',
    );
    assert.ok(filters);
    filters.querySelector("summary")?.click();
    await flush();
    for (const field of [
      "Created",
      "Artefact",
      "Family",
      "Stage",
      "Archived",
      "Test Case",
      "Execution Status",
      "Rerun Requested",
      "Latest Execution",
      "Result status",
      "Find Artefact",
      "Artefact Version",
      "Artefact Track",
      "Environment",
      "Test Plan",
      "Template ID",
    ])
      assert.ok(filters.textContent.includes(field), field);
    assert.equal(calls, 1);

    for (const label of ["Issues", "Reviewers", "Execution Metadata"])
      assert.ok(
        ui.target.querySelector(`button[aria-label="Filter ${label}"]`),
        `${label} is an active column filter`,
      );
    assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 0);
    assert.doesNotMatch(ui.target.textContent, /\+ Add filter/);
    assert.equal(ui.target.querySelector(".condition-popover"), null);
  } finally {
    await ui.destroy();
  }
});

void test("Search URL state keeps all canonical filters applied across Search and Clear all", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(response());
  };
  const metadata = `${Buffer.from("build").toString("base64")}:${Buffer.from("stable").toString("base64")}`;
  const source = new URLSearchParams([
    ["families", "snap"],
    ["test_result_statuses", "FAILED"],
    ["test_execution_statuses", "IN_PROGRESS"],
    ["artefacts", "one,two"],
    ["artefact_versions", "1"],
    ["artefact_tracks", "stable"],
    ["environments", "lab"],
    ["test_plans", "smoke"],
    ["test_cases", "case"],
    ["artefact_stages", ""],
    ["artefact_is_archived", "false"],
    ["rerun_is_requested", "true"],
    ["execution_is_latest", "true"],
    ["issues", "any"],
    ["reviewer_ids", "none"],
    ["execution_metadata", metadata],
    ["from_date", "2026-01-01T00:00:00Z"],
    ["until_date", "2026-01-31T23:59:59Z"],
    ["template_ids", "template"],
  ]);
  const ui = mounted(source.toString());
  try {
    await flush();
    assert.equal(ui.target.querySelector('[role="alert"]'), null);
    assert.equal(calls.length, 1);
    for (const key of app.SEARCH_FILTERS)
      assert.ok(calls[0].searchParams.has(key), key);
    assert.deepEqual(calls[0].searchParams.getAll("artefacts"), ["one", "two"]);
    assert.deepEqual(calls[0].searchParams.getAll("artefact_stages"), [""]);
    assert.deepEqual(calls[0].searchParams.getAll("issues"), ["any"]);
    assert.deepEqual(calls[0].searchParams.getAll("reviewer_ids"), ["none"]);
    assert.equal(calls[0].searchParams.get("execution_is_latest"), "true");

    button(ui.target, "Search").click();
    await flush();
    assert.equal(
      calls.length,
      2,
      "Search reapplies the same full canonical query",
    );
    for (const key of app.SEARCH_FILTERS)
      assert.ok(ui.handle.currentUrl.searchParams.has(key), key);
    assert.deepEqual(calls[1].searchParams.getAll("execution_metadata"), [
      metadata,
    ]);

    button(ui.target, "Clear all").click();
    await flush();
    assert.equal(calls.length, 3);
    assert.equal(ui.handle.currentUrl.search, "");
    assert.equal(calls[2].searchParams.has("execution_is_latest"), false);
    assert.equal(calls[2].searchParams.get("offset"), "0");
    assert.equal(calls[2].searchParams.get("limit"), "50");
  } finally {
    await ui.destroy();
  }
});

void test("legacy assignee_ids restores compatibly while URL writes and API requests are canonical", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(response());
  };
  const legacyUrl = url("assignee_ids=11,12");
  const legacy = app.parseSearchPage(legacyUrl.searchParams, families);
  assert.deepEqual(legacy.filters.reviewer_ids, [11, 12]);
  assert.deepEqual(legacy.problems, []);

  const updated = app.editedSearchParams(
    legacy.filters,
    legacyUrl.searchParams,
  );
  assert.equal(updated.has("assignee_ids"), false);
  assert.deepEqual(updated.getAll("reviewer_ids"), ["11", "12"]);

  const store = new app.TestResultsSearchStore();
  await store.search(legacy, families);
  assert.equal(calls.length, 1);
  assert.deepEqual(calls[0].searchParams.getAll("reviewer_ids"), ["11", "12"]);
  assert.equal(calls[0].searchParams.has("assignee_ids"), false);

  const canonicalWins = app.parseSearchPage(
    url("reviewer_ids=none&assignee_ids=11").searchParams,
    families,
  );
  assert.equal(canonicalWins.filters.reviewer_ids, "none");
  assert.deepEqual(canonicalWins.problems, []);
  const invalidCanonicalBlocksAlias = app.parseSearchPage(
    url("reviewer_ids=&assignee_ids=11").searchParams,
    families,
  );
  assert.ok(
    invalidCanonicalBlocksAlias.problems.some((problem) =>
      problem.startsWith("Invalid reviewer_ids:"),
    ),
  );
  store.cancel();
});

void test("advanced column filter state hydrates IDs, modes, and literal metadata into the canonical draft", () => {
  const metadata = `${Buffer.from("failure:charm").toString("base64")}:${Buffer.from("值, punctuation: 🚀").toString("base64")}`;
  const adapted = app.searchFiltersFromGridState(
    {
      global: "",
      custom: {},
      columns: [
        {
          id: "issues",
          operator: "equals",
          value: "",
          selectedValues: ["41", "42"],
        },
        {
          id: "reviewers",
          operator: "equals",
          value: "",
          selectedValues: ["none"],
        },
        {
          id: "executionMetadata",
          operator: "equals",
          value: "",
          selectedValues: [metadata],
        },
      ],
    },
    app.emptyFilters(),
  );
  assert.deepEqual(adapted.issues, [41, 42]);
  assert.equal(adapted.reviewer_ids, "none");
  assert.deepEqual(adapted.execution_metadata, [
    { category: "failure:charm", values: ["值, punctuation: 🚀"] },
  ]);
  const params = app.searchFilterParams(adapted);
  assert.deepEqual(params.getAll("issues"), ["41", "42"]);
  assert.deepEqual(params.getAll("reviewer_ids"), ["none"]);
  assert.equal(params.has("assignee_ids"), false);
  assert.deepEqual(params.getAll("execution_metadata"), [metadata]);
});

void test("URL-hydrated issue, reviewer, and metadata filters populate their column editors", async () => {
  app.searchFilterLabelCache().clear();
  /** @type {URL[]} */
  const calls = [];
  const metadata = `${Buffer.from("failure:component").toString("base64")}:${Buffer.from("值, exact: 🚀").toString("base64")}`;
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    calls.push(request);
    if (request.pathname.endsWith("/test-results/search-page"))
      return Promise.resolve(response());
    if (request.pathname.endsWith("/issues/41"))
      return Promise.resolve(
        json({
          id: 41,
          source: "github",
          project: "test",
          key: "BUG-41",
          title: "Hydrated issue",
        }),
      );
    if (request.pathname.endsWith("/execution-metadata"))
      return Promise.resolve(
        json({
          execution_metadata: { "failure:component": ["值, exact: 🚀"] },
        }),
      );
    return Promise.resolve(response());
  };
  const ui = mounted(
    `issues=41&reviewer_ids=none&execution_metadata=${encodeURIComponent(metadata)}`,
  );
  try {
    await flush();
    assert.equal(
      calls.filter((request) =>
        request.pathname.endsWith("/test-results/search-page"),
      ).length,
      1,
    );
    await chooseFilter(ui.target, "Issues");
    assert.equal(
      ui.target.querySelector('input[name="issues"]')?.value,
      "",
      "selected positive IDs hydrate separately from pending suggestion text",
    );
    assert.match(
      hydratedSelection(ui.target, "issues"),
      /#41 github — test\/BUG-41 — Hydrated issue/,
    );

    await chooseFilter(ui.target, "Reviewers");
    const reviewerMenu = ui.target.querySelector(
      '[data-search-grid-menu="reviewer_ids"]',
    );
    assert.ok(reviewerMenu);
    assert.equal(
      reviewerMenu.querySelector('input[type="radio"][value="none"]')?.checked,
      true,
      "the explicit reviewer mode hydrates into its exclusive radio group",
    );
    assert.equal(
      reviewerMenu.querySelector('input[name="reviewer_ids"]'),
      null,
    );

    await chooseFilter(ui.target, "Execution Metadata");
    assert.match(
      panel(ui.target).querySelector('[aria-label="Metadata conditions"]')
        ?.textContent ?? "",
      /failure:component.*值, exact: 🚀/,
    );
    assert.ok(
      calls.some((request) => request.pathname.endsWith("/execution-metadata")),
      "the known map loads only when the metadata editor opens",
    );
    assert.equal(
      calls.filter((request) =>
        request.pathname.endsWith("/test-results/search-page"),
      ).length,
      1,
      "hydration and suggestion maps do not re-fetch table rows",
    );
    assert.equal(ui.handle.currentUrl.searchParams.get("reviewer_ids"), "none");
    assert.equal(ui.handle.currentUrl.searchParams.has("assignee_ids"), false);
  } finally {
    await ui.destroy();
  }
});

void test("archived, rerun, stage, issue and reviewer search filters", async () => {
  globalThis.fetch = (input) =>
    Promise.resolve(
      new URL(input instanceof Request ? input.url : input).pathname.includes(
        "/test-results/search-page",
      )
        ? response()
        : json({}, 403),
    );
  const ui = mounted(
    "artefact_is_archived=false&rerun_is_requested=false&issues=none&reviewer_ids=any&artefact_stages=unknown,alpha&families=snap",
  );
  try {
    await flush();
    const gridFilters = ui.target.querySelector(
      '[data-testid="search-grid-filters"]',
    );
    assert.ok(gridFilters);
    gridFilters.querySelector("summary")?.click();
    await flush();
    for (const key of ["artefact_is_archived", "rerun_is_requested"]) {
      const select = /** @type {HTMLSelectElement | null} */ (
        gridFilters.querySelector(`[data-search-grid-filter="${key}"]`)
      );
      assert.ok(select);
      assert.equal(select.value, "false");
      select.value = "true";
      select.dispatchEvent(new browser.Event("change", { bubbles: true }));
    }
    const unknownStage = /** @type {HTMLInputElement | null} */ (
      gridFilters.querySelector('input[value="unknown"]')
    );
    assert.ok(unknownStage?.checked);
    unknownStage.click();
    for (const [label, field] of [
      ["Issues", "issues"],
      ["Reviewers", "reviewer_ids"],
    ]) {
      chip(ui.target, label).click();
      await flush();
      await clickInput(panel(ui.target), 'input[value="ids"]');
      await enter(panel(ui.target), `input[name="${field}"]`, "any,1");
      button(panel(ui.target), "Add exact IDs").click();
      await flush();
      assert.ok(panel(ui.target).querySelector('[role="alert"]'));
      await replaceExact(
        panel(ui.target),
        `input[name="${field}"]`,
        "51, 52,51",
      );
      await flushColumnDraft();
      assert.match(
        panel(ui.target).querySelector('[aria-label="Selected details"]')
          ?.textContent ?? "",
        /#51 details unavailable.*#52 details unavailable/,
      );
      const removeUnavailable =
        /** @type {import('happy-dom').HTMLButtonElement | null} */ (
          panel(ui.target).querySelector(
            'button[aria-label="Remove selected 51"]',
          )
        );
      assert.ok(
        removeUnavailable,
        "an unavailable manual ID remains removable",
      );
      removeUnavailable.click();
      await flush();
      assert.equal(panel(ui.target).querySelectorAll(".selected li").length, 1);
      button(panel(ui.target), "Clear filter").click();
      await flush();
      assert.equal(
        panel(ui.target).querySelectorAll(".selected li").length,
        0,
        "clearing an ID filter also clears the mounted editor selection",
      );
      chip(ui.target, label).click();
      await flush();
      chip(ui.target, label).click();
      await flush();
      await clickInput(panel(ui.target), 'input[value="any"]');
      assert.equal(
        panel(ui.target).querySelectorAll("input:checked").length,
        1,
      );
      assert.equal(
        panel(ui.target).querySelector(`input[name="${field}"]`),
        null,
      );
      await flushColumnDraft();
      assert.equal(
        panel(ui.target).querySelector('input[value="any"]')?.checked,
        true,
      );
      chip(ui.target, label).click();
      await flush();
      chip(ui.target, label).click();
      await flush();
      await clickInput(panel(ui.target), 'input[value="none"]');
      await flushColumnDraft();
      assert.equal(
        panel(ui.target).querySelector('input[value="none"]')?.checked,
        true,
      );
    }
    button(ui.target, "Search").click();
    await flush();
    assert.deepEqual(
      ui.handle.currentUrl.searchParams.getAll("artefact_stages"),
      ["alpha"],
    );
    assert.equal(
      ui.handle.currentUrl.searchParams.get("artefact_is_archived"),
      "true",
    );
    assert.equal(
      ui.handle.currentUrl.searchParams.get("rerun_is_requested"),
      "true",
    );
    assert.equal(ui.handle.currentUrl.searchParams.get("issues"), "none");
    assert.equal(ui.handle.currentUrl.searchParams.get("reviewer_ids"), "none");
    assert.equal(
      ui.handle.currentUrl.searchParams.has("execution_is_latest"),
      false,
    );
  } finally {
    await ui.destroy();
  }
});

void test("metadata filter editor validates and removes literal pending pairs", async () => {
  globalThis.fetch = () => Promise.resolve(response());
  const ui = mounted();
  try {
    await flush();
    await chooseFilter(ui.target, "Metadata");
    for (const [category, value] of [
      ["", "value"],
      ["category", ""],
      ["🐧".repeat(201), "value"],
      ["category", "x".repeat(201)],
    ]) {
      await enter(
        panel(ui.target),
        'input[name="metadata-category"]',
        category,
      );
      await enter(panel(ui.target), 'input[name="metadata-value"]', value);
      button(panel(ui.target), "Add pair").click();
      await flush();
      assert.match(
        panel(ui.target).querySelector('[role="alert"]')?.textContent ?? "",
        /1–200 characters/,
      );
    }
    for (const [category, value] of [
      ["🐧".repeat(200), "🐧".repeat(200)],
      ["category:1,2", "value:1,2"],
      ["category:1,2", "value:1,2"],
      ["category:1,2", "other"],
    ]) {
      await enter(
        panel(ui.target),
        'input[name="metadata-category"]',
        category,
      );
      await enter(panel(ui.target), 'input[name="metadata-value"]', value);
      button(panel(ui.target), "Add pair").click();
      await flush();
    }
    assert.equal(
      panel(ui.target).querySelectorAll('button[aria-label^="Remove metadata"]')
        .length,
      3,
    );
    button(panel(ui.target), "Remove pair").click();
    await flush();
    await flushColumnDraft();
    assert.match(
      panel(ui.target).querySelector('[aria-label="Metadata conditions"]')
        ?.textContent ?? "",
      /category:1,2.*value:1,2.*other/,
    );
    button(panel(ui.target), "Remove pair").click();
    await flush();
    button(panel(ui.target), "Remove pair").click();
    await flush();
    assert.equal(
      panel(ui.target).querySelector(
        '[data-search-grid-clear="execution_metadata"]',
      ),
      null,
    );
    await flush();
    assert.equal(
      chip(ui.target, "Metadata").classList.contains("active"),
      false,
    );
    assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 0);
  } finally {
    await ui.destroy();
  }
});

void test("result-created date filters retain exact offsets and inclusive bounds", async () => {
  /** @type {URL[]} */ const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(response());
  };
  const from = "2026-01-01T01:30:00.123456000+01:30";
  const until = "2026-01-01T00:00:00.123457Z";
  const ui = mounted(
    new URLSearchParams({ from_date: from, until_date: until }).toString(),
  );
  try {
    await flush();
    let gridFilters = ui.target.querySelector(
      '[data-testid="search-grid-filters"]',
    );
    assert.ok(gridFilters);
    gridFilters.querySelector("summary")?.click();
    await flush();
    assert.equal(
      gridFilters.querySelector('[data-search-grid-filter="from_date"]').value,
      from,
    );
    button(ui.target, "Search").click();
    await flush();
    gridFilters = ui.target.querySelector(
      '[data-testid="search-grid-filters"]',
    );
    assert.ok(gridFilters);
    assert.equal(calls.at(-1)?.searchParams.get("from_date"), from);
    assert.equal(calls.at(-1)?.searchParams.get("until_date"), until);
    const invalid = "2026-01-01T00:00:00.0000001Z";
    await enter(gridFilters, '[data-search-grid-filter="until_date"]', invalid);
    button(ui.target, "Search").click();
    await flush();
    assert.match(ui.target.textContent, /microsecond/);
    assert.equal(
      calls.length,
      2,
      "invalid timestamps do not issue a broader query",
    );
    ui.handle.restore(
      url(
        `from_date=${encodeURIComponent(from)}&until_date=${encodeURIComponent(until)}`,
      ),
    );
    await flush();
    gridFilters = ui.target.querySelector(
      '[data-testid="search-grid-filters"]',
    );
    assert.ok(gridFilters);
    const nextUntil = "2026-02-01T10:20:30.123456Z";
    await enter(
      gridFilters,
      '[data-search-grid-filter="until_date"]',
      nextUntil,
    );
    button(ui.target, "Search").click();
    await flush();
    gridFilters = ui.target.querySelector(
      '[data-testid="search-grid-filters"]',
    );
    assert.ok(gridFilters);
    assert.equal(calls.at(-1)?.searchParams.get("from_date"), from);
    assert.equal(calls.at(-1)?.searchParams.get("until_date"), nextUntil);
    await enter(gridFilters, '[data-search-grid-filter="from_date"]', "");
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls.at(-1)?.searchParams.has("from_date"), false);
    assert.equal(calls.at(-1)?.searchParams.get("until_date"), nextUntil);
  } finally {
    await ui.destroy();
  }
});

void test("invalid active dates can be fixed while unknown URL constraints remain blocking", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(response());
  };
  const ui = mounted("artefacts=kept&from_date=bad&unknown=kept&offset=-1");
  try {
    await flush();
    const gridFilters = ui.target.querySelector(
      '[data-testid="search-grid-filters"]',
    );
    assert.ok(gridFilters);
    gridFilters.querySelector("summary")?.click();
    await flush();
    assert.equal(
      gridFilters.querySelector('[data-search-grid-filter="from_date"]').value,
      "",
      "malformed URL timestamps are not coerced into a date",
    );
    await enter(
      gridFilters,
      '[data-search-grid-filter="from_date"]',
      "2026-01-01T00:00:00Z",
    );
    assert.match(ui.target.textContent, /Changes not applied/);
    button(ui.target, "Search").click();
    await flush();
    const params = ui.handle.currentUrl.searchParams;
    assert.equal(params.get("from_date"), "2026-01-01T00:00:00Z");
    assert.equal(params.get("unknown"), "kept");
    assert.equal(params.has("offset"), false);
    assert.equal(calls, 0);
    assert.match(ui.target.textContent, /Unsupported URL filter: unknown/);
  } finally {
    await ui.destroy();
  }
});

void test("issue/reviewer label hydration in search filters", async () => {
  app.searchFilterLabelCache().clear();
  app.errorStore.clear();
  /** @type {string[]} */ const details = [];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    if (request.pathname.includes("/test-results"))
      return Promise.resolve(response());
    details.push(request.pathname);
    const id = Number(request.pathname.split("/").at(-1));
    if (id === 71) return Promise.resolve(json({}, 403));
    if (id === 72) return Promise.resolve(json({}, 404));
    if (id === 73) return Promise.reject(new Error("offline"));
    if (id === 74)
      return Promise.resolve(json({ id: 999, name: "Wrong identity" }));
    return Promise.resolve(
      json({ id, name: "Session reviewer", launchpad_handle: "handle" }),
    );
  };
  const ui = mounted("issues=71,72,73&reviewer_ids=74,75");
  try {
    await flush();
    await flush();
    assert.equal(details.length, 5, JSON.stringify(details));
    assert.match(
      hydratedSelection(ui.target, "issues"),
      /#71 details unavailable.*#72 details unavailable.*#73 details unavailable/,
    );
    assert.match(
      hydratedSelection(ui.target, "reviewer_ids"),
      /#74 details unavailable.*#75 Session reviewer @handle/,
    );
    chip(ui.target, "Issues").click();
    await flush();
    assert.match(panel(ui.target).textContent, /#71 details unavailable/);
    browser.document.dispatchEvent(
      new browser.KeyboardEvent("keydown", { key: "Escape", bubbles: true }),
    );
    await flush();
    button(ui.target, "Search").click();
    await flush();
    assert.equal(
      details.length,
      5,
      "remount/save/retry must use session cache including failures",
    );
    assert.deepEqual(ui.handle.currentUrl.searchParams.getAll("issues"), [
      "71,72,73",
    ]);
    assert.equal(app.errorStore.message, null);
    await app.userStore.refresh(() =>
      Promise.resolve(
        json({ id: 1234, name: "New session", teams: [], is_admin: false }),
      ),
    );
    await flush();
    assert.equal(
      details.length,
      10,
      "changed session invalidates private label cache once",
    );
    assert.equal(app.errorStore.message, null);
  } finally {
    await ui.destroy();
  }
});

void test("issue/reviewer label hydration cancellation", async () => {
  app.searchFilterLabelCache().clear();
  const late = deferred();
  const old = json({});
  let reading = false;
  old.json = async () => {
    reading = true;
    const response = await late.promise;
    // eslint-disable-next-line @typescript-eslint/no-unsafe-return -- Response.json is the browser's untyped body parser.
    return response.json();
  };
  /** @type {AbortSignal[]} */ const oldSignals = [];
  let oldCalls = 0;
  globalThis.fetch = (input, options) => {
    const request = new URL(input instanceof Request ? input.url : input);
    if (request.pathname.endsWith("/issues/81")) {
      oldCalls++;
      if (options?.signal) oldSignals.push(options.signal);
      return Promise.resolve(old);
    }
    if (request.pathname.endsWith("/issues/82"))
      return Promise.resolve(
        json({ id: 82, project: "new", key: "82", title: "Latest issue" }),
      );
    return Promise.resolve(response());
  };
  const ui = mounted("issues=81");
  try {
    await flush();
    assert.equal(reading, true);
    const initialCalls = oldCalls;
    assert.equal(
      initialCalls,
      1,
      "initial draft synchronization must not duplicate hydration",
    );
    assert.match(hydratedSelection(ui.target, "issues"), /#81 loading…/);
    ui.handle.restore(url("issues=82"));
    await flush();
    assert.ok(oldSignals.every((signal) => signal.aborted));
    assert.equal(
      oldCalls,
      initialCalls,
      "newly mounted editors must not hydrate outgoing URL IDs",
    );
    assert.match(hydratedSelection(ui.target, "issues"), /Latest issue/);
    late.resolve(
      json({ id: 81, project: "stale", key: "81", title: "Stale issue" }),
    );
    await flush();
    assert.doesNotMatch(ui.target.textContent, /Stale issue/);
    assert.equal(app.searchFilterLabelCache().peek("issues", 81), undefined);
    assert.match(hydratedSelection(ui.target, "issues"), /Latest issue/);
    assert.equal(
      oldCalls,
      initialCalls,
      "the stale identifier is not rehydrated after its URL condition changes",
    );
  } finally {
    await ui.destroy();
  }
});

void test("label cache deduplicates pending requests and only aborts when its last consumer leaves", async () => {
  const cache = new app.SearchFilterLabelCache();
  const pending = deferred();
  let calls = 0;
  /** @type {AbortSignal | null | undefined} */ let requestSignal;
  globalThis.fetch = (_input, options) => {
    calls++;
    requestSignal = options?.signal;
    return pending.promise;
  };
  const first = new AbortController();
  const second = new AbortController();
  const a = cache.load("reviewer_ids", 91, first.signal);
  const b = cache.load("reviewer_ids", 91, second.signal);
  assert.equal(calls, 1);
  first.abort();
  assert.equal(requestSignal?.aborted, false);
  pending.resolve(
    json({ id: 91, name: "Shared reviewer", launchpad_handle: null }),
  );
  assert.equal(await a, undefined);
  assert.equal(await b, "#91 Shared reviewer");
  assert.equal(cache.peek("reviewer_ids", 91), "#91 Shared reviewer");
  assert.equal(
    await cache.load("reviewer_ids", 91, new AbortController().signal),
    "#91 Shared reviewer",
  );
  assert.equal(calls, 1);
});

void test.skip("deferred: issue and metadata menus preserve draft state", async () => {
  let calls = 0;
  globalThis.fetch = (input) => {
    if (
      new URL(input instanceof Request ? input.url : input).pathname.endsWith(
        "/execution-metadata",
      )
    )
      return Promise.resolve(json({ execution_metadata: {} }));
    calls++;
    return Promise.resolve(response());
  };
  const metadata = `${Buffer.from("category").toString("base64")}:${Buffer.from("value").toString("base64")}`;
  const ui = mounted(`issues=none&execution_metadata=${metadata}`);
  try {
    await flush();
    await chooseFilter(ui.target, "Issues");
    await clickInput(panel(ui.target), 'input[value="any"]');
    await flush();
    assert.match(ui.target.textContent, /Changes not applied/);
    assert.equal(calls, 1, "header edits remain drafts until Search");

    await chooseFilter(ui.target, "Metadata");
    await enter(panel(ui.target), 'input[name="metadata-category"]', "pending");
    await enter(panel(ui.target), 'input[name="metadata-value"]', "query text");
    browser.document.dispatchEvent(
      new browser.KeyboardEvent("keydown", { key: "Escape", bubbles: true }),
    );
    await flush();
    assert.equal(ui.target.querySelector(".menu-anchor:not([hidden])"), null);
    assert.match(
      ui.target.querySelector('[aria-label="Metadata conditions"]')
        ?.textContent ?? "",
      /category.*value/,
      "only explicit Add pair actions edit metadata selections",
    );
    await chooseFilter(ui.target, "Metadata");
    assert.equal(
      ui.target.querySelector('input[name="metadata-category"]')?.value,
      "pending",
      "closing a column menu preserves its transient lookup text",
    );
    button(ui.target, "Search").click();
    await flush();
    assert.equal(ui.handle.currentUrl.searchParams.get("issues"), "any");
    assert.deepEqual(
      app.parseSearchPage(ui.handle.currentUrl.searchParams, families).filters
        .execution_metadata,
      [{ category: "category", values: ["value"] }],
    );
    assert.equal(calls, 2, "only explicit Search fetches test results");
  } finally {
    await ui.destroy();
  }
});

const settleSuggestions = () =>
  new Promise((resolve) => setTimeout(resolve, 290));

/** @param {import('happy-dom').HTMLElement} target @param {string} key */
async function press(target, key) {
  const event = new browser.KeyboardEvent("keydown", {
    key,
    bubbles: true,
    cancelable: true,
  });
  target.dispatchEvent(event);
  await flush();
  return event;
}

/** @param {import('happy-dom').HTMLElement} target */
function suggestionButtons(target) {
  return Array.from(target.querySelectorAll("button")).filter((button) =>
    button.closest(".suggestions"),
  );
}

void test("dynamic grid list editors use lookup APIs while pending query text stays out of the filter draft", async () => {
  /** @type {URL[]} */
  const resultCalls = [];
  /** @type {URL[]} */
  const lookupCalls = [];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    if (request.pathname.endsWith("/test-results/search-page")) {
      resultCalls.push(request);
      return Promise.resolve(response());
    }
    lookupCalls.push(request);
    return Promise.resolve(json({ artefacts: ["suggested artefact"] }));
  };
  const ui = mounted("families=snap");
  try {
    await flush();
    assert.equal(resultCalls.length, 1);
    chip(ui.target, "Artefact").click();
    await flush();
    const input = ui.target.querySelector(
      '[data-search-grid-filter="artefacts"]',
    );
    assert.ok(input);
    await typeOnly(input, "suggested");
    assert.deepEqual(selectedValues(ui.target, "artefacts"), []);
    assert.equal(ui.handle.currentUrl.searchParams.has("artefacts"), false);
    assert.doesNotMatch(ui.target.textContent, /Changes not applied/);
    await settleSuggestions();
    assert.equal(lookupCalls.length, 1);
    assert.equal(lookupCalls[0].pathname, "/v1/artefacts/search");
    assert.equal(lookupCalls[0].searchParams.get("q"), "suggested");
    assert.deepEqual(lookupCalls[0].searchParams.getAll("families"), ["snap"]);
    assert.equal(
      resultCalls.length,
      1,
      "suggestion lookup never fetches results",
    );
    const suggestion = suggestionButtons(ui.target).find((button) =>
      button.textContent.includes("suggested artefact"),
    );
    assert.ok(suggestion);
    suggestion.click();
    await flush();
    assert.deepEqual(selectedValues(ui.target, "artefacts"), [
      "suggested artefact",
    ]);
    assert.match(ui.target.textContent, /Changes not applied/);
    assert.equal(resultCalls.length, 1);

    button(ui.target, "Search").click();
    await flush();
    assert.equal(resultCalls.length, 2);
    assert.deepEqual(resultCalls[1].searchParams.getAll("artefacts"), [
      "suggested artefact",
    ]);
    assert.deepEqual(resultCalls[1].searchParams.getAll("families"), ["snap"]);
  } finally {
    await ui.destroy();
  }
});

void test("lookup contracts use the actual six endpoints, trimmed q, bounded replies and draft family parameters only for name lookups", async () => {
  /** @type {{url: URL; options: RequestInit}[]} */ const calls = [];
  globalThis.fetch = (input, options = {}) => {
    const request = new URL(input instanceof Request ? input.url : input);
    calls.push({ url: request, options });
    const path = request.pathname;
    return Promise.resolve(
      json(
        path.endsWith("/test-cases")
          ? {
              test_cases: [
                { test_case: "a case", template_id: "template1" },
                { test_case: "a case", template_id: "template2" },
                { test_case: "comma,case", template_id: "template3" },
              ],
            }
          : path.endsWith("/issues")
            ? {
                issues: [
                  {
                    id: 204,
                    source: "jira",
                    project: "generic",
                    key: "BUG-4",
                    title: "A failure",
                  },
                  { id: -1 },
                ],
              }
            : path.endsWith("/users")
              ? {
                  users: [
                    {
                      id: 205,
                      name: "A Reviewer",
                      launchpad_handle: "review",
                      email: "review@example.test",
                    },
                  ],
                }
              : path.endsWith("/environments")
                ? { environments: ["a lab", "a lab"] }
                : path.endsWith("/test-plans")
                  ? { test_plans: ["a plan"] }
                  : {
                      artefacts: Array.from(
                        { length: 70 },
                        (_, i) => `artefact${i}`,
                      ),
                    },
      ),
    );
  };
  const fields = /** @type {const} */ ([
    "artefacts",
    "environments",
    "test_plans",
    "test_cases",
    "issues",
    "reviewer_ids",
  ]);
  const paths = [
    "artefacts/search",
    "environments",
    "test-plans",
    "test-cases",
    "issues",
    "users",
  ];
  for (const [index, field] of fields.entries()) {
    assert.deepEqual(
      await app.lookupValues(
        field,
        " a ",
        ["custom-family"],
        new AbortController().signal,
      ),
      [],
    );
    assert.equal(calls.length, index);
    const values = await app.lookupValues(
      field,
      "  a query 🐧  ",
      ["z-family", "a-family", "z-family"],
      new AbortController().signal,
    );
    const call = calls[index];
    assert.equal(call.url.pathname, `/v1/${paths[index]}`);
    assert.equal(call.url.searchParams.get("q"), "a query 🐧");
    assert.equal(call.url.searchParams.get("limit"), index < 4 ? "50" : "10");
    assert.deepEqual(
      call.url.searchParams.getAll("families"),
      index < 4 ? ["a-family", "z-family"] : [],
    );
    assert.equal(call.options.credentials, "include");
    assert.equal(new Headers(call.options.headers).get("X-CSRF-Token"), "1");
    if (field === "artefacts") assert.equal(values.length, 50);
    if (field === "environments") assert.equal(values.length, 1);
    if (field === "test_cases") {
      assert.equal(
        values.length,
        2,
        "duplicate case names with different template IDs are one choice",
      );
      assert.equal(values[0].value, "a case");
      assert.match(values[1].unavailable ?? "", /commas/);
    }
    if (field === "issues")
      assert.match(values[0].label, /#204 jira — generic\/BUG-4 — A failure/);
    if (field === "reviewer_ids")
      assert.match(values[0].label, /A Reviewer @review — review@example.test/);
  }
  assert.match(app.suggestionScope(), /^http:\/\/localhost:30000:/);
});

void test("rich issue/reviewer suggestions and mutually exclusive ID filters", async () => {
  app.searchFilterLabelCache().clear();
  app.errorStore.clear();
  /** @type {URL[]} */ const calls = [];
  const suggestionAttempts = { issues: 0, users: 0 };
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    calls.push(request);
    if (request.pathname.endsWith("/test-results/search-page"))
      return Promise.resolve(response());
    if (request.pathname.endsWith("/issues") && request.searchParams.has("q")) {
      suggestionAttempts.issues++;
      if (suggestionAttempts.issues === 1)
        return Promise.resolve(json({}, 403));
    }
    if (request.pathname.endsWith("/users") && request.searchParams.has("q")) {
      suggestionAttempts.users++;
      if (suggestionAttempts.users === 1) return Promise.resolve(json({}, 500));
    }
    return Promise.resolve(
      json(
        request.pathname.endsWith("/issues")
          ? {
              issues: [
                {
                  id: 330,
                  project: "Generic",
                  key: "BUG-1",
                  title: "Issue title",
                  source: "github",
                },
              ],
            }
          : request.pathname.endsWith("/users")
            ? {
                users: [
                  {
                    id: 331,
                    name: "Person",
                    launchpad_handle: "person",
                    email: "person@example.test",
                  },
                ],
              }
            : {},
      ),
    );
  };
  const ui = mounted();
  try {
    await flush();
    for (const [label, field, rich] of [
      ["Issues", "issues", "Issue title"],
      ["Reviewers", "reviewer_ids", "person@example.test"],
    ]) {
      await chooseFilter(ui.target, label);
      await enter(ui.target, `input[name="${field}"]`, "pe");
      await settleSuggestions();
      assert.match(
        panel(ui.target).textContent,
        field === "issues"
          ? /permission to load suggestions/
          : /Suggestions could not be loaded/,
      );
      assert.equal(button(panel(ui.target), "Add exact IDs").disabled, false);
      assert.equal(
        button(panel(ui.target), "Retry suggestions").disabled,
        false,
      );
      assert.equal(app.errorStore.message, null);
      button(panel(ui.target), "Retry suggestions").click();
      await settleSuggestions();
      assert.match(
        suggestionButtons(panel(ui.target))[0].textContent,
        new RegExp(rich),
      );
      suggestionButtons(panel(ui.target))[0].click();
      await flush();
      assert.match(
        panel(ui.target).querySelector(".selected")?.textContent ?? "",
        new RegExp(rich),
      );
      await flushColumnDraft();
      assert.match(hydratedSelection(ui.target, field), new RegExp(rich));
    }
    assert.equal(
      calls.length,
      5,
      "the initial results GET, two local failures and two retries; no redundant /id GET",
    );
    assert.ok(calls.every((c) => !c.searchParams.has("families")));
    chip(ui.target, "Issues").click();
    await flush();
    await enter(ui.target, 'input[name="issues"]', "any,1");
    button(panel(ui.target), "Add exact IDs").click();
    await flush();
    assert.ok(panel(ui.target).querySelector('[role="alert"]'));
    await enter(ui.target, 'input[name="issues"]', "330,330");
    button(panel(ui.target), "Add exact IDs").click();
    await flush();
    assert.equal(panel(ui.target).querySelectorAll(".selected li").length, 1);
    await clickInput(panel(ui.target), 'input[value="none"]');
    await flushColumnDraft();
    assert.equal(
      panel(ui.target).querySelector('input[value="none"]')?.checked,
      true,
    );
  } finally {
    await ui.destroy();
  }
});

void test.skip("deferred: family-scoped search suggestions", async () => {
  const late = deferred();
  const old = json({});
  old.json = async () => {
    const response = await late.promise;
    // eslint-disable-next-line @typescript-eslint/no-unsafe-return -- Browser response parser.
    return response.json();
  };
  /** @type {AbortSignal | null | undefined} */ let oldSignal;
  /** @type {URL[]} */ const calls = [];
  globalThis.fetch = (input, options) => {
    const request = new URL(input instanceof Request ? input.url : input);
    calls.push(request);
    if (request.searchParams.get("families") === "old-family") {
      oldSignal = options?.signal;
      return Promise.resolve(old);
    }
    return Promise.resolve(json({ artefacts: ["new-family result"] }));
  };
  const target = browser.document.createElement("div");
  browser.document.body.append(target);
  const handle = app.mountSuggestions(
    /** @type {HTMLElement} */ (/** @type {unknown} */ (target)),
  );
  try {
    await enter(target, 'input[name="artefacts"]', "same query");
    await settleSuggestions();
    handle.setFamilies(["new-family"]);
    await flush();
    assert.equal(oldSignal?.aborted, true);
    assert.deepEqual(handle.selected, ["retained"]);
    assert.equal(suggestionButtons(target).length, 0);
    late.resolve(json({ artefacts: ["STALE FAMILY"] }));
    await settleSuggestions();
    assert.equal(calls.length, 2);
    assert.deepEqual(calls[1].searchParams.getAll("families"), ["new-family"]);
    assert.doesNotMatch(target.textContent, /STALE FAMILY/);
    assert.match(target.textContent, /new-family result/);
    assert.deepEqual(handle.selected, ["retained"]);
  } finally {
    await handle.destroy();
    target.remove();
  }
});

void test("metadata suggestion filter menu lazily loads its known map", async () => {
  await app.userStore.refresh(() =>
    Promise.resolve(json({ id: 420, teams: [], is_admin: false })),
  );
  /** @type {URL[]} */ const calls = [];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    calls.push(request);
    if (request.pathname.endsWith("/test-results/search-page"))
      return Promise.resolve(response());
    return Promise.resolve(
      json({
        execution_metadata: {
          "c:at,🐧": ["one,two:三", "other"],
          another: ["elsewhere"],
          ["__proto__"]: ["literal"],
        },
      }),
    );
  };
  const ui = mounted();
  try {
    await flush();
    assert.equal(calls.length, 1, "initial recent results were loaded");
    await chooseFilter(ui.target, "Metadata");
    assert.equal(calls.length, 2);
    assert.equal(calls[1].pathname, "/v1/execution-metadata");
    assert.equal(calls[1].search, "");
    const categoryInput =
      /** @type {import("happy-dom").HTMLInputElement | null} */ (
        ui.target.querySelector('input[name="metadata-category"]')
      );
    assert.ok(categoryInput);
    categoryInput.focus();
    await flush();
    assert.deepEqual(
      Array.from(panel(ui.target).querySelectorAll('[role="option"]')).map(
        (item) => item.textContent,
      ),
      ["c:at,🐧", "another", "__proto__"],
      "known categories are visible on empty-query focus",
    );
    await press(categoryInput, "ArrowUp");
    assert.equal(
      categoryInput.getAttribute("aria-activedescendant"),
      `${categoryInput.id.replace(/-category$/, "")}-category-option-2`,
      "ArrowUp from no active option reaches the last option",
    );
    await press(categoryInput, "ArrowDown");
    assert.equal(
      categoryInput.getAttribute("aria-activedescendant"),
      `${categoryInput.id.replace(/-category$/, "")}-category-option-0`,
      "ArrowDown wraps to the first option",
    );
    await enter(ui.target, 'input[name="metadata-category"]', "c:");
    assert.deepEqual(
      Array.from(panel(ui.target).querySelectorAll('[role="option"]')).map(
        (item) => item.textContent,
      ),
      ["c:at,🐧"],
      "category options are filtered locally",
    );
    assert.equal(
      (await press(categoryInput, "ArrowDown")).defaultPrevented,
      true,
    );
    assert.equal((await press(categoryInput, "Enter")).defaultPrevented, true);
    const valueInput = ui.target.querySelector('input[name="metadata-value"]');
    assert.ok(valueInput);
    assert.equal(
      browser.document.activeElement,
      valueInput,
      "keyboard category selection advances focus to Value",
    );
    assert.equal(valueInput.value, "");
    assert.equal(valueInput.disabled, false);
    assert.match(panel(ui.target).textContent, /Known values for c:at,🐧/);
    assert.equal(
      valueInput.getAttribute("aria-controls"),
      `${valueInput.id.replace(/-value$/, "")}-values`,
      "focused Value controls its mounted suggestions listbox",
    );
    assert.deepEqual(
      Array.from(panel(ui.target).querySelectorAll('[role="option"]')).map(
        (item) => item.textContent,
      ),
      ["one,two:三", "other"],
      "selecting a category reveals its values before typing",
    );
    await enter(ui.target, 'input[name="metadata-value"]', "one,");
    assert.deepEqual(
      Array.from(panel(ui.target).querySelectorAll('[role="option"]')).map(
        (item) => item.textContent,
      ),
      ["one,two:三"],
      "value options are filtered locally within the selected category",
    );
    assert.equal((await press(valueInput, "ArrowDown")).defaultPrevented, true);
    assert.equal((await press(valueInput, "Enter")).defaultPrevented, true);
    assert.equal(valueInput.value, "one,two:三");
    assert.equal(valueInput.hasAttribute("aria-controls"), false);
    assert.equal(valueInput.hasAttribute("aria-activedescendant"), false);
    assert.equal((await press(valueInput, "Enter")).defaultPrevented, true);
    await flushColumnDraft();
    assert.equal(
      ui.target.querySelectorAll(".chip-trigger").length,
      0,
      "pending pair blocks implicit form confirmation",
    );
    button(panel(ui.target), "Add pair").click();
    await flush();
    await enter(ui.target, 'input[name="metadata-category"]', "c:at,🐧");
    await enter(ui.target, 'input[name="metadata-value"]', "manual:comma,🐧");
    button(panel(ui.target), "Add pair").click();
    await flush();
    await flushColumnDraft();
    assert.match(
      panel(ui.target).querySelector('[aria-label="Metadata conditions"]')
        ?.textContent ?? "",
      /c:at,🐧.*one,two:三.*manual:comma,🐧/,
    );
    chip(ui.target, "Metadata").click();
    await flush();
    chip(ui.target, "Metadata").click();
    await flush();
    await enter(ui.target, 'input[name="metadata-category"]', "unknown");
    assert.match(panel(ui.target).textContent, /No\s+matching\s+categories/);
    await enter(ui.target, 'input[name="metadata-category"]', "another");
    await enter(ui.target, 'input[name="metadata-value"]', "pending elsewhere");
    await enter(ui.target, 'input[name="metadata-category"]', "__proto__");
    assert.equal(
      ui.target.querySelector('input[name="metadata-value"]')?.value,
      "",
      "changing category clears a value typed for the prior category",
    );
    assert.match(panel(ui.target).textContent, /one,two:三/);
    assert.match(panel(ui.target).textContent, /manual:comma,🐧/);
    const reopenedCategoryInput =
      /** @type {import("happy-dom").HTMLInputElement | null} */ (
        ui.target.querySelector('input[name="metadata-category"]')
      );
    assert.ok(reopenedCategoryInput);
    const reopenedCategoriesId =
      reopenedCategoryInput.getAttribute("aria-controls");
    reopenedCategoryInput.focus();
    await flush();
    assert.deepEqual(
      Array.from(
        panel(ui.target).querySelectorAll(
          `#${reopenedCategoriesId} [role="option"]`,
        ),
      ).map((item) => item.textContent),
      ["__proto__"],
      "category keys are literal data, not object prototype members",
    );
    assert.equal(
      calls.filter((request) =>
        request.pathname.endsWith("/execution-metadata"),
      ).length,
      1,
      "neither typing nor reopening refetches the full map",
    );
    assert.equal(ui.handle.currentUrl.search, "");
    assert.equal(
      (await press(reopenedCategoryInput, "Escape")).defaultPrevented,
      true,
    );
    await flush();
    assert.equal(
      ui.target.querySelector(".menu-anchor:not([hidden])"),
      null,
      "Escape closes the header menu even while inline suggestions are open",
    );
    assert.match(
      ui.target.querySelector('[aria-label="Metadata conditions"]')
        ?.textContent ?? "",
      /c:at,🐧.*one,two:三.*manual:comma,🐧/,
      "pending category/value text does not change confirmed metadata pairs",
    );
    await app.userStore.refresh(() => Promise.resolve(json(null)));
    await flush();
    await app.userStore.refresh(() =>
      Promise.resolve(json({ id: 420, teams: [], is_admin: false })),
    );
    await flush();
    chip(ui.target, "Metadata").click();
    await flush();
    assert.equal(
      calls.filter((request) =>
        request.pathname.endsWith("/execution-metadata"),
      ).length,
      2,
      "logout while closed invalidates even a subsequent identical profile",
    );
  } finally {
    await ui.destroy();
    await app.userStore.refresh(() => Promise.resolve(json(null)));
  }
});

void test("metadata suggestion cancellation and retry preserve the lazy map contract", async () => {
  await app.userStore.refresh(() =>
    Promise.resolve(json({ id: 430, teams: [], is_admin: false })),
  );
  app.errorStore.clear();
  const late = deferred();
  const old = json({});
  old.json = async () => {
    const response = await late.promise;
    // eslint-disable-next-line @typescript-eslint/no-unsafe-return -- Browser response parser.
    return response.json();
  };
  let count = 0;
  /** @type {AbortSignal | null | undefined} */ let oldSignal;
  globalThis.fetch = (input, options) => {
    const request = new URL(input instanceof Request ? input.url : input);
    if (request.pathname.endsWith("/test-results/search-page"))
      return Promise.resolve(response());
    count++;
    if (count === 1) {
      oldSignal = options?.signal;
      return Promise.resolve(old);
    }
    return Promise.resolve(
      count === 2
        ? json({}, 403)
        : json({ execution_metadata: { latest: ["value"] } }),
    );
  };
  const ui = mounted();
  try {
    await flush();
    await chooseFilter(ui.target, "Metadata");
    browser.document.dispatchEvent(
      new browser.KeyboardEvent("keydown", { key: "Escape", bubbles: true }),
    );
    await flush();
    assert.equal(oldSignal?.aborted, true);
    late.resolve(json({ execution_metadata: { PRIVATE: ["OLD"] } }));
    await flush();
    await chooseFilter(ui.target, "Metadata");
    assert.match(panel(ui.target).textContent, /permission/);
    assert.equal(app.errorStore.message, null);
    await enter(ui.target, 'input[name="metadata-category"]', "manual:🐧");
    await enter(ui.target, 'input[name="metadata-value"]', "value,exact");
    button(panel(ui.target), "Add pair").click();
    await flush();
    button(panel(ui.target), "Retry suggestions").click();
    await flush();
    assert.equal(count, 3);
    await enter(ui.target, 'input[name="metadata-category"]', "");
    const categoriesId = ui.target
      .querySelector('input[name="metadata-category"]')
      ?.getAttribute("aria-controls");
    const options = Array.from(
      panel(ui.target).querySelectorAll(`#${categoriesId} [role="option"]`),
    ).map((item) => item.textContent);
    assert.deepEqual(options, ["latest"]);
    await flushColumnDraft();
    assert.match(
      panel(ui.target).querySelector('[aria-label="Metadata conditions"]')
        ?.textContent ?? "",
      /manual:🐧.*value,exact/,
    );
  } finally {
    await ui.destroy();
    await app.userStore.refresh(() => Promise.resolve(json(null)));
  }
});

void test.skip("deferred: manual metadata filter pairs retain literal semantics", async () => {
  await app.userStore.refresh(() =>
    Promise.resolve(json({ id: 435, teams: [], is_admin: false })),
  );
  globalThis.fetch = (input) =>
    Promise.resolve(
      new URL(input instanceof Request ? input.url : input).pathname.endsWith(
        "/test-results/search-page",
      )
        ? response()
        : json({ execution_metadata: { known: ["suggested"] } }),
    );
  const ui = mounted();
  try {
    await flush();
    await chooseFilter(ui.target, "Metadata");
    await enter(
      ui.target,
      'input[name="metadata-category"]',
      "manual:category🐧",
    );
    const valueInput = await enter(
      ui.target,
      'input[name="metadata-value"]',
      "exact, value:三",
    );
    valueInput.focus();
    await flush();
    const status = panel(ui.target).querySelector('[role="status"]');
    assert.ok(status);
    const manualNoMatch = status.textContent.trim().replace(/\s+/g, " ");
    assert.equal(manualNoMatch, "No known values for this category.");

    const addPair = button(panel(ui.target), "Add pair");
    addPair.focus();
    await flush();
    assert.equal(
      status.textContent.trim().replace(/\s+/g, " "),
      manualNoMatch,
      "manual no-match status persists after focus leaves Value",
    );
    addPair.click();
    await flush();

    assert.match(panel(ui.target).textContent, /"manual:category🐧"/);
    assert.match(panel(ui.target).textContent, /"exact, value:三"/);
    assert.equal(valueInput.value, "", "Add pair clears the committed value");
    assert.equal(
      document.activeElement,
      addPair,
      "adding a pair keeps focus on the action instead of reopening suggestions",
    );
    assert.equal(
      ui.target
        .querySelector('input[name="metadata-category"]')
        ?.getAttribute("aria-expanded"),
      "false",
      "adding a pair does not expand the category list and shift following actions",
    );
    assert.match(
      panel(ui.target).querySelector('[aria-label="Metadata conditions"]')
        ?.textContent ?? "",
      /manual:category🐧.*exact, value:三/,
    );

    chip(ui.target, "Metadata").click();
    await flush();
    chip(ui.target, "Metadata").click();
    await flush();
    await enter(ui.target, 'input[name="metadata-category"]', "second");
    await enter(ui.target, 'input[name="metadata-value"]', "saved value");
    const editAddPair = button(panel(ui.target), "Add pair");
    editAddPair.focus();
    editAddPair.click();
    await flush();
    assert.equal(
      document.activeElement,
      editAddPair,
      "editing also keeps focus on Add pair without opening a list",
    );
    assert.match(
      panel(ui.target).querySelector('[aria-label="Metadata conditions"]')
        ?.textContent ?? "",
      /manual:category🐧.*exact, value:三.*second.*saved value/,
    );
    button(ui.target, "Search").click();
    await flush();
    const applied = app.parseSearchPage(
      ui.handle.currentUrl.searchParams,
      families,
    );
    assert.deepEqual(applied.filters.execution_metadata, [
      { category: "manual:category🐧", values: ["exact, value:三"] },
      { category: "second", values: ["saved value"] },
    ]);
  } finally {
    await ui.destroy();
    await app.userStore.refresh(() => Promise.resolve(json(null)));
  }
});

void test.skip("deferred: metadata filter picker supports keyboard and lazy suggestions", async () => {
  await app.userStore.refresh(() =>
    Promise.resolve(json({ id: 445, teams: [], is_admin: false })),
  );
  const execution_metadata = Object.fromEntries(
    Array.from({ length: 75 }, (_, index) => [
      `category-${index}`,
      index === 0
        ? [
            "first,exact:🐧",
            ...Array.from({ length: 74 }, (_, value) => `option-${value}`),
          ]
        : [`value-${index}`],
    ]),
  );
  /** @type {URL[]} */ const calls = [];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    calls.push(request);
    return Promise.resolve(
      request.pathname.endsWith("/test-results/search-page")
        ? response()
        : json({ execution_metadata }),
    );
  };
  const ui = mounted();
  try {
    await flush();
    assert.equal(calls.length, 1, "initial recent results were loaded");
    await chooseFilter(ui.target, "Metadata");
    await flush();
    const categoryInput =
      /** @type {import("happy-dom").HTMLInputElement | null} */ (
        ui.target.querySelector('input[name="metadata-category"]')
      );
    assert.ok(categoryInput);
    const valueInputBeforeFocus = ui.target.querySelector(
      'input[name="metadata-value"]',
    );
    assert.ok(valueInputBeforeFocus);
    assert.ok(categoryInput.hasAttribute("aria-controls"));
    assert.equal(valueInputBeforeFocus.hasAttribute("aria-controls"), false);
    categoryInput.focus();
    await flush();
    const categoryListId = categoryInput.getAttribute("aria-controls");
    assert.ok(categoryListId);
    assert.equal(
      panel(ui.target)
        .querySelector(`#${categoryListId}`)
        ?.getAttribute("role"),
      "listbox",
      "aria-controls references a mounted category listbox",
    );
    const categoryOptions = () =>
      Array.from(
        panel(ui.target).querySelectorAll(`#${categoryListId} [role="option"]`),
      );
    assert.equal(categoryOptions().length, 50);
    assert.match(panel(ui.target).textContent, /Showing 50 of 75/);
    const categoryList = panel(ui.target).querySelector(`#${categoryListId}`);
    assert.equal(
      categoryList?.getAttribute("class")?.includes("suggestions"),
      true,
    );

    await enter(ui.target, 'input[name="metadata-category"]', "category-7");
    assert.equal(categoryOptions().length, 6);
    assert.ok(
      categoryOptions().some((option) => option.textContent === "category-74"),
    );
    await enter(ui.target, 'input[name="metadata-category"]', "category-0");
    assert.equal(categoryOptions().length, 1);
    /** @type {string[]} */ const categoryScrolls = [];
    for (const option of categoryOptions())
      option.scrollIntoView = (options) => {
        assert.deepEqual(options, { block: "nearest" });
        categoryScrolls.push(option.id);
      };
    assert.equal(
      (await press(categoryInput, "ArrowDown")).defaultPrevented,
      true,
    );
    assert.deepEqual(categoryScrolls, [
      `${categoryInput.id.replace(/-category$/, "")}-category-option-0`,
    ]);
    assert.equal(
      browser.document.getElementById(
        categoryInput.getAttribute("aria-activedescendant"),
      ),
      categoryOptions()[0],
      "active descendant always points to a mounted category option",
    );
    assert.equal((await press(categoryInput, "Enter")).defaultPrevented, true);
    const valueInput = ui.target.querySelector('input[name="metadata-value"]');
    assert.ok(valueInput);
    const valueListId = valueInput.getAttribute("aria-controls");
    const valueOptions = () =>
      Array.from(
        panel(ui.target).querySelectorAll(`#${valueListId} [role="option"]`),
      );
    assert.equal(valueOptions().length, 50);
    assert.match(panel(ui.target).textContent, /Showing 50 of 75/);
    assert.equal(valueOptions()[0]?.textContent, "first,exact:🐧");
    /** @type {string[]} */ const valueScrolls = [];
    for (const option of valueOptions())
      option.scrollIntoView = (options) => {
        assert.deepEqual(options, { block: "nearest" });
        valueScrolls.push(option.id);
      };
    assert.equal((await press(valueInput, "ArrowDown")).defaultPrevented, true);
    assert.deepEqual(valueScrolls, [
      `${valueInput.id.replace(/-value$/, "")}-value-option-0`,
    ]);
    assert.equal(
      browser.document.getElementById(
        valueInput.getAttribute("aria-activedescendant"),
      ),
      valueOptions()[0],
      "active descendant always points to a mounted value option",
    );
    for (let index = 1; index < 50; index++)
      await press(valueInput, "ArrowDown");
    assert.equal(valueScrolls.length, 50);
    assert.equal(
      valueScrolls.at(-1),
      `${valueInput.id.replace(/-value$/, "")}-value-option-49`,
    );
    assert.equal(
      browser.document.getElementById(
        valueInput.getAttribute("aria-activedescendant"),
      ),
      valueOptions()[49],
      "the last visible capped-list option stays the active descendant",
    );
    // Return to the first exact value before committing it.
    for (let index = 0; index < 51; index++)
      await press(valueInput, "ArrowDown");
    assert.equal((await press(valueInput, "Enter")).defaultPrevented, true);
    button(panel(ui.target), "Add pair").click();
    await flush();
    assert.match(panel(ui.target).textContent, /"category-0"/);
    assert.match(panel(ui.target).textContent, /"first,exact:🐧"/);

    await enter(ui.target, 'input[name="metadata-category"]', "category-1");
    await enter(ui.target, 'input[name="metadata-value"]', "pending for one");
    await enter(ui.target, 'input[name="metadata-category"]', "category-2");
    assert.equal(
      ui.target.querySelector('input[name="metadata-value"]')?.value,
      "",
      "pending text cannot be reassigned when category changes",
    );
    assert.match(panel(ui.target).textContent, /"category-0"/);
    assert.match(panel(ui.target).textContent, /"first,exact:🐧"/);
    assert.equal(
      calls.filter((request) =>
        request.pathname.endsWith("/execution-metadata"),
      ).length,
      1,
    );
    assert.equal(
      calls.filter((request) =>
        request.pathname.endsWith("/test-results/search-page"),
      ).length,
      1,
      "typing and choosing metadata adds no test-results search beyond the initial load",
    );
  } finally {
    await ui.destroy();
    await app.userStore.refresh(() => Promise.resolve(json(null)));
  }
});

void test("known metadata cache has a bounded lifetime rather than persisting stale options indefinitely", async () => {
  await app.userStore.refresh(() =>
    Promise.resolve(json({ id: 440, teams: [], is_admin: false })),
  );
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(
      json({ execution_metadata: { category: [`generation${calls}`] } }),
    );
  };
  const now = Date.now;
  try {
    const scope = app.suggestionScope();
    const first = await app.metadataSuggestions.load(
      scope,
      new AbortController().signal,
    );
    const cached = await app.metadataSuggestions.load(
      scope,
      new AbortController().signal,
    );
    assert.deepEqual(first, { category: ["generation1"] });
    assert.deepEqual(cached, first);
    assert.equal(calls, 1);
    Date.now = () => now() + 6 * 60_000;
    const refreshed = await app.metadataSuggestions.load(
      scope,
      new AbortController().signal,
    );
    assert.deepEqual(refreshed, { category: ["generation2"] });
    assert.equal(calls, 2);
  } finally {
    Date.now = now;
    await app.userStore.refresh(() => Promise.resolve(json(null)));
  }
});
