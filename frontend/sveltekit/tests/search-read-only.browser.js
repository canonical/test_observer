// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

// Optional read-only browser regression against a local API/TEST SSO stack.
// Playwright is supplied externally, as in the other *.browser.js runners.
/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access */
import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const { chromium } = await import(
  process.env.PLAYWRIGHT_MODULE ?? "playwright-core"
);
const url = new URL(
  process.env.SEARCH_URL ?? "http://localhost:30001/wip/test-results",
);
url.search = "";
const artifacts = resolve(
  process.env.QA_ARTIFACT_DIR ?? "/tmp/opencode/search-read-only",
);
await mkdir(artifacts, { recursive: true });
const browser = await chromium.launch({
  headless: true,
  args: ["--no-sandbox"],
  ...(process.env.CHROMIUM_EXECUTABLE
    ? { executablePath: process.env.CHROMIUM_EXECUTABLE }
    : {}),
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(15000);
const errors = [];
const mutations = [];
const requests = [];
let auditMutations = false;
page.on("pageerror", () => errors.push("Uncaught browser page error"));
page.on("request", (request) => {
  const parsed = new URL(String(request.url()));
  requests.push({ method: String(request.method()), url: parsed });
  if (
    auditMutations &&
    parsed.pathname.startsWith("/v1/") &&
    !["GET", "HEAD", "OPTIONS"].includes(String(request.method()))
  )
    mutations.push("Unexpected mutation request");
});

try {
  await page.goto(url.href);
  const login = page.locator('a[href*="/v1/auth/saml/login"]').first();
  await login.waitFor();
  const loginUrl = new URL(String(await login.getAttribute("href")), url);
  try {
    assert.ok(
      process.env.TEST_OBSERVER_USERNAME && process.env.TEST_OBSERVER_PASSWORD,
    );
    await login.click();
    await page.locator('input[type="password"]').waitFor();
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
    await page.waitForURL(url.href);
  } catch {
    throw new Error("TEST SSO failed (sensitive details withheld).");
  }
  const authenticated = await page.evaluate(async (href) => {
    const response = await fetch(String(href), {
      credentials: "include",
      headers: { "X-CSRF-Token": "1" },
    });
    const user = response.ok ? await response.json() : null;
    return response.ok && Number.isSafeInteger(user?.id) && user.id > 0;
  }, new URL("/v1/users/me", loginUrl).href);
  assert.equal(authenticated, true);
  auditMutations = true;

  await page
    .locator('.sv-grid-body button[aria-label^="View details for "]')
    .first()
    .waitFor();
  const initialSearch = requests.find(({ url: requestUrl }) =>
    requestUrl.pathname.endsWith("/v1/test-results/search-page"),
  );
  assert.ok(initialSearch, "initial unfiltered recent range was requested");
  assert.equal(initialSearch.method, "GET");
  assert.equal(initialSearch.url.searchParams.get("limit"), "50");
  assert.equal(initialSearch.url.searchParams.get("offset"), "0");
  assert.deepEqual(
    [...initialSearch.url.searchParams.keys()],
    ["offset", "limit", "include_count"],
    "the initial request carries an explicit range and no search conditions",
  );

  assert.equal(
    await page.locator('.results input[type="checkbox"]').count(),
    0,
  );
  assert.equal(
    await page.getByRole("button", { name: "Bulk actions" }).count(),
    0,
  );
  assert.equal(
    await page.getByRole("button", { name: /Create Attachment Rule/ }).count(),
    0,
  );
  const trigger = page
    .locator('.sv-grid-body button[aria-label^="View details for "]')
    .first();
  const row = trigger.locator("xpath=ancestor::tr");
  const run = row.locator('[data-col-id="run"] a');
  const runHref = await run.getAttribute("href");
  assert.ok(runHref, "Run remains available in the unfiltered recent range");
  const priorUrl = page.url();
  const beforeDetails = requests.length;
  await trigger.click();
  const dialog = page.getByRole("dialog", { name: "Test result details" });
  await dialog.waitFor({ state: "visible" });
  await dialog.getByRole("button", { name: "Close", exact: true }).click();
  await dialog.waitFor({ state: "hidden" });
  assert.equal(page.url(), priorUrl);
  assert.equal(requests.length, beforeDetails + 1);
  assert.ok(
    requests
      .at(-1)
      ?.url.pathname.match(/\/v1\/test-results\/search-page\/\d+$/),
    "Details loads through its ID-specific API",
  );

  // An active external filter must not leave SvGrid's generic funnel on top
  // of Search's custom trigger when a wide grid is horizontally scrolled.
  const pointerUrl = new URL(String(page.url()));
  pointerUrl.search = new URLSearchParams([
    ["template_ids", "search-grid-pointer-regression"],
  ]).toString();
  await page.setViewportSize({ width: 800, height: 600 });
  await page.goto(pointerUrl.href);
  const templateTrigger = page.getByRole("button", {
    name: "Filter Template ID",
    exact: true,
  });
  await templateTrigger.waitFor();
  await page.waitForFunction(() =>
    document.querySelector(
      'th[data-svgrid-header-col="templateId"] .sv-grid-col-filter-btn.is-active',
    ),
  );
  assert.ok(
    requests.some(
      ({ url: requestUrl }) =>
        requestUrl.pathname === "/v1/test-results/search-page" &&
        requestUrl.searchParams.get("template_ids") ===
          "search-grid-pointer-regression",
    ),
    "the active narrow header represents an applied server-side template ID",
  );
  await templateTrigger.scrollIntoViewIfNeeded();
  const genericFilter = page.locator(
    'th[data-svgrid-header-col="templateId"] .sv-grid-col-filter-btn.is-active',
  );
  assert.equal(
    await genericFilter.count(),
    1,
    "SvGrid retains external active filter state",
  );
  assert.equal(
    await genericFilter.evaluate(
      /** @param {HTMLElement} button */
      (button) => getComputedStyle(button).display,
    ),
    "none",
    "Search does not expose the generic SvGrid operator control",
  );
  assert.equal(
    await page
      .locator(
        ".sv-grid-column-filter, .sv-grid-filter-operator-btn, .sv-grid-menu-operator-select, .sv-grid-menu-condition-value",
      )
      .count(),
    0,
    "Search does not expose local filter inputs or generic operators",
  );
  const receivesPointer = await templateTrigger.evaluate(
    /** @param {HTMLElement} button */
    (button) => {
      const rect = button.getBoundingClientRect();
      const hit = document.elementFromPoint(
        rect.left + rect.width / 2,
        rect.top + rect.height / 2,
      );
      return hit === button || button.contains(hit);
    },
  );
  assert.equal(
    receivesPointer,
    true,
    "the custom header button owns its pointer hit target",
  );
  await templateTrigger.click();
  const templateMenu = page.getByRole("dialog", {
    name: "Template ID column filter",
  });
  await templateMenu.waitFor({ state: "visible" });
  await page.keyboard.press("Escape");
  await templateMenu.waitFor({ state: "hidden" });
  await page.waitForFunction(
    () =>
      document.activeElement?.getAttribute("aria-label") ===
      "Filter Template ID",
  );

  assert.deepEqual(errors, []);
  assert.deepEqual(mutations, []);
  await writeFile(
    resolve(artifacts, "report.json"),
    JSON.stringify(
      {
        passed: true,
        authenticated,
        initialRequest: {
          method: initialSearch.method,
          limit: initialSearch.url.searchParams.get("limit"),
          offset: initialSearch.url.searchParams.get("offset"),
          filters: [],
        },
        runHref,
        noSelectionOrMutationControls: true,
        detailsLoadsOnDemand: true,
        mutations,
        errors,
      },
      null,
      2,
    ),
  );
  process.stdout.write("Read-only Search surface: PASS.\n");
} finally {
  await browser.close();
}
