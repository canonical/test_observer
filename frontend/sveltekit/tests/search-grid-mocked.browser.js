// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

// Real Chromium integration QA using the current Vite app and synthetic API
// responses. Playwright is supplied externally; this does not contact a live
// Test Observer API or require credentials/database data.
// Playwright is dynamically imported without project types; its API and
// page.evaluate values are intentionally untyped in this standalone script.
/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-return, @typescript-eslint/no-unsafe-argument */
import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { createServer } from "vite";

const { chromium } = await import(
  process.env.PLAYWRIGHT_MODULE ?? "playwright-core"
);
const root = fileURLToPath(new URL("..", import.meta.url));
const basePath = process.env.BASE_PATH ?? "/wip";
const artifacts = resolve(
  process.env.QA_ARTIFACT_DIR ?? "/tmp/opencode/search-grid-mocked",
);
await mkdir(artifacts, { recursive: true });

const categories = Array.from({ length: 41 }, (_, index) => {
  const prefix = `カテゴリー-${String(index + 1).padStart(2, "0")}-`;
  return `${prefix}${"界".repeat(180 - Array.from(prefix).length)}`;
});
/** @type {(rowIndex: number) => string[]} */
const valuesFor = (rowIndex) =>
  [
    `値-${rowIndex + 1}-A-${"🧪é界".repeat(49)}x`,
    `値-${rowIndex + 1}-B-${"δοκιμή/🛰️".repeat(19)}tail`,
  ].map((value) => Array.from(value).slice(0, 200).join(""));
/** @type {(rowIndex: number) => { category: string; value: string }[]} */
const metadataPairs = (rowIndex) =>
  categories.flatMap((category) =>
    valuesFor(rowIndex).map((value) => ({ category, value })),
  );
const rows = Array.from({ length: 50 }, (_, index) => {
  const id = 9000 - index;
  const metadata = metadataPairs(index);
  return {
    test_result: {
      id,
      name: `unicode-case-${index + 1} · λ漢字 🧪`,
      category: `integration-${index % 5}`,
      created_at: `2026-10-25T12:${String(59 - index).padStart(2, "0")}:00Z`,
      template_id: `template-${index % 7}`,
      status: index % 2 === 0 ? "PASSED" : "FAILED",
      issues: [
        {
          id: 3000 + index,
          key: `QA-${index + 1}`,
          title: `Long issue title ${"Δ界🧪".repeat(48)}`.slice(0, 195),
        },
      ],
    },
    test_execution: {
      id: 7000 + index,
      status: "PASSED",
      environment: { name: `env-${index % 4} · 東京` },
      test_plan: `plan-${index % 3}`,
      rerun_is_requested: index % 3 === 0,
      execution_is_latest: index % 2 === 0,
      execution_metadata: metadata,
    },
    artefact: {
      id: 6000 + index,
      name: `synthetic-artefact-${index}`,
      version: `1.${index}.0`,
      track: "latest",
      family: "deb",
      stage: index === 0 ? "" : index % 2 ? "updates" : "proposed",
      archived: index % 2 === 0,
      reviewers: [
        {
          id: 2000 + index,
          name: `Reviewer ${index + 1} · ${"É界".repeat(40)}`,
          launchpad_handle: `reviewer-${index}`,
        },
      ],
    },
    artefact_build: { architecture: "amd64" },
  };
});

const details = {
  test_result: {
    id: rows[0].test_result.id,
    name: rows[0].test_result.name,
    category: rows[0].test_result.category,
    template_id: rows[0].test_result.template_id,
    status: rows[0].test_result.status,
    io_log: "Synthetic details fixture — no production data.",
    issues: [
      {
        issue: {
          id: rows[0].test_result.issues[0].id,
          source: "GITHUB",
          project: "test-observer/qa",
          key: rows[0].test_result.issues[0].key,
          title: rows[0].test_result.issues[0].title,
          status: "OPEN",
        },
      },
    ],
  },
  test_execution: {
    id: rows[0].test_execution.id,
    status: rows[0].test_execution.status,
    environment: rows[0].test_execution.environment,
    test_plan: rows[0].test_execution.test_plan,
    created_at: "2026-10-25T12:00:00Z",
    execution_metadata: Object.fromEntries(
      categories.map((category) => [category, valuesFor(0)]),
    ),
  },
  artefact: {
    id: rows[0].artefact.id,
    name: rows[0].artefact.name,
    version: rows[0].artefact.version,
    track: rows[0].artefact.track,
    family: rows[0].artefact.family,
  },
  artefact_build: rows[0].artefact_build,
};

const searchBody = JSON.stringify({
  count: rows.length,
  limit: 50,
  offset: 0,
  rows,
});
const utf8Bytes = Buffer.byteLength(searchBody, "utf8");
const requestLog = [];
const pageErrors = [];
const server = await createServer({
  configFile: resolve(root, "vite.config.ts"),
  root,
  cacheDir: resolve(artifacts, "vite-cache"),
  server: { host: "127.0.0.1", port: 0, strictPort: false },
});
let browser;
let passed = false;

