// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

// Opt-in real API/TEST SSO + native Chromium regression. No success-path mocks,
// seed changes, app-state hooks, project dependencies, traces or storage dumps.
// Playwright is loaded externally, as in search-view-history.browser.js.
/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-return */
import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { assertDetailsLayout } from "./details-layout.browser.js";

assert.ok(
  process.env.TEST_OBSERVER_USERNAME && process.env.TEST_OBSERVER_PASSWORD,
  "Provide TEST SSO credentials privately via TEST_OBSERVER_USERNAME and TEST_OBSERVER_PASSWORD.",
);
const { chromium } = await import(
  process.env.PLAYWRIGHT_MODULE ?? "playwright-core"
);
const searchUrl = new URL(
  process.env.SEARCH_URL ?? "http://localhost:30001/wip/test-results",
);
searchUrl.search = "test_result_statuses=PASSED,FAILED,SKIPPED&limit=50";
const base = searchUrl.pathname.replace(/\/test-results\/?$/, "");
const artifacts = process.env.QA_ARTIFACT_DIR ?? "/tmp/opencode/search-details";
await mkdir(artifacts, { recursive: true });
const browser = await chromium.launch({
  headless: true,
  args: ["--no-sandbox"],
  ...(process.env.CHROMIUM_EXECUTABLE
    ? { executablePath: process.env.CHROMIUM_EXECUTABLE }
    : {}),
});
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
});
const page = await context.newPage();
page.setDefaultTimeout(15000);
const dialog = page.locator("dialog.search-result-details");
const checks = [];
const errors = [];
/** @type {string[]} */
const requests = [];
const active = new Set();
let rows = [];
const detailsById = new Map();
let authentication = null;
let passed = false;
const limits = [
  "Live data is never mutated: empty/populated optional sections are checked only where present in the real loaded page. Large/complex/malicious examples and zoom are covered by the separate actual-component browser fixture, not claimed as live data evidence.",
];
context.on("request", (request) => {
  const browserPath = new URL(String(request.url())).pathname;
  const path = browserPath.startsWith("/api/")
    ? browserPath.slice("/api".length)
    : browserPath;
  if (path.startsWith("/v1/")) {
    requests.push(path);
    active.add(request);
  }
});
context.on("requestfinished", (request) => active.delete(request));
context.on("requestfailed", (request) => active.delete(request));
page.on("pageerror", () => errors.push("Uncaught browser page error"));
page.on("response", async (response) => {
  const url = new URL(String(response.url()));
  const path = url.pathname.startsWith("/api/")
    ? url.pathname.slice("/api".length)
    : url.pathname;
  if (!response.ok()) return;
  if (path === "/v1/test-results/search-page") {
    const offset = Number(url.searchParams.get("offset"));
    const pageRows = (await response.json()).rows;
    if (offset === 0 || rows.length === 0) rows = pageRows;
  } else if (path.startsWith("/v1/test-results/search-page/")) {
    const details = await response.json();
    detailsById.set(details.test_result.id, details);
  }
});

async function settle() {
  await page.waitForTimeout(400); // include view polling and any debounced lookup
  const deadline = Date.now() + 20000;
  while (active.size && Date.now() < deadline) await page.waitForTimeout(100);
  assert.equal(
    active.size,
    0,
    "Finish existing API requests before zero-traffic intervals",
  );
}

async function navigation(action, href) {
  await page.evaluate(
    async ({ action, href }) => {
      const resource = performance
        .getEntriesByType("resource")
        .find((entry) =>
          entry.name.includes("/runtime/app/navigation/index.js"),
        );
      if (!resource)
        throw new Error("Run this regression against Vite's dev server");
      const nav = await import(resource.name);
      await nav[action](href, { detailsRegression: true });
    },
    { action, href },
  );
}

async function openDetails(trigger) {
  const before = requests.length;
  const href = String(page.url());
  const resultId = Number(await trigger.getAttribute("data-test-result-id"));
  await trigger.click();
  await dialog.waitFor({ state: "visible" });
  await dialog.locator("h3").first().waitFor();
  await page.waitForTimeout(150);
  assert.equal(
    await dialog.evaluate((element) => element.matches(":modal")),
    true,
  );
  assert.equal(
    await dialog
      .getByRole("heading", { name: "Test result details", exact: true })
      .count(),
    1,
  );
  assert.equal(await page.locator("dialog.search-result-details").count(), 1);
  assert.equal(String(page.url()), href, "Details never writes the URL");
  assert.equal(
    requests.length,
    before + 1,
    "Opening Details loads one detail record",
  );
  const detailPath = requests.at(-1);
  assert.ok(detailPath);
  assert.match(detailPath, /\/v1\/test-results\/search-page\/\d+$/);
  assert.ok(
    detailsById.has(resultId),
    "Details response is available for the selected ID",
  );
}

