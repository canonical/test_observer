// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

// Optional live regression: run against Vite + the real API/SSO stack. Playwright
// is intentionally supplied outside this project's locked dependencies. Its
// dynamically loaded browser objects therefore have no local type declarations.
/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-return */
import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const { chromium } = await import(
  process.env.PLAYWRIGHT_MODULE ?? "playwright-core"
);
const searchUrl = new URL(
  process.env.SEARCH_URL ?? "http://localhost:30001/wip/test-results",
);
searchUrl.search = "test_result_statuses=PASSED,FAILED,SKIPPED&limit=50";
const artifacts =
  process.env.QA_ARTIFACT_DIR ?? "/tmp/opencode/search-view-history";
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
/** @type {string[]} */
const requests = [];
/** @type {string[]} */
const errors = [];
/** @type {Set<unknown>} */
const active = new Set();
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
// Do not persist arbitrary error messages from the login page: they could
// contain authentication URLs or payloads. Any uncaught error still fails QA.
page.on("pageerror", () => errors.push("Uncaught browser page error"));
const checks = [];
let passed = false;
let requestDelta = null;
let authentication = null;

async function settleApiRequests() {
  const deadline = Date.now() + 20000;
  while (active.size && Date.now() < deadline) await page.waitForTimeout(100);
  assert.equal(
    active.size,
    0,
    "API requests must finish before measuring traversal",
  );
}