try {
  await server.listen();
  const address = server.httpServer.address();
  assert.ok(address && typeof address !== "string");
  const pageUrl = `http://127.0.0.1:${address.port}${basePath}/test-results`;
  const apiOrigin = "http://localhost:30000";
  browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox"],
    ...(process.env.CHROMIUM_EXECUTABLE
      ? { executablePath: process.env.CHROMIUM_EXECUTABLE }
      : {}),
  });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
  });
  await context.addInitScript(() => {
    window.__searchQaParseMetrics = [];
    // Preserve the response receiver while retaining the native implementation.
    // eslint-disable-next-line @typescript-eslint/unbound-method -- The original method requires each Response as its receiver.
    const original = Response.prototype.json;
    Response.prototype.json = async function (...args) {
      const url = this.url;
      const isSearch =
        url.includes("/v1/test-results/search-page?") ||
        url.endsWith("/v1/test-results/search-page");
      const started = performance.now();
      const result = await original.apply(this, args);
      if (isSearch) {
        window.__searchQaParseMetrics.push({
          parseAndDecodeMs: performance.now() - started,
          completedAt: performance.now(),
        });
      }
      return result;
    };
  });
  const page = await context.newPage();
  page.setDefaultTimeout(20000);
  page.on("pageerror", (error) => pageErrors.push(String(error)));

  await context.route(`${apiOrigin}/v1/**`, async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    requestLog.push({
      method: request.method(),
      pathname: url.pathname,
      search: url.search,
    });
    const cors = {
      "access-control-allow-origin": new URL(pageUrl).origin,
      "access-control-allow-credentials": "true",
      "access-control-allow-methods": "GET, OPTIONS",
      "access-control-allow-headers": "content-type, x-csrf-token",
    };
    if (request.method() === "OPTIONS") {
      await route.fulfill({ status: 204, headers: cors });
      return;
    }
    if (url.pathname === "/v1/users/me") {
      await route.fulfill({
        status: 200,
        headers: cors,
        contentType: "application/json",
        body: "null",
      });
      return;
    }
    if (url.pathname === "/v1/execution-metadata") {
      const knownMetadata = Object.fromEntries(
        categories.map((category, index) => [category, valuesFor(0, index)]),
      );
      await route.fulfill({
        status: 200,
        headers: cors,
        contentType: "application/json",
        body: JSON.stringify({ execution_metadata: knownMetadata }),
      });
      return;
    }
    if (url.pathname === "/v1/test-results/search-page") {
      const params = url.searchParams;
      const offset = Number(params.get("offset") ?? 0);
      const limit = Number(params.get("limit") ?? 50);
      // Deliberately echo this unchanged row block for every applied query so
      // the QA can detect any client-side filtering of server-returned rows.
      const body = JSON.stringify({
        count: rows.length,
        limit,
        offset,
        rows: rows.slice(offset, offset + limit),
      });
      await route.fulfill({
        status: 200,
        headers: cors,
        contentType: "application/json",
        body,
      });
      return;
    }
    if (
      url.pathname === `/v1/test-results/search-page/${rows[0].test_result.id}`
    ) {
      await route.fulfill({
        status: 200,
        headers: cors,
        contentType: "application/json",
        body: JSON.stringify(details),
      });
      return;
    }
    await route.fulfill({
      status: 404,
      headers: cors,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Unmocked QA endpoint" }),
    });
  });

  await page.goto(pageUrl, { waitUntil: "networkidle" });
  await page
    .locator('tbody tr td[data-col-id="details"] button')
    .first()
    .waitFor();
  await page.waitForFunction(() => window.__searchQaParseMetrics.length > 0);
  const initialJsonMetrics = await page.evaluate(
    () => window.__searchQaParseMetrics[0],
  );
  const initialRenderTimeMs = await page.evaluate(
    (parsedAt) => performance.now() - parsedAt,
    initialJsonMetrics.completedAt,
  );
  const expectedColumns = [
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
    "environment",
    "architecture",
    "testPlan",
    "templateId",
    "issues",
    "reviewers",
    "executionMetadata",
  ];
  const initialRows = await page.locator("tbody tr").count();
  const columnIds = await page
    .locator("th[data-svgrid-header-col]")
    .evaluateAll((headers) =>
      headers.map((header) => header.getAttribute("data-svgrid-header-col")),
    );
  const filterTriggers = await page
    .locator("button.column-filter-trigger")
    .count();
  assert.deepEqual(
    columnIds,
    expectedColumns,
    "the grid exposes the final ordered 23 columns",
  );
  assert.equal(
    filterTriggers,
    18,
    "the 18 filter groups are column-header editors",
  );
  assert.ok(initialRows > 0, "the mock API rows are rendered");
  const initialVisualGeometry = await page.evaluate(() => {
    const target = document.querySelector(
      'tbody td[data-col-id="issues"] button',
    );
    const rect = target?.getBoundingClientRect();
    const hit =
      rect &&
      document.elementFromPoint(
        rect.left + rect.width / 2,
        rect.top + rect.height / 2,
      );
    const filterBar = document
      .querySelector(".filter-bar")
      ?.getBoundingClientRect();
    return {
      viewport: { width: innerWidth, height: innerHeight },
      target: rect && {
        left: rect.left,
        right: rect.right,
        top: rect.top,
        bottom: rect.bottom,
      },
      hitTag: hit?.tagName,
      hitClass: hit?.className ?? "",
      filterBar: filterBar && {
        left: filterBar.left,
        right: filterBar.right,
        top: filterBar.top,
        bottom: filterBar.bottom,
      },
      document: { height: document.documentElement.scrollHeight, scrollY },
    };
  });
  process.stdout.write(
    `Initial geometry: ${JSON.stringify(initialVisualGeometry)}\n`,
  );
  await page.screenshot({
    path: resolve(artifacts, "search-grid-1440x1000.png"),
    fullPage: false,
  });

  const firstRow = page.locator("tbody tr").first();
  assert.match(
    await firstRow.locator('td[data-col-id="stage"]').innerText(),
    /\(none\)/,
  );
  assert.match(
    await firstRow.locator('td[data-col-id="category"]').innerText(),
    /integration-0/,
  );
  assert.match(
    await firstRow.locator('td[data-col-id="execution"]').innerText(),
    /7000/,
  );
  assert.match(
    await firstRow.locator('td[data-col-id="architecture"]').innerText(),
    /amd64/,
  );
  assert.match(
    await firstRow.locator('td[data-col-id="status"]').innerText(),
    /PASSED/,
  );
  for (const [column, label] of [
    ["issues", "1 issue"],
    ["reviewers", "1 reviewer"],
    ["executionMetadata", "82 metadata pairs"],
  ]) {
    const cell = firstRow.locator(`td[data-col-id="${column}"]`);
    assert.equal(
      await cell.locator("button.summary").innerText(),
      label,
      `${column} displays its concise count summary`,
    );
    assert.equal(
      await cell.locator(".preview").count(),
      0,
      `${column} does not render raw values inline`,
    );
  }

  const gridScrollState = await page.evaluate(async () => {
    const container = document.querySelector(".sv-grid-container");
    const cell = document.querySelector('tbody td[data-col-id="issues"]');
    if (!container || !cell) return null;
    const containerRect = container.getBoundingClientRect();
    const cellRect = cell.getBoundingClientRect();
    const targetLeft =
      cellRect.left - containerRect.left + container.scrollLeft;
    container.scrollLeft = Math.max(0, targetLeft - 4);
    await new Promise((resolve) =>
      requestAnimationFrame(() => requestAnimationFrame(resolve)),
    );
    const visibleCell = cell.getBoundingClientRect();
    return {
      clientWidth: container.clientWidth,
      scrollWidth: container.scrollWidth,
      scrollLeft: container.scrollLeft,
      cellLeft: visibleCell.left,
      cellRight: visibleCell.right,
      containerLeft: container.getBoundingClientRect().left,
      containerRight: container.getBoundingClientRect().right,
    };
  });
  assert.ok(
    gridScrollState && gridScrollState.scrollLeft > 0,
    "the SvGrid horizontal scrollbar reaches the compact summary columns",
  );
  process.stdout.write(
    `Issue column scroll: ${JSON.stringify(gridScrollState)}\n`,
  );

  const valueDialogChecks = [];
  let valueDialogVisuals;
  let valueDialogNarrowVisuals;
  for (const [column, buttonName, expectedText, expectedItems] of [
    ["issues", "1 issue", rows[0].test_result.issues[0].title, 1],
    ["reviewers", "1 reviewer", rows[0].artefact.reviewers[0].name, 1],
    ["executionMetadata", "82 metadata pairs", categories[40], 82],
  ]) {
    const cell = firstRow.locator(`td[data-col-id="${column}"]`);
    const showAll = cell.getByRole("button", { name: buttonName, exact: true });
    await showAll.focus();
    await page.keyboard.press("Enter");
    const dialog = page.locator("dialog.search-grid-value-dialog[open]");
    await dialog.waitFor({ state: "visible" });
    assert.match(
      await dialog.innerText(),
      new RegExp(expectedText.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")),
    );
    if (column === "executionMetadata") {
      assert.deepEqual(
        await dialog.locator("thead th[scope=col]").allTextContents(),
        ["Category", "Value"],
        "the metadata dialog exposes semantic Category and Value headings",
      );
      assert.equal(await dialog.locator("tbody tr").count(), expectedItems);
    } else {
      assert.equal(await dialog.locator("li").count(), expectedItems);
    }
    assert.equal(
      await dialog.evaluate((element) => element.closest("td") === null),
      true,
      "the dialog is shared beside the grid, not owned by a virtualized cell",
    );
    assert.ok(await dialog.locator(".dialog-content-header, header").count());
    assert.ok(await dialog.locator(".dialog-content-footer, footer").count());
    if (column === "issues") {
      const issueLink = dialog.getByRole("link", {
        name: `View issue ${rows[0].test_result.issues[0].key}`,
      });
      assert.equal(
        await issueLink.getAttribute("href"),
        `${basePath}/issues/${rows[0].test_result.issues[0].id}`,
      );
      assert.equal(await issueLink.getAttribute("target"), "_blank");
      assert.equal(await issueLink.getAttribute("rel"), "noopener noreferrer");
      assert.match(await issueLink.innerText(), /QA-1/);
      assert.match(await issueLink.innerText(), /Long issue title/);
    }
    if (column === "executionMetadata") {
      const actualPairs = await dialog
        .locator("tbody tr")
        .evaluateAll((items) =>
          items.map((item) => [
            item.querySelector('th[scope="row"]')?.textContent ?? "",
            item.querySelector("td")?.textContent ?? "",
          ]),
        );
      assert.deepEqual(
        actualPairs,
        metadataPairs(0).map((pair) => [pair.category, pair.value]),
        "the dialog preserves every literal Unicode metadata category/value pair",
      );
      valueDialogVisuals = await dialog.evaluate((element) => {
        const rect = element.getBoundingClientRect();
        const body = element.querySelector(".value-body");
        const bodyRect = body?.getBoundingClientRect();
        const header = element.querySelector(".dialog-content-header, header");
        const footer = element.querySelector(".dialog-content-footer, footer");
        const headerRect = header?.getBoundingClientRect();
        const footerRect = footer?.getBoundingClientRect();
        const style = getComputedStyle(element);
        const bodyStyle = body ? getComputedStyle(body) : null;
        const backdrop = getComputedStyle(element, "::backdrop");
        return {
          viewport: { width: innerWidth, height: innerHeight },
          dialog: {
            left: rect.left,
            right: rect.right,
            top: rect.top,
            bottom: rect.bottom,
            width: rect.width,
            height: rect.height,
          },
          centered: {
            x: Number(rect.left) + Number(rect.width) / 2,
            y: Number(rect.top) + Number(rect.height) / 2,
          },
          border: {
            width: style.borderTopWidth,
            style: style.borderTopStyle,
            radius: style.borderTopLeftRadius,
          },
          surface: style.backgroundColor,
          backdrop: backdrop.backgroundColor,
          body: body && {
            clientHeight: body.clientHeight,
            scrollHeight: body.scrollHeight,
            overflowY: bodyStyle?.overflowY,
            top: bodyRect?.top,
            bottom: bodyRect?.bottom,
          },
          header: headerRect && {
            top: headerRect.top,
            bottom: headerRect.bottom,
          },
          footer: footerRect && {
            top: footerRect.top,
            bottom: footerRect.bottom,
          },
        };
      });
      process.stdout.write(
        `Summary modal wide geometry: ${JSON.stringify(valueDialogVisuals)}\n`,
      );
      assert.ok(valueDialogVisuals.body);
      assert.ok(
        Math.abs(valueDialogVisuals.centered.x - 720) < 2 &&
          Math.abs(valueDialogVisuals.centered.y - 500) < 2,
        `the list modal is centered: ${JSON.stringify(valueDialogVisuals)}`,
      );
      assert.ok(valueDialogVisuals.dialog.width <= 900);
      assert.equal(valueDialogVisuals.border.style, "solid");
      assert.ok(Number.parseFloat(valueDialogVisuals.border.width) > 0);
      assert.notEqual(valueDialogVisuals.surface, "rgba(0, 0, 0, 0)");
      assert.notEqual(valueDialogVisuals.backdrop, "rgba(0, 0, 0, 0)");
      assert.match(valueDialogVisuals.body.overflowY, /auto|scroll/);
      assert.ok(
        valueDialogVisuals.body.scrollHeight >
          valueDialogVisuals.body.clientHeight,
        "long metadata uses an internally scrolling modal body",
      );
      assert.ok(valueDialogVisuals.header.top >= valueDialogVisuals.dialog.top);
      assert.ok(
        valueDialogVisuals.footer.bottom <= valueDialogVisuals.dialog.bottom,
        "the footer remains visible outside the scroll body",
      );

      await page.setViewportSize({ width: 800, height: 600 });
      await page.waitForTimeout(50);
      const narrowDialogGeometry = await dialog.evaluate((element) => {
        const rect = element.getBoundingClientRect();
        const body = element.querySelector(".value-body");
        return {
          left: rect.left,
          right: rect.right,
          top: rect.top,
          bottom: rect.bottom,
          width: rect.width,
          height: rect.height,
          bodyClientHeight: body?.clientHeight ?? 0,
          bodyScrollHeight: body?.scrollHeight ?? 0,
        };
      });
      valueDialogNarrowVisuals = narrowDialogGeometry;
      assert.ok(
        narrowDialogGeometry.left >= 0 &&
          narrowDialogGeometry.right <= 800 &&
          narrowDialogGeometry.width <= 768 + 1,
        `the responsive modal stays within 1rem side margins: ${JSON.stringify(narrowDialogGeometry)}`,
      );
      assert.ok(
        narrowDialogGeometry.top >= 0 &&
          narrowDialogGeometry.bottom <= 600 &&
          narrowDialogGeometry.height <= 568 + 1,
        `the responsive modal stays within 1rem vertical margins: ${JSON.stringify(narrowDialogGeometry)}`,
      );
      assert.ok(
        narrowDialogGeometry.bodyScrollHeight >
          narrowDialogGeometry.bodyClientHeight,
        "the value list remains scrollable in the narrow viewport",
      );
      await page.setViewportSize({ width: 1440, height: 1000 });
      await page.waitForTimeout(50);
    }
    valueDialogChecks.push({ column, completeItems: expectedItems });
    await dialog.getByRole("button", { name: "Close", exact: true }).click();
    await dialog.waitFor({ state: "hidden" });
    assert.equal(
      await showAll.evaluate((element) => document.activeElement === element),
      true,
      `${column} closing returns focus to its summary trigger`,
    );
  }

  const escapeTrigger = firstRow.getByRole("button", {
    name: "1 issue",
    exact: true,
  });
  await escapeTrigger.focus();
  await page.keyboard.press("Enter");
  const escapeDialog = page.locator("dialog.search-grid-value-dialog[open]");
  await escapeDialog.waitFor({ state: "visible" });
  await page.keyboard.press("Escape");
  await escapeDialog.waitFor({ state: "hidden" });
  assert.equal(
    await escapeTrigger.evaluate(
      (element) => document.activeElement === element,
    ),
    true,
    "Escape closes the shared dialog and restores focus to its trigger",
  );

  const initialSearchCount = requestLog.filter(
    (request) => request.pathname === "/v1/test-results/search-page",
  ).length;
  const originalUrl = page.url();
  const statusTrigger = page.getByRole("button", {
    name: "Filter Result status",
    exact: true,
  });
  await statusTrigger.focus();
  await page.keyboard.press("Enter");
  const statusMenu = page.getByRole("dialog", {
    name: "Result status column filter",
  });
  await statusMenu.waitFor({ state: "visible" });
  assert.equal(
    await statusMenu.evaluate(
      (menu) =>
        menu.contains(document.activeElement) &&
        document.activeElement instanceof HTMLInputElement,
    ),
    true,
    "keyboard opening moves focus into the column editor",
  );
  await statusMenu.locator('input[value="FAILED"]').check();
  await page.locator(".draft-notice").waitFor();
  assert.equal(
    page.url(),
    originalUrl,
    "editing a column only updates the draft",
  );
  assert.equal(
    requestLog.filter(
      (request) => request.pathname === "/v1/test-results/search-page",
    ).length,
    initialSearchCount,
    "draft edits do not fetch result rows",
  );
  await page.keyboard.press("Escape");
  await page.waitForFunction(
    () =>
      document.activeElement?.getAttribute("aria-label") ===
      "Filter Result status",
  );
  const beforeApply = await page
    .locator("tbody tr")
    .first()
    .locator('td[data-col-id="execution"]')
    .innerText();
  const appliedResponse = page.waitForResponse((response) => {
    const url = new URL(response.url());
    return (
      url.pathname === "/v1/test-results/search-page" &&
      url.searchParams.get("test_result_statuses") === "FAILED"
    );
  });
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await page.waitForURL(
    (url) => url.searchParams.get("test_result_statuses") === "FAILED",
  );
  assert.equal((await appliedResponse).status(), 200);
  await page.waitForFunction(
    (id) =>
      [...document.querySelectorAll('tbody td[data-col-id="execution"]')].some(
        (cell) => cell.textContent.trim() === String(id),
      ),
    7000,
  );
  const filterRequest = [...requestLog]
    .reverse()
    .find(
      (request) =>
        request.pathname === "/v1/test-results/search-page" &&
        request.search.includes("test_result_statuses=FAILED"),
    );
  assert.ok(
    filterRequest,
    "Search sends the applied exact filter to the server endpoint",
  );
  assert.equal(
    await page
      .locator("tbody tr")
      .first()
      .locator('td[data-col-id="execution"]')
      .innerText(),
    beforeApply,
    "the client does not locally remove a row returned by the server mock",
  );
  assert.equal(
    await page.locator('button[aria-label*="Sort"]').count(),
    0,
    "local sort controls are not exposed",
  );
  assert.equal(
    await page
      .locator(
        ".sv-grid-column-filter, .sv-grid-filter-operator-btn, .sv-grid-menu-operator-select",
      )
      .count(),
    0,
    "generic client-side filter/operator controls are not exposed",
  );

  const backResponse = page.waitForResponse((response) => {
    const url = new URL(response.url());
    return (
      url.pathname === "/v1/test-results/search-page" &&
      !url.searchParams.has("test_result_statuses")
    );
  });
  await page.goBack({ waitUntil: "domcontentloaded" });
  await page.waitForURL((url) => !url.searchParams.has("test_result_statuses"));
  assert.equal((await backResponse).status(), 200);
  await page
    .locator('tbody tr td[data-col-id="details"] button')
    .first()
    .waitFor();
  const forwardResponse = page.waitForResponse((response) => {
    const url = new URL(response.url());
    return (
      url.pathname === "/v1/test-results/search-page" &&
      url.searchParams.get("test_result_statuses") === "FAILED"
    );
  });
  await page.goForward({ waitUntil: "domcontentloaded" });
  await page.waitForURL(
    (url) => url.searchParams.get("test_result_statuses") === "FAILED",
  );
  assert.equal((await forwardResponse).status(), 200);
  await page
    .locator('tbody tr td[data-col-id="details"] button')
    .first()
    .waitFor();
  await page.reload({ waitUntil: "networkidle" });
  assert.equal(
    new URL(page.url()).searchParams.get("test_result_statuses"),
    "FAILED",
    "reload restores the applied URL condition",
  );
  await page.getByRole("button", { name: "Clear all", exact: true }).click();
  await page.waitForURL((url) => !url.searchParams.has("test_result_statuses"));
  assert.equal(
    new URL(page.url()).search,
    "",
    "Clear all removes the applied query and table-view URL",
  );
  await page
    .locator('tbody tr td[data-col-id="details"] button')
    .first()
    .waitFor();

  const detailRequestsBefore = requestLog.filter((request) =>
    request.pathname.includes("/search-page/"),
  ).length;
  const detailTrigger = page
    .locator('tbody tr td[data-col-id="details"] button')
    .first();
  const detailsUrl = page.url();
  await detailTrigger.focus();
  await page.keyboard.press("Enter");
  const detailsDialog = page.getByRole("dialog", {
    name: "Test result details",
  });
  await detailsDialog.waitFor({ state: "visible" });
  await detailsDialog
    .getByText("Execution Metadata", { exact: true })
    .waitFor();
  assert.equal(
    await detailsDialog.locator("table.execution-metadata tbody tr").count(),
    41,
    "on-demand Details includes every metadata category",
  );
  assert.equal(
    await detailsDialog.locator("table.execution-metadata tbody li").count(),
    82,
    "on-demand Details includes all metadata values",
  );
  assert.match(await detailsDialog.innerText(), /カテゴリー-41/);
  assert.equal(
    requestLog.filter((request) => request.pathname.includes("/search-page/"))
      .length,
    detailRequestsBefore + 1,
    "one ID-specific Details request is made only after activation",
  );
  assert.equal(
    page.url(),
    detailsUrl,
    "opening Details does not change query or URL",
  );
  await page.keyboard.press("Escape");
  await detailsDialog.waitFor({ state: "hidden" });
  assert.equal(
    await detailTrigger.evaluate(
      (element) => document.activeElement === element,
    ),
    true,
    "closing Details restores focus to its trigger",
  );
  assert.equal(
    requestLog.filter((request) => request.pathname.includes("/search-page/"))
      .length,
    detailRequestsBefore + 1,
    "closing Details does not fetch again",
  );

  await page.setViewportSize({ width: 800, height: 600 });
  await page.waitForTimeout(100);
  const narrowGeometry = await page.evaluate(() => {
    const grid = document.querySelector(".results-grid");
    const elements = [
      grid,
      ...Array.from(grid?.querySelectorAll("*") ?? []),
    ].filter(Boolean);
    const scrollables = elements
      .map((element) => {
        const style = getComputedStyle(element);
        return {
          element,
          className: element.className,
          clientWidth: element.clientWidth,
          scrollWidth: element.scrollWidth,
          clientHeight: element.clientHeight,
          scrollHeight: element.scrollHeight,
          overflowX: style.overflowX,
          overflowY: style.overflowY,
        };
      })
      .filter(
        (item) =>
          (item.scrollWidth > item.clientWidth + 1 &&
            /auto|scroll/.test(item.overflowX)) ||
          (item.scrollHeight > item.clientHeight + 1 &&
            /auto|scroll/.test(item.overflowY)),
      );
    return {
      viewport: { width: innerWidth, height: innerHeight },
      document: {
        clientWidth: document.documentElement.clientWidth,
        scrollWidth: document.documentElement.scrollWidth,
      },
      scrollables: scrollables.map(
        ({
          className,
          clientWidth,
          scrollWidth,
          clientHeight,
          scrollHeight,
          overflowX,
          overflowY,
        }) => ({
          className,
          clientWidth,
          scrollWidth,
          clientHeight,
          scrollHeight,
          overflowX,
          overflowY,
        }),
      ),
      rowHeights: Array.from(document.querySelectorAll("tbody tr"))
        .slice(0, 20)
        .map((row) => row.getBoundingClientRect().height),
    };
  });
  assert.equal(narrowGeometry.viewport.width, 800);
  const horizontal = await page.evaluate(async () => {
    const grid = document.querySelector(".results-grid");
    const candidates = [
      grid,
      ...Array.from(grid?.querySelectorAll("*") ?? []),
    ].filter(
      (element) =>
        element.scrollWidth > element.clientWidth + 1 &&
        /auto|scroll/.test(getComputedStyle(element).overflowX),
    );
    const target = candidates.sort(
      (a, b) => b.scrollWidth - b.clientWidth - (a.scrollWidth - a.clientWidth),
    )[0];
    if (!target) return null;
    const started = performance.now();
    target.scrollLeft = target.scrollWidth;
    await new Promise((resolve) =>
      requestAnimationFrame(() => requestAnimationFrame(resolve)),
    );
    return {
      className: target.className,
      clientWidth: target.clientWidth,
      scrollWidth: target.scrollWidth,
      scrollLeft: target.scrollLeft,
      settleMs: performance.now() - started,
    };
  });
  assert.ok(
    horizontal && horizontal.scrollWidth > horizontal.clientWidth,
    "narrow viewport retains a grid horizontal scroll range",
  );
  assert.ok(
    horizontal.scrollLeft > 0,
    "the grid can scroll horizontally to its far-right columns",
  );
  await page.evaluate(async () => {
    const container = document.querySelector(".sv-grid-container");
    if (!container) return;
    container.scrollLeft = 0;
    await new Promise((resolve) =>
      requestAnimationFrame(() => requestAnimationFrame(resolve)),
    );
  });
  const detailsHeader = page.locator('th[data-svgrid-header-col="details"]');
  await detailsHeader.waitFor();
  const headerGeometry = await detailsHeader.evaluate((header) => {
    const rect = header.getBoundingClientRect();
    return { left: rect.left, right: rect.right, width: rect.width };
  });
  assert.ok(
    headerGeometry.left < 800 && headerGeometry.right > 0,
    "the leading Details column is reachable at 800px",
  );
  const vertical = await page.evaluate(async () => {
    const grid = document.querySelector(".results-grid");
    const candidates = [
      grid,
      ...Array.from(grid?.querySelectorAll("*") ?? []),
    ].filter(
      (element) =>
        element.scrollHeight > element.clientHeight + 1 &&
        /auto|scroll/.test(getComputedStyle(element).overflowY),
    );
    const target = candidates.sort(
      (a, b) =>
        b.scrollHeight - b.clientHeight - (a.scrollHeight - a.clientHeight),
    )[0];
    if (!target) return null;
    const started = performance.now();
    target.scrollTop = target.scrollHeight;
    await new Promise((resolve) =>
      requestAnimationFrame(() => requestAnimationFrame(resolve)),
    );
    return {
      className: target.className,
      clientHeight: target.clientHeight,
      scrollHeight: target.scrollHeight,
      scrollTop: target.scrollTop,
      settleMs: performance.now() - started,
    };
  });
  assert.ok(
    vertical && vertical.scrollHeight > vertical.clientHeight,
    "the result grid retains a vertical scroll range for the loaded result block",
  );
  assert.ok(
    vertical.scrollTop > 0,
    "the loaded result block can be scrolled vertically",
  );
  await page.waitForFunction(() =>
    [...document.querySelectorAll('tbody td[data-col-id="execution"]')].some(
      (cell) => cell.textContent.trim() === "7049",
    ),
  );
  const metadataTrigger = page.getByRole("button", {
    name: "Filter Execution Metadata",
    exact: true,
  });
  await metadataTrigger.focus();
  await page.keyboard.press("Enter");
  const metadataMenu = page.getByRole("dialog", {
    name: "Execution Metadata column filter",
  });
  await metadataMenu.waitFor({ state: "visible" });
  const menuGeometry = await metadataMenu.evaluate((menu) => {
    const rect = menu.getBoundingClientRect();
    return {
      left: rect.left,
      right: rect.right,
      top: rect.top,
      bottom: rect.bottom,
    };
  });
  assert.ok(
    menuGeometry.left >= 0 &&
      menuGeometry.right <= 800 &&
      menuGeometry.top >= 0 &&
      menuGeometry.bottom <= 600,
    "the keyboard-opened far-right filter menu remains within the narrow viewport",
  );
  await page.keyboard.press("Escape");
  await page.waitForFunction(
    () =>
      document.activeElement?.getAttribute("aria-label") ===
      "Filter Execution Metadata",
  );

  const parseBench = await page.evaluate((body) => {
    const timings = [];
    let parsedRows = 0;
    for (let index = 0; index < 2; index += 1) JSON.parse(body);
    for (let index = 0; index < 10; index += 1) {
      const started = performance.now();
      const parsed = JSON.parse(body);
      timings.push(performance.now() - started);
      parsedRows = parsed.rows.length;
    }
    return {
      iterations: timings.length,
      parsedRows,
      minMs: Math.min(...timings),
      meanMs: timings.reduce((sum, value) => sum + value, 0) / timings.length,
      medianMs: [...timings].sort((a, b) => a - b)[
        Math.floor(timings.length / 2)
      ],
      maxMs: Math.max(...timings),
    };
  }, searchBody);
  const rowHeights = narrowGeometry.rowHeights;
  const sortedRowHeights = [...rowHeights].sort((a, b) => a - b);
  const browserMetrics = {
    fixture: {
      type: "synthetic, client-only mocked Search API fixture; not production/live API data",
      resultRows: rows.length,
      issueSummariesPerRow: 1,
      reviewerSummariesPerRow: 1,
      metadataCategoriesPerRow: categories.length,
      metadataValuesPerCategory: 2,
      metadataPairsPerRow: categories.length * 2,
      totalMetadataPairs: rows.length * categories.length * 2,
      maxCategoryCodePoints: Math.max(
        ...categories.map((item) => Array.from(item).length),
      ),
      maxValueCodePoints: Math.max(
        ...rows.flatMap((row, index) =>
          metadataPairs(index).map((pair) => Array.from(pair.value).length),
        ),
      ),
      noReviewerEmails: rows.every((row) =>
        row.artefact.reviewers.every((reviewer) => !("email" in reviewer)),
      ),
    },
    response: {
      uncompressedJsonUtf8Bytes: utf8Bytes,
      contentEncoding: "identity (route.fulfill body; no gzip/brotli) ",
      body: "same synthetic 50-row Search block used by the mock route",
    },
    parse: {
      actualSearchResponseJsonAndDecodeMs: initialJsonMetrics.parseAndDecodeMs,
      standaloneJsonParse: parseBench,
    },
    render: {
      msAfterSearchResponseJsonCompleteToFirstRowReadiness: initialRenderTimeMs,
      renderedRowsAtInitialViewport: initialRows,
      note: "waited for the first loaded Details cell; duration includes Svelte/SvGrid update plus a small Playwright observation delay",
    },
    rowHeightCssPx: {
      samples: rowHeights.length,
      min: Math.min(...rowHeights),
      median: sortedRowHeights[Math.floor(sortedRowHeights.length / 2)],
      max: Math.max(...rowHeights),
      allFixedHeight: new Set(rowHeights).size <= 1,
    },
    scrolling: {
      horizontal,
      vertical,
      narrowViewport: narrowGeometry,
      note: "programmatic horizontal scroll to max followed by two animation frames; settle time is not a smooth-wheel benchmark",
    },
  };
  assert.equal(parseBench.parsedRows, 50);
  assert.ok(
    pageErrors.length === 0,
    `browser page errors: ${pageErrors.join(" | ")}`,
  );
  passed = true;
  await page.screenshot({
    path: resolve(artifacts, "search-grid-800x600.png"),
    fullPage: false,
  });
  await writeFile(
    resolve(artifacts, "report.json"),
    JSON.stringify(
      {
        passed,
        mockedApiRequests: requestLog,
        checks: {
          orderedColumns: columnIds,
          columnCount: columnIds.length,
          filterGroups: filterTriggers,
          draftDoesNotFetchOrChangeUrl: true,
          searchAppliesUrlAndServerCondition: true,
          browserBackForwardReloadAndClearAll: true,
          keyboardHeaderOpenEscapeAndFocusReturn: true,
          compactRowsAndAllPairDialogs: valueDialogChecks,
          sharedValueDialog: {
            count: 1,
            centeredResponsiveBounds: {
              desktop: valueDialogVisuals,
              narrow: valueDialogNarrowVisuals,
            },
            internalScrollingAndFixedHeaderFooter: true,
            closeButtonRestoresEachTrigger: true,
            escapeRestoresFocus: true,
          },
          detailsFetchedOnDemandAndCloseRestoresFocus: true,
          localFilteringAndSortingDisabled: true,
          narrowViewportAndHorizontalNavigation: true,
        },
        metrics: browserMetrics,
        limitations: [
          "API is intercepted and returns synthetic fixture data; no production or live-stack behavior is evidenced.",
          "Mock deliberately returns the same rows for every filter to test that the browser does not re-filter rows locally.",
          "JSON response bytes are uncompressed UTF-8 route body bytes, not compressed wire bytes or server response sizes.",
          "Standalone parse benchmark is in this Chromium session and uses ten JSON.parse iterations after two warmups.",
          "Render interval begins after response.json completes and ends after initial row readiness plus the browser harness observation; it is not a controlled laboratory benchmark.",
          "Scroll settle timing measures an instant programmatic scroll and two animation frames, not wheel/trackpad throughput.",
        ],
      },
      null,
      2,
    ),
  );
  process.stdout.write(
    `Mocked Search browser QA: PASS (${artifacts}/report.json)\n`,
  );
} finally {
  if (browser) await browser.close();
  await server.close();
  if (!passed)
    process.stderr.write(
      "Mocked Search browser QA did not complete successfully.\n",
    );
}
