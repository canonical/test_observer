// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

// Deterministic Chromium smoke test of the real SvelteKit issues route. The
// browser uses a local Vite server and fulfills only API requests with fixtures.
/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-argument, @typescript-eslint/no-unsafe-return */
import assert from "node:assert/strict";
import { createServer } from "vite";

const apiOrigin = "http://localhost:30000";
const issues = Array.from({ length: 52 }, (_, index) => ({
  id: index + 1,
  source: index >= 50 ? "jira" : "github",
  project: index >= 50 ? "OPS" : "canonical/test-observer",
  key: index >= 50 ? `OPS-${index - 49}` : String(index + 1),
  title:
    index === 0
      ? "Needle regression issue"
      : index === 51
        ? "Closed cleanup issue"
        : `Test issue ${index + 1}`,
  status: index === 50 ? "unknown" : index === 51 ? "closed" : "open",
  url:
    index >= 50
      ? `https://warthogs.atlassian.net/browse/OPS-${index - 49}`
      : `https://github.com/canonical/test-observer/issues/${index + 1}`,
  test_executions_count: index === 0 ? 1 : index,
  family: index % 2 === 0 ? "snap" : "deb",
}));
const apiRequests = [];
let createdRequest = null;
const server = await createServer({
  server: { host: "127.0.0.1", port: 0 },
});
let browser;

function filteredIssues(url) {
  const params = url.searchParams;
  const status = params.getAll("status");
  const families = params.getAll("families");
  const source = params.get("source");
  const project = params.get("project");
  const query = (params.get("q") ?? "").toLowerCase();
  return issues.filter((issue) => {
    if (source && issue.source !== source) return false;
    if (project && issue.project !== project) return false;
    if (status.length && !status.includes(issue.status)) return false;
    if (families.length && !families.includes(issue.family)) return false;
    if (
      query &&
      !`${issue.source} ${issue.project} ${issue.key} ${issue.title} ${issue.status}`
        .toLowerCase()
        .includes(query)
    )
      return false;
    return true;
  });
}

