// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

// Opt-in real Chromium/SvelteKit/SvGrid integration with synthetic API responses.
// No live API, credentials, database writes or Playwright project dependency.
/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-argument, @typescript-eslint/no-unsafe-return */
import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { createServer } from "vite";

const artifacts = resolve(
  process.env.QA_ARTIFACT_DIR ?? "/tmp/opencode/issue-results-browser",
);
await mkdir(artifacts, { recursive: true });
const requests = [];
const pageErrors = [];
const total = 625;
const log =
  '<script>alert("literal")</script>\n  indented 🧪\n' + "unbroken".repeat(800);
/** @param {number} index @param {number} [issue] */
function row(index, issue = 73) {
  return {
    test_result: {
      id: issue * 1000 + index,
      name: `issue-${issue}-case-${index}`,
      category: "smoke",
      status: "FAILED",
      created_at: "2026-10-25T12:00:00Z",
      template_id: "template",
      issues: [{ id: issue, key: `QA-${issue}`, title: `Issue ${issue}` }],
    },
    test_execution: {
      id: 7000 + index,
      status: "FAILED",
      environment: { name: "test lab" },
      test_plan: "smoke",
      rerun_is_requested: false,
      execution_is_latest: true,
      execution_metadata: [{ category: "literal <metadata>", value: "λ 🧪" }],
    },
    artefact: {
      id: 42,
      name: "example artefact",
      version: "1.2",
      track: "stable",
      family: index === 624 ? "unconfigured" : "api-family",
      stage: "",
      archived: false,
      reviewers: [],
    },
    artefact_build: { architecture: "amd64" },
  };
}
/** @param {number} id */
function details(id) {
  const issue = Math.floor(id / 1000);
  const source = row(id % 1000, issue);
  return {
    ...source,
    test_result: {
      ...source.test_result,
      io_log: log,
      issues: [
        {
          issue: {
            id: issue,
            source: "github",
            project: "qa",
            key: `QA-${issue}`,
            title: `Issue ${issue}`,
            status: "open",
          },
        },
      ],
    },
    test_execution: {
      ...source.test_execution,
      created_at: "2026-10-25T12:00:00Z",
      execution_metadata: { "literal <metadata>": ["λ 🧪"] },
    },
  };
}
const server = await createServer({
  cacheDir: resolve(artifacts, "vite-cache"),
  server: { host: "127.0.0.1", port: 0 },
});
let browser;
let passed = false;
try {
  await server.listen();
  const address = server.httpServer.address();
  assert.ok(address && typeof address !== "string");
  const origin = `http://127.0.0.1:${address.port}`;
  const base = `${origin}/wip`;
  const { chromium } = await import(
    process.env.PLAYWRIGHT_MODULE ?? "playwright-core"
  );
  browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox"],
    ...(process.env.CHROMIUM_EXECUTABLE
      ? { executablePath: process.env.CHROMIUM_EXECUTABLE }
      : {}),
  });
  const page = await browser.newPage({
    viewport: { width: 1440, height: 900 },
  });
  page.setDefaultTimeout(20000);
  page.on("pageerror", (e) => pageErrors.push(e.message));
  await page.route("**/wip/families.json", (route) =>
    route.fulfill({
      json: {
        families: [
          {
            name: "configured-route",
            api_name: "api-family",
            stages: [],
            columns: [],
            filters: [],
          },
        ],
      },
    }),
  );
  let resultStatus = 200;
  let detailsStatus = 200;
  let meStatus = 200;
  let me = null;
  await page.route("http://localhost:30000/**", (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const headers = {
      "access-control-allow-origin": origin,
      "access-control-allow-credentials": "true",
      "access-control-allow-headers": "content-type,x-csrf-token",
      "access-control-allow-methods": "GET,OPTIONS",
    };
    if (request.method() === "OPTIONS")
      return route.fulfill({ status: 204, headers });
    requests.push({
      path: url.pathname,
      query: url.search,
      method: request.method(),
    });
    const reply = (json, status = 200) =>
      route.fulfill({ status, headers, json });
    if (url.pathname === "/v1/users/me") return reply(me, meStatus);
    if (/^\/v1\/issues\/\d+$/.test(url.pathname)) {
      const id = Number(url.pathname.split("/").at(-1));
      return reply({
        id,
        source: "github",
        project: "qa",
        key: `QA-${id}`,
        title: `Issue ${id}`,
        status: "open",
        url: `https://example.invalid/${id}`,
        labels: [],
        attachment_rules: [],
        auto_rerun_enabled: false,
      });
    }
    if (url.pathname === "/v1/test-results/search-page") {
      const issue = Number(url.searchParams.get("issues"));
      assert.equal(url.searchParams.getAll("issues").length, 1);
      if (resultStatus !== 200)
        return reply({ detail: "Result access failure" }, resultStatus);
      const offset = Number(url.searchParams.get("offset"));
      const limit = Number(url.searchParams.get("limit"));
      return reply({
        count:
          url.searchParams.get("include_count") === "true"
            ? issue === 81
              ? 0
              : total
            : null,
        offset,
        limit,
        rows:
          issue === 81
            ? []
            : Array.from({ length: Math.min(limit, total - offset) }, (_, n) =>
                row(offset + n, issue),
              ),
      });
    }
    if (/search-page\/\d+$/.test(url.pathname))
      return reply(
        details(Number(url.pathname.split("/").at(-1))),
        detailsStatus,
      );
    return reply({ detail: "Unmocked endpoint" }, 404);
  });
  await page.goto(`${base}/issues/73?issues=80&offset=500`);
  await page
    .getByText("625 matching test results on the server.", { exact: false })
    .waitFor();
  const grid = page.locator(".issue-results-grid");
  const labels = /** @type {string[]} */ (
    await grid.locator("thead tr th").allTextContents()
  ).map((label) => label.trim());
  assert.equal(labels[labels.indexOf("Architecture") + 1], "Environment");
  assert.equal(await grid.getByRole("checkbox").count(), 0);
  assert.equal(
    requests.filter((r) => /search-page\/\d+$/.test(r.path)).length,
    0,
  );
  assert.ok(
    requests
      .filter((r) => r.path.endsWith("search-page"))
      .every((r) => new URLSearchParams(r.query).get("issues") === "73"),
  );
  /** @param {number} index */
  async function scrollTo(index) {
    await grid.evaluate(
      /** @param {HTMLElement} element @param {number} index */ (
        element,
        index,
      ) => {
        const candidates = [...element.querySelectorAll("*")].filter(
          (e) =>
            e.scrollHeight > e.clientHeight + 1 &&
            /auto|scroll/.test(getComputedStyle(e).overflowY),
        );
        const scroller = candidates
          .sort(
            (a, b) =>
              b.scrollHeight -
              b.clientHeight -
              (a.scrollHeight - a.clientHeight),
          )
          .at(0);
        if (!scroller) throw new Error("No grid scroller");
        scroller.scrollTop = index * 30;
      },
      index,
    );
    await grid
      .locator(`button[data-test-result-id="${73000 + index}"]`)
      .waitFor();
  }
  await scrollTo(125);
  const trigger = page.getByRole("button", {
    name: "View details for issue-73-case-125",
    exact: true,
  });
  const run = grid.getByRole("link", {
    name: "View Run for issue-73-case-125",
    exact: true,
  });
  assert.equal(
    await run.getAttribute("href"),
    "/wip/configured-route/42?testExecutionId=7125&testResultId=73125",
  );
  await trigger.focus();
  await page.keyboard.press("Enter");
  const dialog = page.getByRole("dialog", {
    name: "Test result details",
    exact: true,
  });
  await dialog.locator("pre").waitFor();
  assert.equal(await dialog.locator("pre").textContent(), log);
  assert.equal(await dialog.locator("script").count(), 0);
  assert.equal(
    await dialog
      .getByRole("link", { name: "View issue QA-73" })
      .getAttribute("href"),
    "/wip/issues/73",
  );
  await page.keyboard.press("Escape");
  await dialog.waitFor({ state: "hidden" });
  assert.equal(
    await trigger.evaluate((e) => document.activeElement === e),
    true,
  );
  // Keep the modal snapshot alive while virtualized cells and cached blocks go.
  await trigger.click();
  await dialog.locator("pre").waitFor();
  for (const index of [175, 225, 275, 325, 375, 425, 475, 525, 575, 624])
    await scrollTo(index);
  assert.equal(await dialog.locator("pre").textContent(), log);
  await page.keyboard.press("Escape");
  await dialog.waitFor({ state: "hidden" });
  assert.equal(await grid.evaluate((e) => document.activeElement === e), true);
  assert.match(await grid.textContent(), /Run unavailable/);
  await page
    .getByRole("button", {
      name: "View details for issue-73-case-624",
      exact: true,
    })
    .click();
  await dialog.getByText("unconfigured", { exact: true }).waitFor();
  assert.equal(await dialog.getByRole("link", { name: "View Run" }).count(), 0);
  await page.keyboard.press("Escape");
  await dialog.waitFor({ state: "hidden" });
  assert.ok(
    requests.some((r) => new URLSearchParams(r.query).get("offset") === "600"),
  );
  await page
    .getByText("625 matching test results on the server.", { exact: false })
    .waitFor();

  // Delay already-parsed bodies, ignoring AbortSignal, to exercise generation
  // guards rather than relying solely on Chromium's transport cancellation.
  await page.evaluate((base) => {
    // eslint-disable-next-line @typescript-eslint/unbound-method
    const readJson = Response.prototype.json;
    window.__issueQaHold = "";
    window.__issueQaReleases = [];
    Response.prototype.json = async function () {
      const body = await readJson.call(this);
      if (window.__issueQaHold && this.url.includes(window.__issueQaHold))
        await new Promise((resolve) => window.__issueQaReleases.push(resolve));
      return body;
    };
    for (const id of [73, 80, 81]) {
      const link = document.createElement("a");
      link.href = `${base}/issues/${id}`;
      link.id = `qa-issue-${id}`;
      link.textContent = `QA navigate ${id}`;
      document.body.append(link);
    }
  }, base);
  await page.locator("#qa-issue-80").click();
  await page
    .getByRole("button", {
      name: "View details for issue-80-case-0",
      exact: true,
    })
    .waitFor();
  await page.evaluate(() => (window.__issueQaHold = "issues=73"));
  await page.locator("#qa-issue-73").click();
  await page.waitForFunction(() => window.__issueQaReleases.length === 1);
  await page.locator("#qa-issue-80").click();
  await page
    .getByRole("button", {
      name: "View details for issue-80-case-0",
      exact: true,
    })
    .waitFor();
  await page.evaluate(() => {
    window.__issueQaHold = "";
    window.__issueQaReleases.splice(0).forEach((release) => release());
  });
  assert.equal(
    await page
      .getByRole("button", { name: /View details for issue-73/ })
      .count(),
    0,
  );
  await page.evaluate(() => (window.__issueQaHold = "search-page/80000"));
  await page
    .getByRole("button", {
      name: "View details for issue-80-case-0",
      exact: true,
    })
    .click();
  await page.waitForFunction(() => window.__issueQaReleases.length === 1);
  await page.locator("#qa-issue-81").evaluate((e) => e.click());
  await page
    .getByText("No test results are attached to this issue.", { exact: true })
    .waitFor();
  await page.evaluate(() => {
    window.__issueQaHold = "";
    window.__issueQaReleases.splice(0).forEach((release) => release());
  });
  assert.equal(await page.locator("dialog[open]").count(), 0);
  await page.goBack();
  await page
    .getByRole("button", {
      name: "View details for issue-80-case-0",
      exact: true,
    })
    .waitFor();
  await page.goForward();
  await page
    .getByText("No test results are attached to this issue.", { exact: true })
    .waitFor();

  for (const status of [503, 401, 403]) {
    resultStatus = status;
    me = status === 403 ? { id: 1, teams: [], is_admin: false } : null;
    await page.goto(`${base}/issues/73`);
    await page
      .getByText(
        status === 503
          ? /Could not load test results/
          : status === 401
            ? /need to be logged in/
            : /don't have permission to view these test results/,
      )
      .waitFor();
    resultStatus = 200;
    await page
      .getByRole("button", { name: "Retry results", exact: true })
      .click();
    await page
      .getByRole("button", {
        name: "View details for issue-73-case-0",
        exact: true,
      })
      .waitFor();
  }
  detailsStatus = 403;
  await page
    .getByRole("button", {
      name: "View details for issue-73-case-0",
      exact: true,
    })
    .click();
  await dialog
    .getByText(/don't have permission to view these result details/)
    .waitFor();
  detailsStatus = 200;
  await dialog.getByRole("button", { name: "Retry", exact: true }).click();
  await dialog.locator("pre").waitFor();
  await page.keyboard.press("Escape");
  await dialog.waitFor({ state: "hidden" });
  meStatus = 503;
  resultStatus = 403;
  await page.goto(`${base}/issues/73`);
  await page.getByText(/couldn't verify your session/).waitFor();
  meStatus = 200;
  resultStatus = 200;
  // Narrow dark rendering still exposes the same read-only grid and actions.
  await page.setViewportSize({ width: 800, height: 600 });
  await page.emulateMedia({ colorScheme: "dark" });
  await page
    .getByRole("button", { name: "Retry results", exact: true })
    .click();
  await page
    .getByRole("button", {
      name: "View details for issue-73-case-0",
      exact: true,
    })
    .waitFor();
  await page.screenshot({
    path: resolve(artifacts, "issue-results-narrow-dark.png"),
    fullPage: true,
  });
  assert.ok(requests.every((r) => r.method === "GET"));
  assert.deepEqual(pageErrors, []);
  passed = true;
  process.stdout.write("Issue results Chromium: PASS (mocked API only)\n");
} finally {
  await writeFile(
    resolve(artifacts, "report.json"),
    JSON.stringify(
      { passed, mockedApiOnly: true, total, requests, pageErrors },
      null,
      2,
    ),
  );
  await browser?.close();
  await server.close();
}
