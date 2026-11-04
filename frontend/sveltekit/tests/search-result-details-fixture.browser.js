// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

// Opt-in real Chromium + actual component/styles, synthetic read-only data.
// The standalone Vite server is test-only: no SvelteKit routes or live API/SSO.
/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-return */
/* global chrome */
import assert from "node:assert/strict";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { createServer } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import {
  assertDetailsLayout,
  assertLogBodyScrolling,
} from "./details-layout.browser.js";
import { largeResult, emptyResult } from "./fixtures/details/data.js";

const { chromium } = await import(
  process.env.PLAYWRIGHT_MODULE ?? "playwright-core"
);
const artifacts = resolve(
  process.env.QA_ARTIFACT_DIR ?? "/tmp/opencode/details-layout/fixture-browser",
);
await mkdir(artifacts, { recursive: true });
const server = await createServer({
  configFile: false,
  root: fileURLToPath(new URL("./fixtures/details", import.meta.url)),
  cacheDir: resolve(artifacts, "vite-cache"),
  plugins: [svelte({ compilerOptions: { runes: true } })],
  resolve: {
    alias: { $lib: fileURLToPath(new URL("../src/lib", import.meta.url)) },
  },
  server: {
    host: "127.0.0.1",
    port: 0,
    fs: { allow: [fileURLToPath(new URL("..", import.meta.url))] },
  },
});
const profile = await mkdtemp(resolve(artifacts, "chromium-profile-"));
let context;
const checks = [];
const errors = [];
const apiRequests = [];
let passed = false;
try {
  await server.listen();
  const address = server.httpServer.address();
  assert.ok(address && typeof address !== "string");
  const url = `http://127.0.0.1:${address.port}/`;
  context = await chromium.launchPersistentContext(profile, {
    headless: true,
    viewport: null,
    args: ["--no-sandbox", "--window-size=1440,987"],
    ...(process.env.CHROMIUM_EXECUTABLE
      ? { executablePath: process.env.CHROMIUM_EXECUTABLE }
      : {}),
  });
  context.on("request", (request) => {
    // Pragma's real stylesheet loads a font from assets.ubuntu.com/v1/;
    // that static font is not a Test Observer API request.
    if (
      request.resourceType() !== "font" &&
      new URL(String(request.url())).pathname.startsWith("/v1/")
    )
      apiRequests.push(request.url());
  });
  const page = context.pages()[0];
  page.setDefaultTimeout(15000);
  page.on("pageerror", (error) => errors.push(String(error)));
  const cdp = await context.newCDPSession(page);
  const { windowId } = await cdp.send("Browser.getWindowForTarget");
  const dialog = page.locator("dialog.search-result-details");
  for (const zoom of [1, 1.2]) {
    // Actual Chromium browser zoom, set through its own Settings API in an
    // isolated disposable profile. NOT CSS zoom, pinch scale, or a DPR mock.
    await page.goto("chrome://settings/appearance");
    await page.evaluate(
      (zoom) =>
        new Promise((done) =>
          chrome.settingsPrivate.setDefaultZoom(zoom, done),
        ),
      zoom,
    );
    await page.goto(url);
    const chromeHeight = Number(
      await page.evaluate(
        () => outerHeight - Math.round(innerHeight * devicePixelRatio),
      ),
    );
    for (const [width, height] of [
      [1920, 900],
      [1440, 900],
      [960, 900],
      [800, 900],
      [800, 600],
    ]) {
      await cdp.send("Browser.setWindowBounds", {
        windowId,
        bounds: { width, height: height + chromeHeight },
      });
      await page.waitForFunction(
        ({ width, height, zoom }) =>
          Math.abs(innerWidth * zoom - width) < 2 &&
          Math.abs(innerHeight * zoom - height) < 2,
        { width, height, zoom },
      );
      assert.ok(
        Math.abs((await page.evaluate(() => devicePixelRatio)) - zoom) < 0.001,
        "Verify actual 100%/120% browser zoom",
      );
      for (const theme of ["light", "dark"]) {
        /** @param {string} section */
        const capture = async (section) => {
          // Playwright's CSS-sized screenshot clip crops native browser zoom.
          // Capture Chromium's full physical viewport and verify PNG dimensions.
          const screenshot = await cdp.send("Page.captureScreenshot", {
            format: "png",
            captureBeyondViewport: false,
          });
          const image = Buffer.from(String(screenshot.data), "base64");
          assert.equal(image.readUInt32BE(16), width);
          assert.equal(image.readUInt32BE(20), height);
          await writeFile(
            resolve(
              artifacts,
              `fixture-${width}x${height}-${theme}-${Math.round(zoom * 100)}-${section}.png`,
            ),
            image,
          );
        };
        await page.evaluate((theme) => {
          document.documentElement.className = theme;
        }, theme);
        const trigger = page.getByRole("button", {
          name: "Open representative details",
          exact: true,
        });
        await trigger.click();
        await dialog.waitFor({ state: "visible" });
        assert.equal(
          await dialog.evaluate((element) => element.matches(":modal")),
          true,
        );
        const layout = await assertDetailsLayout(
          dialog,
          largeResult.test_execution.execution_metadata,
        );
        assert.equal(layout.bodyOverflow, true);
        const actualFields = await dialog
          .locator("section > .description-list-container dd")
          .allTextContents();
        assert.deepEqual(actualFields.slice(0, 13), [
          largeResult.test_result.name,
          largeResult.test_result.category,
          largeResult.test_result.template_id,
          "FAILED",
          "Configured-routes",
          largeResult.artefact.name,
          largeResult.artefact.version,
          largeResult.artefact.track,
          largeResult.artefact_build.architecture,
          "7",
          largeResult.test_execution.test_plan,
          largeResult.test_execution.environment.name,
          "FAILED",
        ]);
        assert.equal(
          await dialog.locator("pre").textContent(),
          largeResult.test_result.io_log,
        );
        assert.equal(
          await dialog.locator("pre").evaluate(
            /** @param {HTMLPreElement} log */ (log) => {
              const selection = getSelection();
              const range = document.createRange();
              range.selectNodeContents(log);
              selection.removeAllRanges();
              selection.addRange(range);
              const text = selection.toString();
              selection.removeAllRanges();
              return getComputedStyle(log).userSelect === "text" ? text : null;
            },
          ),
          largeResult.test_result.io_log,
          "The full literal log remains selectable/copyable",
        );
        assert.equal(
          await dialog.locator("script, img").count(),
          0,
          "Malicious-looking values stay literal",
        );
        assert.equal(
          await page.evaluate(() => "detailsInjected" in globalThis),
          false,
        );
        assert.deepEqual(
          await dialog
            .locator(".issues a")
            .evaluateAll((links) =>
              links.map((link) => [
                link.getAttribute("href"),
                link.getAttribute("target"),
                link.getAttribute("rel"),
              ]),
            ),
          [
            ["/fixture-base/issues/101", "_blank", "noopener noreferrer"],
            ["/fixture-base/issues/102", "_blank", "noopener noreferrer"],
          ],
        );
        const scrolling = await assertLogBodyScrolling(page, dialog);
        await capture("log-end");
        await dialog
          .locator("h4")
          .evaluate((heading) => heading.scrollIntoView({ block: "start" }));
        await capture("metadata");
        // Native Tab visits the one body region and links/footer, never the log.
        await dialog
          .getByRole("button", { name: "Close details", exact: true })
          .focus();
        await page.keyboard.press("Tab");
        assert.equal(
          await dialog
            .locator(".details-body")
            .evaluate((element) => document.activeElement === element),
          true,
        );
        for (const expected of [
          "View issue EX-101",
          "View issue EX-102",
          `View Run for ${largeResult.test_result.name}`,
        ]) {
          await page.keyboard.press("Tab");
          assert.equal(
            await dialog
              .getByRole("link", { name: expected, exact: true })
              .evaluate((element) => document.activeElement === element),
            true,
          );
        }
        await page.keyboard.press("Tab");
        assert.equal(
          await dialog
            .getByRole("button", { name: "Close", exact: true })
            .evaluate((element) => document.activeElement === element),
          true,
        );
        await dialog.locator(".details-body").evaluate((element) => {
          element.scrollTop = 0;
        });
        await capture("scalars");
        await page.keyboard.press("Escape");
        await dialog.waitFor({ state: "hidden" });
        assert.equal(
          await trigger.evaluate(
            (element) => document.activeElement === element,
          ),
          true,
        );
        await page
          .getByRole("button", { name: "Open empty details", exact: true })
          .click();
        await dialog.waitFor({ state: "visible" });
        const emptyLayout = await assertDetailsLayout(
          dialog,
          emptyResult.test_execution.execution_metadata,
        );
        assert.equal(await dialog.locator("pre, .issues, time").count(), 0);
        assert.equal(
          await dialog.getByText("Run unavailable", { exact: true }).count(),
          1,
        );
        if (height === 900 && zoom === 1)
          assert.equal(
            emptyLayout.bodyOverflow,
            false,
            "Short records keep natural height rather than a forced scrollpane",
          );
        await dialog
          .getByRole("button", { name: "Close", exact: true })
          .click();
        await dialog.waitFor({ state: "hidden" });
        checks.push({
          width,
          height,
          theme,
          zoom,
          layout,
          scrolling,
          emptyLayout,
        });
      }
    }
  }
  assert.deepEqual(
    apiRequests,
    [],
    "The representative browser fixture never contacts an API",
  );
  assert.deepEqual(errors, []);
  passed = true;
} finally {
  await context?.close();
  await server.close();
  await rm(profile, { recursive: true, force: true });
  await writeFile(
    resolve(artifacts, "fixture-report.json"),
    JSON.stringify(
      {
        passed,
        evidence:
          "Actual modal/component styles in Chromium, synthetic read-only data; NOT live API or exact production data",
        zoom: "Native Chromium default zoom through Settings API; isolated disposable profile",
        checks,
        errors,
        apiRequests,
      },
      null,
      2,
    ),
  );
  process.stdout.write(
    `Representative Details browser fixture: ${passed ? "PASS" : "FAIL"}; report ${resolve(artifacts, "fixture-report.json")}\n`,
  );
}
