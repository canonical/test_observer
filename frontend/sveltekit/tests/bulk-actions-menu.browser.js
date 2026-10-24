// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

// Optional read-only browser regression against a local API/TEST SSO stack.
// Playwright is supplied externally, as in the other *.browser.js runners.
/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-return */
import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const { chromium } = await import(
  process.env.PLAYWRIGHT_MODULE ?? "playwright-core"
);
const url = new URL(
  process.env.SEARCH_URL ?? "http://localhost:30001/wip/test-results",
);
url.search = "families=snap&limit=50";
const artifacts = resolve(
  process.env.QA_ARTIFACT_DIR ?? "/tmp/opencode/bulk-menu-surface",
);
await mkdir(artifacts, { recursive: true });
const browser = await chromium.launch({
  headless: true,
  args: ["--no-sandbox"],
  ...(process.env.CHROMIUM_EXECUTABLE
    ? { executablePath: process.env.CHROMIUM_EXECUTABLE }
    : {}),
});
const page = await browser.newPage({ viewport: { width: 1853, height: 1000 } });
page.setDefaultTimeout(15000);
const errors = [];
const mutations = [];
const checks = [];
let auditMutations = false;
page.on("pageerror", () => errors.push("Uncaught browser page error"));
page.on("request", (request) => {
  if (
    auditMutations &&
    new URL(String(request.url())).pathname.startsWith("/v1/") &&
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
    .getByRole("checkbox", { name: "Select all rows", exact: true })
    .check();
  const summary = page.locator(
    ".selection-summary > p[role=status]:not(.bulk-disabled)",
  );
  const selected = await summary.textContent();
  const trigger = page.getByRole("button", {
    name: "Bulk actions",
    exact: true,
  });
  const menu = page.getByRole("menu", { name: "Bulk actions", exact: true });
  for (const width of [1853, 1440, 960, 800]) {
    await page.setViewportSize({ width, height: 1000 });
    for (const theme of ["light", "dark"]) {
      for (let attempt = 0; attempt < 3; attempt++) {
        if (
          await page
            .locator("html")
            .evaluate(
              (element, theme) => element.classList.contains(theme),
              theme,
            )
        )
          break;
        await page
          .getByText(/^Theme: (Light|Dark|System)$/, { exact: true })
          .click();
      }
      await trigger.click();
      await menu.waitFor({ state: "visible" });
      await page.waitForFunction(() => {
        const menu = document.querySelector(".bulk-actions-menu:popover-open");
        return menu && !menu.textContent.includes("Checking permissions");
      });
      const surface = await menu.evaluate(
        /** @param {HTMLElement} element */ (element) => {
          const style = getComputedStyle(element);
          const expected = document.createElement("span");
          expected.style.backgroundColor = "var(--lp-color-background-default)";
          element.append(expected);
          const expectedColor = getComputedStyle(expected).backgroundColor;
          expected.remove();
          const rect = element.getBoundingClientRect();
          return {
            background: style.backgroundColor,
            expectedColor,
            borderStyle: style.borderTopStyle,
            borderWidth: style.borderTopWidth,
            shadow: style.boxShadow,
            top: rect.top,
            right: rect.right,
            bottom: rect.bottom,
            left: rect.left,
            viewportWidth: innerWidth,
            viewportHeight: innerHeight,
            alignments: [...element.querySelectorAll("[role=menuitem]")].map(
              (item) => getComputedStyle(item).justifyContent,
            ),
          };
        },
      );
      assert.equal(surface.background, surface.expectedColor);
      assert.notEqual(surface.background, "rgba(0, 0, 0, 0)");
      assert.equal(surface.borderStyle, "solid");
      assert.equal(surface.borderWidth, "1px");
      assert.notEqual(surface.shadow, "none");
      assert.deepEqual(surface.alignments, Array(4).fill("flex-start"));
      assert.ok(surface.left >= 0 && surface.right <= surface.viewportWidth);
      assert.ok(surface.top >= 0 && surface.bottom <= surface.viewportHeight);
      assert.equal(await menu.getByRole("menuitem").count(), 4);
      await page.screenshot({
        path: resolve(artifacts, `menu-${width}-${theme}.png`),
        animations: "disabled",
        timeout: 5000,
      });
      await page.keyboard.press("End");
      assert.equal(
        await menu
          .getByRole("menuitem", {
            name: "Delete Rerun Requests…",
            exact: true,
          })
          .evaluate((element) => document.activeElement === element),
        true,
      );
      await page.keyboard.press("Escape");
      await menu.waitFor({ state: "hidden" });
      assert.equal(
        await trigger.evaluate((element) => document.activeElement === element),
        true,
      );
      assert.equal(await summary.textContent(), selected);
      assert.equal(page.url(), url.href);
      checks.push({ width, theme, surface });
    }
  }
  assert.deepEqual(errors, []);
  assert.deepEqual(mutations, []);
  await writeFile(
    resolve(artifacts, "report.json"),
    JSON.stringify(
      { passed: true, authenticated, checks, mutations, errors },
      null,
      2,
    ),
  );
  process.stdout.write(
    `Bulk menu surface: PASS (${checks.length} viewport/theme checks).\n`,
  );
} finally {
  await browser.close();
}