try {
  await server.listen();
  const address = server.httpServer.address();
  assert.ok(address && typeof address !== "string");
  const viteOrigin = `http://127.0.0.1:${address.port}`;
  const base = `${viteOrigin}/wip`;
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
  page.setDefaultTimeout(30000);
  const pageErrors = [];
  page.on("pageerror", (error) => {
    pageErrors.push(error.message);
    console.error("Mocked Issues page error:", error.message);
  });

  await page.route(`${apiOrigin}/**`, async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    apiRequests.push({ method: request.method(), url: url.href });
    const origin = request.headers().origin ?? viteOrigin;
    const cors = {
      "access-control-allow-origin": origin,
      "access-control-allow-credentials": "true",
      "access-control-allow-headers": "content-type,x-csrf-token",
      "access-control-allow-methods": "GET,PUT,OPTIONS",
      vary: "Origin",
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
    if (url.pathname === "/v1/issues" && request.method() === "GET") {
      const params = url.searchParams;
      if (params.get("q") === "delayed-error") {
        await route.fulfill({
          status: 503,
          headers: cors,
          contentType: "application/json",
          body: JSON.stringify({ detail: "Obsolete issue-list error" }),
        });
        return;
      }
      const matches = filteredIssues(url);
      const limit = Number(params.get("limit") ?? 50);
      const offset = Number(params.get("offset") ?? 0);
      await route.fulfill({
        status: 200,
        headers: cors,
        contentType: "application/json",
        body: JSON.stringify({
          issues: matches
            .slice(offset, offset + limit)
            .map(({ family: _family, ...issue }) => issue),
          count: matches.length,
          limit,
          offset,
        }),
      });
      return;
    }
    if (url.pathname === "/v1/issues" && request.method() === "PUT") {
      createdRequest = JSON.parse(request.postData() ?? "{}");
      const issue = {
        id: 100,
        source: "github",
        project: "canonical/test-observer",
        key: "100",
        title: "Created from the issues list",
        status: "open",
        url: createdRequest.url,
        test_executions_count: 0,
      };
      issues.push({ ...issue, family: "snap" });
      await route.fulfill({
        status: 200,
        headers: cors,
        contentType: "application/json",
        body: JSON.stringify(issue),
      });
      return;
    }
    await route.fulfill({
      status: 404,
      headers: cors,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Unmocked endpoint" }),
    });
  });

  await page.goto(`${base}/issues`);
  await page.getByRole("heading", { name: "Issues", exact: true }).waitFor();
  await page.getByRole("link", { name: "Needle regression issue" }).waitFor();
  await page.getByRole("button", { name: /Load more issues/ }).waitFor();
  const initialRequest = apiRequests.find(
    (request) =>
      request.method === "GET" &&
      new URL(request.url).pathname === "/v1/issues",
  );
  assert.ok(initialRequest, "Initial issues list request was made");
  const initialParams = new URL(initialRequest.url).searchParams;
  assert.deepEqual(initialParams.getAll("status"), ["open", "unknown"]);
  assert.equal(initialParams.get("limit"), "50");
  assert.equal(initialParams.get("offset"), "0");
  assert.equal(new URL(page.url()).pathname, "/wip/issues");
  assert.equal(await page.locator(".issue-title").count(), 50);
  assert.equal(
    await page
      .getByRole("link", { name: "Open external issue #1 in a new tab" })
      .getAttribute("target"),
    "_blank",
  );
  assert.equal(
    await page
      .getByRole("link", { name: "Needle regression issue" })
      .getAttribute("href"),
    "/wip/issues/1",
  );

  await page.getByRole("button", { name: /Load more issues/ }).click();
  await page.getByRole("link", { name: "OPS-1" }).waitFor();
  assert.equal(await page.locator(".issue-title").count(), 51);

  await page.getByLabel("JIRA", { exact: true }).check();
  await page.getByRole("link", { name: "OPS-1" }).waitFor();
  assert.equal(await page.locator(".issue-title").count(), 1);
  assert.equal(new URL(page.url()).searchParams.get("source"), "jira");
  const sourceRequest = apiRequests.at(-1);
  assert.equal(new URL(sourceRequest.url).searchParams.get("source"), "jira");

  await page.goto(`${base}/issues?status=closed`);
  await page.getByRole("link", { name: "Closed cleanup issue" }).waitFor();
  assert.equal(new URL(page.url()).searchParams.get("status"), "closed");
  assert.equal(await page.locator(".issue-title").count(), 1);

  await page.goto(`${base}/issues?q=Needle`);
  await page.getByRole("link", { name: "Needle regression issue" }).waitFor();
  assert.equal(new URL(page.url()).searchParams.get("q"), "Needle");
  assert.equal(await page.locator(".issue-title").count(), 1);

  // Hold error-body parsing across a newer SPA query, not just the request
  // headers. A generation check before awaiting that body is insufficient.
  await page.evaluate(() => {
    // eslint-disable-next-line @typescript-eslint/unbound-method -- Rebound to the actual response with call below.
    const readJson = Response.prototype.json;
    Response.prototype.json = function () {
      if (this.status !== 503) return readJson.call(this);
      return new Promise((resolve, reject) => {
        window.__releaseIssueListError = () =>
          readJson.call(this).then(resolve, reject);
      });
    };
  });
  await page.getByLabel("Search issues", { exact: true }).fill("delayed-error");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await page.waitForFunction(() => !!window.__releaseIssueListError);
  await page.getByLabel("Search issues", { exact: true }).fill("Needle");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await page.getByRole("link", { name: "Needle regression issue" }).waitFor();
  await page.evaluate(() => window.__releaseIssueListError());
  await page.evaluate(() => new Promise(requestAnimationFrame));
  assert.equal(await page.getByRole("alert").count(), 0);
  assert.equal(await page.locator(".issue-title").count(), 1);

  await page.goto(`${base}/issues`);
  await page.getByRole("button", { name: "Add issue", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Add issue" });
  await dialog.waitFor();
  await page
    .getByLabel("External issue URL")
    .fill("https://example.test/issues/42");
  await page
    .getByRole("button", { name: "Add issue", exact: true })
    .last()
    .click();
  await page
    .getByText(
      "Enter a supported GitHub issue, Jira issue, or Launchpad bug URL.",
    )
    .waitFor();
  assert.equal(createdRequest, null, "Unsupported URLs never reach the API");

  const supportedUrl = "https://github.com/canonical/test-observer/issues/100";
  await page.getByLabel("External issue URL").fill(supportedUrl);
  await page
    .getByRole("button", { name: "Add issue", exact: true })
    .last()
    .click();
  await dialog.waitFor({ state: "hidden" });
  assert.deepEqual(createdRequest, { url: supportedUrl });
  await page.getByRole("button", { name: /Load more issues/ }).click();
  await page
    .getByRole("link", { name: "Created from the issues list" })
    .waitFor();
  assert.deepEqual(pageErrors, []);
  process.stdout.write(
    "Issues page Chromium smoke: PASS (base path, API defaults, paging, query filters, links, URL validation, creation).\n",
  );
} finally {
  if (browser) await browser.close();
  await server.close();
}
