// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

// Opt-in real API/TEST SSO + native Chromium regression. No success-path mocks,
// seed changes, app-state hooks, project dependencies, traces or storage dumps.
// Playwright is loaded externally, as in search-view-history.browser.js.
/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-return */
import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

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
const requests = [];
const active = new Set();
let rows = [];
let authentication = null;
let passed = false;
const limits = [
  "Live data is never mutated: empty/populated optional sections are checked only where present in the real loaded page. Huge/malicious logs, Unicode and absent configured families are deterministic mounted fixtures.",
];
context.on("request", (request) => {
  const path = new URL(String(request.url())).pathname;
  if (path.startsWith("/v1/")) {
    requests.push(path);
    active.add(request);
  }
});
context.on("requestfinished", (request) => active.delete(request));
context.on("requestfailed", (request) => active.delete(request));
page.on("pageerror", () => errors.push("Uncaught browser page error"));
page.on("response", async (response) => {
  if (
    new URL(String(response.url())).pathname === "/v1/test-results" &&
    response.ok()
  )
    rows = (await response.json()).test_results;
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
  await trigger.click();
  await dialog.waitFor({ state: "visible" });
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
  assert.equal(requests.length, before, "Opening Details never calls the API");
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
  assert.equal(loginUrl.pathname, "/v1/auth/saml/login");
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
  authentication = await page.evaluate(async (url) => {
    const response = await fetch(String(url), {
      credentials: "include",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": "1" },
    });
    const user = response.ok ? await response.json() : null;
    return {
      status: response.status,
      authenticated: Number.isSafeInteger(user?.id) && user.id > 0,
    };
  }, new URL("/v1/users/me", loginUrl).href);
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
        .slice(0, 4)
        .map(
          (element) =>
            element.getAttribute("data-svgrid-header-col") ??
            (element.classList.contains("sv-grid-selection-column")
              ? "selection"
              : "unknown"),
        ),
    );
  assert.deepEqual(headerOrder, ["selection", "run", "details", "artefact"]);
  await page
    .locator('[data-svgrid-header-col="testCase"] button.sv-grid-header-sort')
    .click();
  await settle();
  const trigger = page
    .locator('.sv-grid-body button[aria-label^="View details for "]')
    .first();
  const id = Number(await trigger.getAttribute("data-test-result-id"));
  const raw = rows.find((row) => row.test_result.id === id);
  assert.ok(
    raw,
    "Visible ID must map to a real raw API record after local sorting",
  );
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

  const header = page.getByRole("checkbox", {
    name: "Select all rows",
    exact: true,
  });
  await trigger
    .locator("xpath=ancestor::tr")
    .getByRole("checkbox", { name: "Select row", exact: true })
    .click();
  const explicit = await page
    .locator(".selection-summary p[role=status]")
    .textContent();
  await openDetails(trigger);
  await closeDetails(trigger, "Escape");
  assert.equal(
    await page.locator(".selection-summary p[role=status]").textContent(),
    explicit,
  );
  await header.click();
  const all = page.getByRole("checkbox", {
    name: /^Apply bulk options to all/,
  });
  await all.check();
  const exclusion = trigger
    .locator("xpath=ancestor::tr")
    .getByRole("checkbox", { name: "Select row", exact: true });
  await exclusion.click();
  const selected = await page
    .locator(".selection-summary p[role=status]")
    .textContent();
  assert.match(String(selected), /1 excluded/);
  const selectedId = String(await trigger.getAttribute("data-test-result-id"));

  for (const width of [1440, 960, 800]) {
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
      const stableTrigger = page.locator(
        `button[data-test-result-id="${selectedId}"]`,
      );
      await stableTrigger.focus();
      const before = requests.length;
      await page.keyboard.press("Enter");
      await dialog.waitFor({ state: "visible" });
      assert.equal(await dialog.evaluate((el) => el.matches(":modal")), true);
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
        new Date(String(raw.test_execution.created_at)).toISOString(),
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
        before,
        "Keyboard open/traversal/scroll is loaded-data only",
      );
      assert.equal(
        await page.locator(".selection-summary p[role=status]").textContent(),
        selected,
      );
      await page.screenshot({
        path: resolve(artifacts, `details-${width}-${theme}.png`),
      });
      await closeDetails(stableTrigger, "Escape");
      for (const method of ["Close details", "Close", "backdrop"]) {
        await openDetails(stableTrigger);
        await closeDetails(stableTrigger, method);
        assert.equal(await all.isChecked(), true);
        assert.equal(await exclusion.getAttribute("aria-checked"), "false");
        assert.equal(
          await page.locator(".selection-summary p[role=status]").textContent(),
          selected,
        );
      }
      checks.push({
        width,
        theme,
        id,
        nativeFocusAndClose: true,
        browserChromeTransfers,
        backgroundFocusTargets: backgroundFocus.tested,
        zeroTraffic: true,
        geometry,
      });
    }
  }

  // Real loaded optional sections, including a row with no issues/log where
  // available. Local filtering makes virtualized offscreen records reachable.
  const cases = [
    ...new Set(
      [
        rows.find((row) => row.test_result.issues?.length)?.test_result.id,
        rows.find((row) => row.test_result.io_log)?.test_result.id,
        rows.find(
          (row) => !row.test_result.issues?.length && !row.test_result.io_log,
        )?.test_result.id,
      ].filter(Boolean),
    ),
  ];
  for (const caseId of cases) {
    const row = rows.find((row) => row.test_result.id === caseId);
    await page
      .locator(".sv-grid-global-filter input")
      .fill(row.test_result.name);
    await settle();
    const button = page.locator(`button[data-test-result-id="${caseId}"]`);
    await openDetails(button);
    const issues = row.test_result.issues ?? [];
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
      row.test_result.io_log ? 1 : 0,
    );
    if (row.test_result.io_log)
      assert.equal(
        await dialog.locator(".io-log").textContent(),
        row.test_result.io_log,
      );
    await closeDetails(button, "Close");
    checks.push({
      optionalCaseId: caseId,
      issues: issues.length,
      hasLog: Boolean(row.test_result.io_log),
    });
  }
  if (!rows.some((row) => row.test_result.issues?.length))
    limits.push(
      "No real loaded row has an issue attachment; issue hrefs covered deterministically only.",
    );
  if (
    !rows.some(
      (row) => !row.test_result.issues?.length && !row.test_result.io_log,
    )
  )
    limits.push(
      "No real loaded row has both empty issues and empty log; empty sections covered deterministically only.",
    );
  await page.locator(".sv-grid-global-filter input").fill("");
  await settle();

  // Confirmed and unconfirmed editor state survives the modal, while native
  // public view-only Back/Forward leaves the same dialog and its focus in place.
  const panel = page.locator(".condition-popover:popover-open");
  await page.getByRole("button", { name: "+ Add filter", exact: true }).click();
  await panel.getByRole("button", { name: "Template ID", exact: true }).click();
  await panel.locator('input[name="template_ids"]').fill("confirmed draft");
  await panel.getByRole("button", { name: "Add filter", exact: true }).click();
  const chip = page.locator('.chip-trigger[aria-label^="Edit Template ID:"]');
  await chip.click();
  await panel.locator('input[name="template_ids"]').fill("unconfirmed draft");
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
    Buffer.from(
      JSON.stringify({ sorting: [{ id: "testCase", desc: true }] }),
    ).toString("base64url"),
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
  assert.equal(
    await chip.getAttribute("title"),
    "Template ID: confirmed draft",
  );
  await chip.click();
  assert.equal(
    await panel.locator('input[name="template_ids"]').inputValue(),
    "unconfirmed draft",
  );
  await page.keyboard.press("Escape");
  checks.push({
    viewOnlyHistoryFocus: true,
    confirmedAndUnconfirmedDrafts: true,
  });
  const current = page
    .locator('.sv-grid-body button[aria-label^="View details for "]')
    .first();
  await settle();
  await openDetails(current);
  // A meaningful backend query invalidates the selected loaded record. Unlike
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