// Resolve the actual Vite-served SvelteKit public modules, not a router mock or
// application-state hook. This regression deliberately exercises native popstate.
async function navigation(action, href, state) {
  await page.evaluate(
    async ({ action, href, state }) => {
      const resource = performance
        .getEntriesByType("resource")
        .find((entry) =>
          entry.name.includes("/runtime/app/navigation/index.js"),
        );
      if (!resource)
        throw new Error(
          "Run this browser regression against the Vite dev server.",
        );
      const nav = await import(resource.name);
      await nav[action](href, state);
    },
    { action, href, state },
  );
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
  assert.equal(loginUrl.searchParams.get("return_to"), searchUrl.href);
  const requiresLogin = !!(await page
    .locator('.results a[href*="/auth/saml/login"]')
    .count());
  const suppliedCredentials =
    Boolean(process.env.TEST_OBSERVER_USERNAME) ||
    Boolean(process.env.TEST_OBSERVER_PASSWORD);
  if (suppliedCredentials || requiresLogin) {
    assert.ok(
      process.env.TEST_OBSERVER_USERNAME && process.env.TEST_OBSERVER_PASSWORD,
      "Provide SSO credentials through TEST_OBSERVER_USERNAME / TEST_OBSERVER_PASSWORD; do not store them in reports.",
    );
    // Use the application's real public login link even when anonymous result
    // reads are allowed in development. No API/session/store hooks or mocks.
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
      // Playwright call logs can include fill arguments; never print them.
      throw new Error("Real SSO login failed (sensitive details withheld).");
    }
  }
  authentication = await page.evaluate(
    async (url) => {
      // Match fetchApi's ordinary request defaults: the backend requires this
      // fixed, non-secret CSRF presence marker even for session-authenticated GETs.
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
  assert.equal(authentication.status, 200, "/me must succeed on the real API");
  if (suppliedCredentials || requiresLogin)
    assert.equal(
      authentication.authenticated,
      true,
      "/me must confirm a real authenticated browser session after SSO",
    );
  await page.locator(".results .sv-grid-root").waitFor();
  // SvGrid uses native table rows (implicit roles), not explicit role="row".
  await page
    .locator(
      ".results .sv-grid-body .sv-grid-row:not(.sv-grid-empty-row):not(.sv-grid-row-spacer)",
    )
    .first()
    .waitFor();
  await settleApiRequests();

  // Exercise a real URL-backed filter through native query history before
  // measuring the separate view-only traversal's zero-request guarantee.
  const initialQueryUrl = String(page.url());
  const testCaseQueryUrl = new URL(initialQueryUrl);
  testCaseQueryUrl.searchParams.set("test_cases", "smoke");
  const beforeQueryHistory = requests.length;
  await navigation("pushState", testCaseQueryUrl.href, {
    queryHistory: "test-case",
  });
  await page.waitForURL(testCaseQueryUrl.href);
  await settleApiRequests();
  const testCaseFilterActive = () =>
    page
      .getByRole("button", { name: "Filter Test case", exact: true })
      .evaluate((button) => button.classList.contains("active"));
  assert.equal(
    await testCaseFilterActive(),
    true,
    "URL predicates mark their column",
  );
  await page.reload();
  await page.locator(".results .sv-grid-root").waitFor();
  await settleApiRequests();
  assert.equal(
    await testCaseFilterActive(),
    true,
    "reload restores the query from its URL",
  );
  await page.evaluate(() => {
    history.back();
  });
  await page.waitForURL(initialQueryUrl);
  await settleApiRequests();
  assert.equal(
    await testCaseFilterActive(),
    false,
    "Back restores the prior URL query",
  );
  await page.evaluate(() => {
    history.forward();
  });
  await page.waitForURL(testCaseQueryUrl.href);
  await settleApiRequests();
  assert.equal(
    await testCaseFilterActive(),
    true,
    "Forward restores the test-case filter",
  );
  assert.ok(requests.length >= beforeQueryHistory + 3);

  const panel = page.locator(
    '.menu-anchor[role="dialog"][aria-label="Test case column filter"]',
  );
  await page
    .getByRole("button", { name: "Filter Test case", exact: true })
    .click();
  await panel
    .locator('[data-search-grid-filter="test_cases"]')
    .fill("draft case");
  await settleApiRequests();
  assert.equal(
    await panel.locator('[data-search-grid-filter="test_cases"]').inputValue(),
    "draft case",
    "an unapplied exact filter remains a draft",
  );
  await page.evaluate(() => {
    window.__historyRegression = {
      input: document.activeElement,
      editor: document.querySelector(
        '.menu-anchor[aria-label="Test case column filter"]',
      ),
      popover: document.querySelector(
        '.menu-anchor[aria-label="Test case column filter"]',
      ),
      grid: document.querySelector(".sv-grid-root"),
      inert: [],
      focusout: 0,
      overlays: 0,
    };
    const evidence = window.__historyRegression;
    evidence.input.addEventListener("focusout", () => evidence.focusout++);
    new MutationObserver((mutations) => {
      for (const mutation of mutations)
        evidence.inert.push({
          old: mutation.oldValue,
          current: mutation.target.getAttribute("inert"),
        });
    }).observe(document.querySelector(".page-content"), {
      attributes: true,
      attributeFilter: ["inert"],
      attributeOldValue: true,
    });
    new MutationObserver((mutations) => {
      for (const mutation of mutations)
        for (const node of mutation.addedNodes)
          if (
            node instanceof Element &&
            (node.matches(".loading-overlay") ||
              node.querySelector(".loading-overlay"))
          )
            evidence.overlays++;
    }).observe(document.querySelector(".content-region"), {
      childList: true,
      subtree: true,
    });
  });
  const initial = String(page.url());
  const state = { historyRegression: "preserved" };
  await navigation("replaceState", initial, state);
  const before = requests.length;
  const viewUrl = new URL(initial);
  viewUrl.searchParams.set(
    "view",
    Buffer.from(JSON.stringify({ hiddenColumns: ["version"] })).toString(
      "base64url",
    ),
  );
  await navigation("pushState", viewUrl.href, state);
  await page.waitForFunction(
    () => !document.querySelector('th[data-svgrid-header-col="version"]'),
  );

  for (let cycle = 0; cycle < 2; cycle++) {
    for (const direction of ["back", "forward"]) {
      await page.evaluate((direction) => history[direction](), direction);
      await page.waitForURL(direction === "back" ? initial : viewUrl.href);
      await page.waitForFunction(
        (hidden) =>
          Boolean(
            document.querySelector('th[data-svgrid-header-col="version"]'),
          ) !== hidden,
        direction === "forward",
      );
      // Allow navigation completion and native inert/focusout events to settle.
      await page.waitForTimeout(150);
      const evidence = await page.evaluate(async () => {
        const resource = performance
          .getEntriesByType("resource")
          .find((entry) => entry.name.includes("/runtime/app/state/index.js"));
        const { page } = await import(resource.name);
        const saved = window.__historyRegression;
        return {
          focused: document.activeElement === saved.input,
          sameInput:
            document.querySelector('[data-search-grid-filter="test_cases"]') ===
            saved.input,
          sameEditor:
            document.querySelector(
              '.menu-anchor[aria-label="Test case column filter"]',
            ) === saved.editor,
          samePopover:
            document.querySelector(
              '.menu-anchor[aria-label="Test case column filter"]',
            ) === saved.popover,
          sameGrid: document.querySelector(".sv-grid-root") === saved.grid,
          open: !document.querySelector(
            '.menu-anchor[aria-label="Test case column filter"]',
          )?.hidden,
          draftValue: saved.input.value,
          notice: !!document.querySelector(".draft-notice"),
          focusout: saved.focusout,
          inert: saved.inert,
          overlays: saved.overlays,
          overlayPresent: !!document.querySelector(".loading-overlay"),
          pageState: page.state,
        };
      });
      checks.push({ cycle, direction, ...evidence });
      assert.equal(
        evidence.focused,
        true,
        `${direction} must preserve editor focus`,
      );
      assert.equal(
        evidence.sameInput &&
          evidence.sameEditor &&
          evidence.samePopover &&
          evidence.sameGrid &&
          evidence.open &&
          evidence.notice,
        true,
      );
      assert.equal(evidence.draftValue, "draft case");
      assert.equal(
        evidence.focusout,
        0,
        "focus must never leave, even transiently",
      );
      assert.deepEqual(
        evidence.inert,
        [],
        "shallow history must never inert the page",
      );
      assert.deepEqual(evidence.pageState, state);
      assert.equal(evidence.overlays, 0, "no even transient loading overlay");
      assert.equal(evidence.overlayPresent, false);
    }
  }
  requestDelta = requests.length - before;
  assert.equal(
    requestDelta,
    0,
    "view-only native history must not request the backend",
  );
  assert.deepEqual(errors, []);
  passed = true;
} finally {
  // Never save credentials, cookies, tokens or storageState; only assertions.
  await writeFile(
    resolve(artifacts, "report.json"),
    JSON.stringify(
      { passed, authentication, checks, requestDelta, errors },
      null,
      2,
    ),
  );
  if (await page.locator(".search-page .sv-grid-root").count())
    await page
      .locator(".search-page")
      .screenshot({ path: resolve(artifacts, "history.png") });
  await browser.close();
  process.stdout.write(
    `Native search-view history regression: ${passed ? "PASS" : "FAIL"}; ${checks.length} traversal checks; report ${resolve(artifacts, "report.json")}\n`,
  );
}