async function closeDetails(trigger, method) {
  const before = requests.length;
  const href = String(page.url());
  if (method === "Escape") await page.keyboard.press("Escape");
  else if (method === "backdrop") await page.mouse.click(5, 5);
  else await dialog.getByRole("button", { name: method, exact: true }).click();
  await dialog.waitFor({ state: "hidden" });
  await page.waitForTimeout(150);
  assert.equal(
    await trigger.evaluate((element) => document.activeElement === element),
    true,
    `${method} restores the Details trigger`,
  );
  assert.equal(String(page.url()), href);
  assert.equal(requests.length, before, "Closing Details never calls the API");
}

try {
  await page.goto(searchUrl.href);
  await page.waitForFunction(() =>
    /matching test results on the server|need to be logged in/.test(
      document.querySelector(".results")?.textContent ?? "",
    ),
  );
  const login = page.locator('a[href*="/v1/auth/saml/login"]').first();
  const loginUrl = new URL(String(await login.getAttribute("href")), searchUrl);
  const proxiedApi = loginUrl.pathname.startsWith("/api/v1/");
  assert.equal(
    proxiedApi || loginUrl.pathname === "/v1/auth/saml/login",
    true,
    "login uses either the same-origin proxy or the development API origin",
  );
  try {
    await login.click();
    await page.locator('input[type="password"]').waitFor({ timeout: 30000 });
    await page
      .locator('input[name="username"], input#username')
      .first()
      .fill(process.env.TEST_OBSERVER_USERNAME);
    await page
      .locator('input[type="password"]')
      .fill(process.env.TEST_OBSERVER_PASSWORD);
    await page
      .locator('button[type="submit"], input[type="submit"]')
      .first()
      .click();
    await page.waitForURL(searchUrl.href, { timeout: 30000 });
  } catch {
    throw new Error("Real SSO login failed (sensitive details withheld).");
  }
  authentication = await page.evaluate(
    async (url) => {
      const response = await fetch(String(url), {
        credentials: "include",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": "1" },
      });
      const user = response.ok ? await response.json() : null;
      return {
        status: response.status,
        authenticated: Number.isSafeInteger(user?.id) && user.id > 0,
      };
    },
    new URL(
      proxiedApi ? "/api/v1/users/me" : "/v1/users/me",
      proxiedApi ? searchUrl : loginUrl,
    ).href,
  );
  assert.deepEqual(authentication, { status: 200, authenticated: true });
  await page
    .locator('.sv-grid-body button[aria-label^="View details for "]')
    .first()
    .waitFor();
  await settle();
  assert.ok(rows.length > 1, "Real seeded data must contain multiple results");

  const headerOrder = await page
    .locator(".results thead th")
    .evaluateAll((elements) =>
      elements
        .slice(0, 3)
        .map((element) => element.getAttribute("data-svgrid-header-col")),
    );
  assert.deepEqual(headerOrder, ["createdAt", "artefact", "testCase"]);
  assert.equal(
    await page.locator('.results input[type="checkbox"]').count(),
    0,
    "Search is read-only and has no row-selection checkboxes",
  );
  assert.equal(
    await page.getByRole("button", { name: "Bulk actions" }).count(),
    0,
  );
  assert.equal(
    await page.getByRole("button", { name: /Create Attachment Rule/ }).count(),
    0,
  );
  assert.equal(await page.locator(".sv-grid-header-icon-hint").count(), 0);
  assert.equal(await page.locator(".sv-grid-filter-button").count(), 0);
  assert.equal(await page.locator(".sv-grid-global-filter").count(), 0);
  const trigger = page
    .locator('.sv-grid-body button[aria-label^="View details for "]')
    .first();
  const id = Number(await trigger.getAttribute("data-test-result-id"));
  const raw = rows.find((row) => row.test_result.id === id);
  assert.ok(raw, "Visible ID maps to a raw record in newest-first API order");
  const runHref = await trigger
    .locator("xpath=ancestor::tr")
    .locator('[data-col-id="run"] a')
    .getAttribute("href");
  assert.ok(runHref.startsWith(`${base}/`));
  const run = new URL(String(runHref), searchUrl);
  assert.equal(
    run.searchParams.get("testExecutionId"),
    String(raw.test_execution.id),
  );
  assert.equal(run.searchParams.get("testResultId"), String(id));

  for (const width of [1920, 1440, 960, 800]) {
    await page.setViewportSize({ width, height: 900 });
    for (const theme of ["light", "dark"]) {
      for (
        let step = 0;
        step < 3 &&
        !(await page
          .locator("html")
          .evaluate((el, theme) => el.classList.contains(theme), theme));
        step++
      )
        await page
          .getByText(/^Theme: (Light|Dark|System)$/, { exact: true })
          .click();
      assert.equal(
        await page
          .locator("html")
          .evaluate((el, theme) => el.classList.contains(theme), theme),
        true,
      );
      await settle();
      const stableTrigger = page.locator(`button[data-test-result-id="${id}"]`);
      const iconGeometry = await stableTrigger.evaluate((element) => {
        const icon = element.querySelector(".details-icon svg");
        const bounds = icon.getBoundingClientRect();
        const button = element.getBoundingClientRect();
        const cell = element.closest("td").getBoundingClientRect();
        return {
          width: bounds.width,
          height: bounds.height,
          buttonRight: button.right,
          cellRight: cell.right,
        };
      });
      assert.ok(Math.abs(iconGeometry.width - 16) < 0.1);
      assert.ok(Math.abs(iconGeometry.height - 16) < 0.1);
      assert.ok(
        iconGeometry.buttonRight < iconGeometry.cellRight,
        "Details keeps its eye and label inside the column at every typography breakpoint",
      );
      await stableTrigger.focus();
      const before = requests.length;
      await page.keyboard.press("Enter");
      await dialog.waitFor({ state: "visible" });
      await dialog.locator("h3").first().waitFor();
      assert.equal(await dialog.evaluate((el) => el.matches(":modal")), true);
      assert.equal(requests.length, before + 1);
      assert.match(requests.at(-1), /\/v1\/test-results\/search-page\/\d+$/);
      const rawDetails = detailsById.get(id);
      assert.ok(rawDetails);
      assert.equal(
        await dialog
          .getByRole("link", {
            name: `View Run for ${raw.test_result.name}`,
            exact: true,
          })
          .getAttribute("href"),
        runHref,
      );
      assert.equal(
        await dialog.locator("time").getAttribute("datetime"),
        new Date(String(rawDetails.test_execution.created_at)).toISOString(),
      );
      assert.equal(
        await dialog
          .locator("section")
          .first()
          .locator("dd")
          .first()
          .textContent(),
        raw.test_result.name,
      );
      /** @type {Record<string, string[]>} */
      const executionMetadata = rawDetails.test_execution.execution_metadata;
      const layout = await assertDetailsLayout(dialog, executionMetadata);
      const backgroundFocus = await page.evaluate(() => {
        const modal = document.querySelector("dialog.search-result-details");
        const controls = Array.from(
          document.querySelectorAll(
            ".search-page button:not(:disabled), .search-page input:not(:disabled)",
          ),
        ).filter((control) => control.getClientRects().length > 0);
        let leaked = false;
        for (const control of controls) {
          control.focus({ preventScroll: true });
          if (document.activeElement === control) leaked = true;
        }
        return {
          tested: controls.length,
          blocked: !leaked,
          modal: modal.matches(":modal"),
          inside: modal.contains(document.activeElement),
        };
      });
      assert.ok(
        backgroundFocus.tested > 0,
        "Exercise real background controls",
      );
      assert.equal(
        backgroundFocus.blocked,
        true,
        "Native modal blocks background application focus",
      );
      assert.equal(backgroundFocus.modal && backgroundFocus.inside, true);
      let browserChromeTransfers = 0;
      for (let i = 0; i < 18; i++) {
        await page.keyboard.press(i % 3 === 0 ? "Shift+Tab" : "Tab");
        const focus = await dialog.evaluate((el) => ({
          modal: el.matches(":modal"),
          inside: el.contains(document.activeElement),
          body: document.activeElement === document.body,
          documentFocused: document.hasFocus(),
        }));
        assert.equal(
          focus.modal,
          true,
          "Keyboard traversal keeps the native modal open",
        );
        assert.equal(
          focus.inside === true ||
            (focus.body === true && focus.documentFocused === false),
          true,
          "Native traversal may reach browser chrome, never a background application control",
        );
        if (!focus.inside) {
          // Chromium can move from the first modal control to browser chrome on
          // Shift+Tab: BODY + !hasFocus(), also reproduced with a plain dialog.
          // This is not an app focus leak, but Tab must return to the modal.
          browserChromeTransfers++;
          await page.keyboard.press("Tab");
          assert.equal(
            await dialog.evaluate(
              (el) =>
                el.matches(":modal") &&
                document.hasFocus() &&
                el.contains(document.activeElement),
            ),
            true,
            "Tab returns from browser chrome to the native modal",
          );
        }
      }
      const geometry = await dialog.evaluate((element) => {
        const rect = element.getBoundingClientRect();
        const body = element.querySelector(".details-body");
        body.scrollTop = body.scrollHeight;
        const footer = element.querySelector("footer").getBoundingClientRect();
        return {
          width: rect.width,
          left: rect.left,
          right: rect.right,
          top: rect.top,
          bottom: rect.bottom,
          viewport: innerWidth,
          footerBottom: footer.bottom,
          bodyScroll: body.scrollTop,
          bodyOverflow: body.scrollHeight > body.clientHeight,
          pageScroll: document.scrollingElement.scrollTop,
        };
      });
      assert.ok(
        Math.abs(geometry.width - Math.min(900, width - 32)) <= 2,
        `Details must be about 900px on desktop and shrink only for viewport margins (actual ${geometry.width}px at ${width}px)`,
      );
      assert.ok(
        geometry.left >= 15 &&
          geometry.right <= width - 15 &&
          geometry.top >= 15 &&
          geometry.bottom <= 885,
      );
      assert.ok(geometry.footerBottom <= 885);
      if (geometry.bodyOverflow)
        assert.ok(
          geometry.bodyScroll > 0,
          "Modal body scroll reaches bottom independently of footer",
        );
      await dialog.getByRole("button", { name: "Close", exact: true }).hover();
      await page.mouse.wheel(0, 900);
      assert.equal(
        await page.evaluate(() => document.scrollingElement.scrollTop),
        geometry.pageScroll,
        "Background body does not scroll",
      );
      assert.equal(
        requests.length,
        before + 1,
        "Opening loads one detail record; traversal and scrolling add no requests",
      );
      await page.screenshot({
        path: resolve(artifacts, `details-${width}-${theme}.png`),
      });
      await closeDetails(stableTrigger, "Escape");
      for (const method of ["Close details", "Close", "backdrop"]) {
        await openDetails(stableTrigger);
        await closeDetails(stableTrigger, method);
        assert.equal(
          await page.locator('.results input[type="checkbox"]').count(),
          0,
        );
      }
      checks.push({
        width,
        theme,
        id,
        nativeFocusAndClose: true,
        browserChromeTransfers,
        backgroundFocusTargets: backgroundFocus.tested,
        noRequestsAfterDetailsLoaded: true,
        geometry,
        layout,
      });
    }
  }

  // Load modal-only fields for real rows, including optional issues/log data.
  const cases = [
    ...new Set(
      [
        rows.find((row) => row.test_result.issues?.length)?.test_result.id,
        rows[0]?.test_result.id,
        rows.find((row) => !row.test_result.issues?.length)?.test_result.id,
      ].filter(Boolean),
    ),
  ];
  for (const caseId of cases) {
    const rowIndex = rows.findIndex(
      (candidate) => candidate.test_result.id === caseId,
    );
    await page.locator(".sv-grid-container").evaluate((element, index) => {
      element.scrollTop = index * 32;
    }, rowIndex);
    await settle();
    const button = page.locator(`button[data-test-result-id="${caseId}"]`);
    await openDetails(button);
    const details = detailsById.get(caseId);
    assert.ok(details);
    /** @type {Record<string, string[]>} */
    const executionMetadata = details.test_execution.execution_metadata;
    await assertDetailsLayout(dialog, executionMetadata);
    const issues = details.test_result.issues ?? [];
    assert.equal(await dialog.locator(".issues a").count(), issues.length);
    for (const { issue } of issues) {
      const key = String(issue.key ?? "");
      const link = dialog.getByRole("link", {
        name: `View issue ${key.length ? key : String(issue.id)}`,
        exact: true,
      });
      assert.equal(
        await link.getAttribute("href"),
        `${base}/issues/${issue.id}`,
      );
      assert.equal(await link.getAttribute("target"), "_blank");
      assert.equal(await link.getAttribute("rel"), "noopener noreferrer");
    }
    assert.equal(
      await dialog.locator(".io-log").count(),
      details.test_result.io_log ? 1 : 0,
    );
    if (details.test_result.io_log)
      assert.equal(
        await dialog.locator(".io-log").textContent(),
        details.test_result.io_log,
      );
    await closeDetails(button, "Close");
    checks.push({
      optionalCaseId: caseId,
      issues: issues.length,
      hasLog: Boolean(details.test_result.io_log),
    });
  }
  if (
    !cases.some((caseId) => detailsById.get(caseId)?.test_result.issues?.length)
  )
    limits.push(
      "No real loaded row has an issue attachment; issue hrefs covered deterministically only.",
    );
  if (
    !cases.some((caseId) => {
      const details = detailsById.get(caseId);
      return (
        !details?.test_result.issues?.length && !details?.test_result.io_log
      );
    })
  )
    limits.push(
      "No real loaded row has both empty issues and empty log; empty sections covered deterministically only.",
    );
  await page.locator(".sv-grid-container").evaluate((element) => {
    element.scrollTop = 0;
  });
  await settle();

  // Column-menu drafts survive the modal, while native
  // public view-only Back/Forward leaves the same dialog and its focus in place.
  const panel = page.locator(
    '.menu-anchor[aria-label="Test case column filter"]',
  );
  await page
    .getByRole("button", { name: "Filter Test case", exact: true })
    .click();
  await panel
    .locator('[data-search-grid-filter="test_cases"]')
    .fill("draft one, draft two");
  await settle();
  const first = page
    .locator('.sv-grid-body button[aria-label^="View details for "]')
    .first();
  await openDetails(first);
  await dialog.getByRole("button", { name: "Close", exact: true }).focus();
  await page.evaluate(() => {
    window.__detailsRegression = {
      dialog: document.querySelector("dialog.search-result-details"),
      grid: document.querySelector(".sv-grid-root"),
      focus: document.activeElement,
      focusout: 0,
    };
    document.activeElement.addEventListener(
      "focusout",
      () => window.__detailsRegression.focusout++,
    );
  });
  const initial = String(page.url());
  const viewUrl = new URL(initial);
  viewUrl.searchParams.set(
    "view",
    Buffer.from(JSON.stringify({ hiddenColumns: ["track"] })).toString(
      "base64url",
    ),
  );
  const before = requests.length;
  await navigation("replaceState", initial);
  await navigation("pushState", viewUrl.href);
  for (const direction of ["back", "forward", "back", "forward"]) {
    await page.evaluate((direction) => history[direction](), direction);
    await page.waitForURL(direction === "back" ? initial : viewUrl.href);
    await page.waitForTimeout(150);
    const evidence = await page.evaluate(() => {
      const saved = window.__detailsRegression;
      return {
        sameDialog:
          document.querySelector("dialog.search-result-details") ===
          saved.dialog,
        sameGrid: document.querySelector(".sv-grid-root") === saved.grid,
        open: saved.dialog.matches(":modal"),
        focused: saved.focus === document.activeElement,
        focusout: saved.focusout,
      };
    });
    assert.deepEqual(evidence, {
      sameDialog: true,
      sameGrid: true,
      open: true,
      focused: true,
      focusout: 0,
    });
  }
  assert.equal(
    requests.length,
    before,
    "View-only modal history never queries",
  );
  const beforeClose = requests.length;
  await dialog.getByRole("button", { name: "Close", exact: true }).click();
  await dialog.waitFor({ state: "hidden" });
  await page.waitForTimeout(150);
  assert.equal(
    await page.evaluate(() =>
      document.activeElement.matches(
        ".results-grid, button[data-test-result-id]",
      ),
    ),
    true,
    "Restore the exact invoker or meaningful grid fallback after recycling",
  );
  assert.equal(requests.length, beforeClose);
  await page
    .getByRole("button", { name: "Filter Test case", exact: true })
    .click();
  assert.equal(
    await panel.locator('[data-search-grid-filter="test_cases"]').inputValue(),
    "draft one, draft two",
  );
  checks.push({
    viewOnlyHistoryFocus: true,
    columnDraftSurvivesDetails: true,
  });
  const current = page
    .locator('.sv-grid-body button[aria-label^="View details for "]')
    .first();
  await settle();
  await openDetails(current);
  // A meaningful backend query invalidates the loaded record. Unlike
  // the view-only intervals above, this transition intentionally fetches.
  const changedQuery = new URL(String(page.url()));
  changedQuery.searchParams.set("test_result_statuses", "PASSED");
  await navigation("pushState", changedQuery.href);
  await dialog.waitFor({ state: "hidden" });
  await settle();
  checks.push({ meaningfulQueryClosesModal: true });
  assert.deepEqual(errors, []);
  passed = true;
} finally {
  await writeFile(
    resolve(artifacts, "details-report.json"),
    JSON.stringify({ passed, authentication, checks, limits, errors }, null, 2),
  );
  await browser.close();
  process.stdout.write(
    `Native search Details regression: ${passed ? "PASS" : "FAIL"}; report ${resolve(artifacts, "details-report.json")}\n`,
  );
}
