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
  const path = new URL(String(request.url())).pathname;
  if (path.startsWith("/v1/")) {
    requests.push(path);
    active.add(request);
  }
});
context.on("requestfinished", (request) => active.delete(request));
context.on("requestfailed", (request) => active.delete(request));
page.on("pageerror", (error) => errors.push(String(error)));
const checks = [];
let passed = false;
let requestDelta = null;

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
  if (await page.locator('.results a[href*="/auth/saml/login"]').count()) {
    assert.ok(
      process.env.TEST_OBSERVER_USERNAME && process.env.TEST_OBSERVER_PASSWORD,
      "Provide SSO credentials through TEST_OBSERVER_USERNAME / TEST_OBSERVER_PASSWORD; do not store them in reports.",
    );
    await page
      .locator("section.search-page")
      .getByRole("link", { name: "Log in", exact: true })
      .click();
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
  }
  await page.locator(".results .sv-grid-root").waitFor();
  const deadline = Date.now() + 20000;
  while (active.size && Date.now() < deadline) await page.waitForTimeout(100);
  assert.equal(
    active.size,
    0,
    "initial API requests must finish before measuring traversal",
  );

  const panel = page.locator(".condition-popover:popover-open");
  await page.getByRole("button", { name: "+ Add filter", exact: true }).click();
  await panel
    .getByRole("button", { name: "Artefact names", exact: true })
    .click();
  await panel
    .getByLabel("Exact values", { exact: true })
    .fill("confirmed-but-unapplied");
  await panel.getByRole("button", { name: "Add filter", exact: true }).click();
  await page
    .locator('.chip-trigger[aria-label^="Edit Artefact names:"]')
    .click();
  await panel
    .getByLabel("Exact values", { exact: true })
    .fill("unconfirmed-editor-text");
  await page.evaluate(() => {
    window.__historyRegression = {
      input: document.activeElement,
      grid: document.querySelector(".sv-grid-root"),
      inert: [],
      focusout: 0,
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
  });
  const initial = String(page.url());
  const state = { historyRegression: "preserved" };
  await navigation("replaceState", initial, state);
  const before = requests.length;
  const viewUrl = new URL(initial);
  viewUrl.searchParams.set(
    "view",
    Buffer.from(JSON.stringify({ globalFilter: "test" })).toString("base64url"),
  );
  await navigation("pushState", viewUrl.href, state);
  await page.waitForFunction(
    () =>
      document.querySelector(".sv-grid-global-filter input")?.value === "test",
  );

  for (let cycle = 0; cycle < 2; cycle++) {
    for (const direction of ["back", "forward"]) {
      await page.evaluate((direction) => history[direction](), direction);
      await page.waitForURL(direction === "back" ? initial : viewUrl.href);
      await page.waitForFunction(
        (expected) =>
          document.querySelector(".sv-grid-global-filter input")?.value ===
          expected,
        direction === "back" ? "" : "test",
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
            document.querySelector('input[name="artefacts"]') === saved.input,
          sameGrid: document.querySelector(".sv-grid-root") === saved.grid,
          open: !!document.querySelector(".condition-popover:popover-open"),
          confirmed: document
            .querySelector('.chip-trigger[aria-label^="Edit Artefact names:"]')
            ?.getAttribute("title"),
          unconfirmed: saved.input.value,
          notice: !!document.querySelector(".draft-notice"),
          focusout: saved.focusout,
          inert: saved.inert,
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
          evidence.sameGrid &&
          evidence.open &&
          evidence.notice,
        true,
      );
      assert.equal(
        evidence.confirmed,
        "Artefact names: confirmed-but-unapplied",
      );
      assert.equal(evidence.unconfirmed, "unconfirmed-editor-text");
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
    JSON.stringify({ passed, checks, requestDelta, errors }, null, 2),
  );
  if (await page.locator(".search-page .sv-grid-root").count())
    await page.screenshot({ path: resolve(artifacts, "history.png") });
  await browser.close();
  process.stdout.write(
    `Native search-view history regression: ${passed ? "PASS" : "FAIL"}; ${checks.length} traversal checks; report ${resolve(artifacts, "report.json")}\n`,
  );
}
