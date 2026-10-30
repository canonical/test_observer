// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

// Chromium coverage for the issue detail slice. All API traffic is intercepted;
// no live backend, test data, or mutation is used.
/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-argument, @typescript-eslint/no-unsafe-return */
import assert from "node:assert/strict";
import { createServer } from "vite";
import { setTimeout as delay } from "node:timers/promises";

const apiOrigin = "http://localhost:30000";
const detailPath = "/v1/issues/73";
const apiRequests = [];
const detail = {
  id: 73,
  source: "github",
  project: "canonical/test-observer",
  key: "73",
  title: "Issue detail deep link regression",
  status: "open",
  url: "https://github.com/canonical/test-observer/issues/73",
  labels: ["frontend"],
  auto_rerun_enabled: false,
  attachment_rules: [
    {
      id: 14,
      enabled: true,
      families: ["snap", "deb"],
      artefacts: ["example-app"],
      artefact_versions: ["1.2"],
      artefact_stages: ["", "edge"],
      artefact_tracks: ["latest/stable"],
      environment_names: ["ubuntu-24.04"],
      test_plans: ["smoke"],
      test_case_names: ["install / test"],
      template_ids: ["template-1"],
      test_result_statuses: ["FAILED", "SKIPPED"],
      execution_metadata: { "ci:provider": ["GitHub Actions", "Buildkite"] },
    },
  ],
};
const initialRule = structuredClone(detail.attachment_rules[0]);
const otherIssue = structuredClone(detail);
otherIssue.id = 80;
otherIssue.key = "80";
otherIssue.title = "A different issue with the same rule ID";
let holdNextPatch = false;
let deleteFailure = "";
let holdDelete = false;
let deleteStarted = () => undefined;
let releaseDelete = () => undefined;
let deleteGate = Promise.resolve();
let signalHeldPatchStart = () => undefined;
const heldPatchStarted = new Promise((resolve) => {
  signalHeldPatchStart = resolve;
});
let releaseHeldPatch = () => undefined;
const heldPatchGate = new Promise((resolve) => {
  releaseHeldPatch = resolve;
});
let signalHeldPatchFinished = () => undefined;
const heldPatchFinished = new Promise((resolve) => {
  signalHeldPatchFinished = resolve;
});
const server = await createServer({
  server: { host: "127.0.0.1", port: 0 },
});
let browser;

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
    console.error("Mocked issue-detail page error:", error.message);
  });
  await page.route(`${apiOrigin}/**`, async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    apiRequests.push({
      method: request.method(),
      path: url.pathname,
      url,
      body: request.postData(),
    });
    const origin = request.headers().origin ?? viteOrigin;
    const cors = {
      "access-control-allow-origin": origin,
      "access-control-allow-credentials": "true",
      "access-control-allow-headers": "content-type,x-csrf-token",
      "access-control-allow-methods": "GET,PATCH,DELETE,OPTIONS",
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
    if (url.pathname === "/v1/test-results/search-page") {
      await route.fulfill({
        status: 200,
        headers: cors,
        contentType: "application/json",
        body: JSON.stringify({ count: 0, limit: 50, offset: 0, rows: [] }),
      });
      return;
    }
    if (url.pathname === detailPath && request.method() === "GET") {
      await route.fulfill({
        status: 200,
        headers: cors,
        contentType: "application/json",
        body: JSON.stringify(detail),
      });
      return;
    }
    if (url.pathname === "/v1/issues/80" && request.method() === "GET") {
      await route.fulfill({
        status: 200,
        headers: cors,
        contentType: "application/json",
        body: JSON.stringify(otherIssue),
      });
      return;
    }
    if (url.pathname === "/v1/issues/74" && request.method() === "GET") {
      const invalid = structuredClone(detail);
      invalid.id = 74;
      invalid.attachment_rules = [
        { ...initialRule, test_result_statuses: ["UNKNOWN"] },
      ];
      await route.fulfill({
        status: 200,
        headers: cors,
        contentType: "application/json",
        body: JSON.stringify(invalid),
      });
      return;
    }
    if (url.pathname === "/v1/issues/75" && request.method() === "GET") {
      const invalid = structuredClone(detail);
      invalid.id = 75;
      invalid.attachment_rules = [{ ...initialRule, families: ["mystery"] }];
      await route.fulfill({
        status: 200,
        headers: cors,
        contentType: "application/json",
        body: JSON.stringify(invalid),
      });
      return;
    }
    if (url.pathname === "/v1/issues/999" && request.method() === "GET") {
      await route.fulfill({
        status: 404,
        headers: cors,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Issue not found" }),
      });
      return;
    }
    if (url.pathname === "/v1/issues/500" && request.method() === "GET") {
      await route.fulfill({
        status: 503,
        headers: cors,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Service unavailable" }),
      });
      return;
    }
    if (
      url.pathname === "/v1/issues/73/attachment-rules/14" &&
      request.method() === "PATCH"
    ) {
      const body = JSON.parse(request.postData() ?? "{}");
      assert.equal(typeof body.enabled, "boolean");
      if (holdNextPatch) {
        holdNextPatch = false;
        signalHeldPatchStart();
        await heldPatchGate;
        await route.fulfill({
          status: 200,
          headers: cors,
          contentType: "application/json",
          body: JSON.stringify({ ...initialRule, enabled: body.enabled }),
        });
        signalHeldPatchFinished();
        return;
      }
      detail.attachment_rules[0].enabled = body.enabled;
      await route.fulfill({
        status: 200,
        headers: cors,
        contentType: "application/json",
        body: JSON.stringify(detail.attachment_rules[0]),
      });
      return;
    }
    if (
      url.pathname === "/v1/issues/73/attachment-rules/14" &&
      request.method() === "DELETE"
    ) {
      if (holdDelete) {
        deleteStarted();
        await deleteGate;
      }
      if (deleteFailure) {
        await route.fulfill({
          status: 403,
          headers: cors,
          json: { detail: deleteFailure },
        });
        return;
      }
      detail.attachment_rules = detail.attachment_rules.filter(
        (rule) => rule.id !== 14,
      );
      await route.fulfill({ status: 204, headers: cors });
      return;
    }
    await route.fulfill({
      status: 404,
      headers: cors,
      contentType: "application/json",
      body: JSON.stringify({ detail: `Unmocked endpoint: ${url.pathname}` }),
    });
  });

  const detailRequestStart = apiRequests.length;
  await page.goto(`${base}/issues/73`);
  await page
    .getByRole("heading", { name: detail.title, exact: true })
    .waitFor();
  assert.equal(new URL(page.url()).pathname, "/wip/issues/73");
  assert.ok(
    apiRequests
      .slice(detailRequestStart)
      .some(
        (request) => request.path === detailPath && request.method === "GET",
      ),
  );
  await page
    .getByRole("link", { name: "Open external issue 73 in a new tab" })
    .waitFor();
  await page.getByText("canonical/test-observer", { exact: true }).waitFor();
  await page.getByText("github", { exact: true }).waitFor();
  await page.getByText("open", { exact: true }).waitFor();
  assert.equal(
    await page
      .getByRole("heading", { name: "Test Results", exact: true })
      .count(),
    1,
    "issue details include their own read-only result section",
  );
  assert.equal(
    await page
      .getByRole("switch", { name: "Auto-rerun on new matches" })
      .count(),
    1,
  );
  assert.equal(
    apiRequests.some(
      (request) =>
        request.path === "/v1/test-results/search-page" &&
        request.url.searchParams.get("issues") === "73",
    ),
    true,
    "opening issue details fetches only their pinned results",
  );

  const summary = page.getByText("Attachment Rule #14", { exact: true });
  await summary.waitFor();
  const details = page.locator("details.rule");
  assert.equal(
    await details.locator("[open]").count(),
    0,
    "rule starts collapsed",
  );
  await summary.click();
  await page.getByText("ubuntu-24.04", { exact: true }).waitFor();
  await page.getByText(/GitHub Actions/).waitFor();
  await page.getByText(/Buildkite/).waitFor();
  await page.getByText("(none)", { exact: true }).waitFor();

  const viewFilters = page.getByRole("link", { name: "View filters" });
  const viewUrl = new URL(await viewFilters.getAttribute("href"), viteOrigin);
  assert.equal(viewUrl.pathname, "/wip/test-results");
  assert.equal(viewUrl.searchParams.get("issues"), "73");
  assert.deepEqual(viewUrl.searchParams.getAll("families"), ["snap", "deb"]);
  assert.deepEqual(viewUrl.searchParams.getAll("artefacts"), ["example-app"]);
  assert.deepEqual(viewUrl.searchParams.getAll("artefact_versions"), ["1.2"]);
  assert.deepEqual(viewUrl.searchParams.getAll("artefact_stages"), [
    "",
    "edge",
  ]);
  assert.deepEqual(viewUrl.searchParams.getAll("artefact_tracks"), [
    "latest/stable",
  ]);
  assert.deepEqual(viewUrl.searchParams.getAll("environments"), [
    "ubuntu-24.04",
  ]);
  assert.deepEqual(viewUrl.searchParams.getAll("test_plans"), ["smoke"]);
  assert.deepEqual(viewUrl.searchParams.getAll("test_cases"), [
    "install / test",
  ]);
  assert.deepEqual(viewUrl.searchParams.getAll("template_ids"), ["template-1"]);
  assert.deepEqual(viewUrl.searchParams.getAll("test_result_statuses"), [
    "FAILED",
    "SKIPPED",
  ]);
  assert.deepEqual(viewUrl.searchParams.getAll("execution_metadata"), [
    `${Buffer.from("ci:provider").toString("base64")}:${Buffer.from("GitHub Actions").toString("base64")}`,
    `${Buffer.from("ci:provider").toString("base64")}:${Buffer.from("Buildkite").toString("base64")}`,
  ]);
  await viewFilters.click();
  await page.waitForURL((url) => url.pathname === "/wip/test-results");
  assert.equal(new URL(page.url()).searchParams.get("issues"), "73");
  await page.goto(`${base}/issues/73`);
  await page
    .getByRole("heading", { name: detail.title, exact: true })
    .waitFor();
  await page.getByText("Attachment Rule #14", { exact: true }).click();

  holdNextPatch = true;
  await page.getByRole("button", { name: "Disable", exact: true }).click();
  await heldPatchStarted;
  await page.goto(`${base}/issues/80`);
  await page
    .getByRole("heading", { name: otherIssue.title, exact: true })
    .waitFor();
  await page.getByText("Attachment Rule #14", { exact: true }).click();
  const otherIssueDisable = page.getByRole("button", {
    name: "Disable",
    exact: true,
  });
  assert.equal(await otherIssueDisable.isDisabled(), false);
  releaseHeldPatch();
  await heldPatchFinished;
  await delay(100);
  assert.equal(
    await page.getByRole("button", { name: "Disable", exact: true }).count(),
    1,
    "a late PATCH for another issue must not replace a same-ID rule",
  );
  await page.goto(`${base}/issues/73`);
  await page
    .getByRole("heading", { name: detail.title, exact: true })
    .waitFor();
  await page.getByText("Attachment Rule #14", { exact: true }).click();

  await page.getByRole("button", { name: "Disable", exact: true }).click();
  await page.getByRole("button", { name: "Enable", exact: true }).waitFor();
  assert.equal(
    await page.locator(".rule-state .value").textContent(),
    "Disabled",
    "read-only Pragma state updates after confirmation",
  );
  await page.getByRole("button", { name: "Enable", exact: true }).click();
  await page.getByRole("button", { name: "Disable", exact: true }).waitFor();
  assert.equal(
    await page.locator(".rule-state .value").textContent(),
    "Enabled",
  );
  const patchRequests = apiRequests.filter(
    (request) => request.method === "PATCH",
  );
  assert.equal(patchRequests.length, 3);
  assert.ok(
    patchRequests.every(
      (request) => request.path === "/v1/issues/73/attachment-rules/14",
    ),
  );
  assert.deepEqual(
    patchRequests.map((request) => JSON.parse(request.body)),
    [{ enabled: false }, { enabled: false }, { enabled: true }],
  );

  const deleteTrigger = page.getByRole("button", {
    name: "Delete",
    exact: true,
  });
  await deleteTrigger.focus();
  await page.keyboard.press("Enter");
  const confirm = page.getByRole("dialog", { name: "Delete attachment rule?" });
  await confirm.waitFor();
  assert.equal(
    await confirm.evaluate(
      (e) => e.matches(":modal") && e.classList.contains("ds"),
    ),
    true,
  );
  assert.equal(
    apiRequests.filter((request) => request.method === "DELETE").length,
    0,
    "opening confirmation does not delete",
  );
  await confirm.getByRole("button", { name: "Cancel" }).click();
  await confirm.waitFor({ state: "hidden" });
  assert.equal(
    await deleteTrigger.evaluate((e) => document.activeElement === e),
    true,
  );
  await deleteTrigger.click();
  await confirm.waitFor();
  await page.keyboard.press("Escape");
  await confirm.waitFor({ state: "hidden" });
  assert.equal(
    await deleteTrigger.evaluate((e) => document.activeElement === e),
    true,
  );

  // Integrated rule actions use the installed Modal in both themes and constrained
  // viewports. Long permission errors are literal; only the body scrolls and the
  // real header/footer stay reachable. All DELETE traffic is intercepted above.
  deleteFailure =
    "<script>not executable</script>\n" +
    "Long literal permission failure 🧪 ".repeat(350);
  const modalGeometry = [];
  for (const [theme, width, height] of [
    ["light", 1440, 900],
    ["dark", 1440, 900],
    ["light", 800, 420],
    ["dark", 390, 600],
  ]) {
    await page.setViewportSize({ width, height });
    await page.emulateMedia({ colorScheme: theme });
    await deleteTrigger.click();
    await confirm.waitFor();
    await confirm
      .getByRole("button", { name: "Delete rule", exact: true })
      .click();
    await confirm.getByRole("alert").waitFor();
    assert.equal(await confirm.getByRole("alert").textContent(), deleteFailure);
    assert.equal(await confirm.locator("script").count(), 0);
    const body = confirm.getByRole("region", {
      name: "Delete attachment rule content",
    });
    await body.focus();
    await page.keyboard.press("End");
    await page.waitForFunction(() => {
      const e = document.querySelector(".delete-rule-body");
      return e.scrollTop + e.clientHeight >= e.scrollHeight - 2;
    });
    const geometry = await confirm.evaluate((e) => {
      const rect = e.getBoundingClientRect();
      const header = e
        .querySelector(".dialog-content-header")
        .getBoundingClientRect();
      const footer = e
        .querySelector(".dialog-content-footer")
        .getBoundingClientRect();
      const body = e.querySelector(".delete-rule-body");
      return {
        inside:
          rect.left >= 0 &&
          rect.right <= innerWidth + 1 &&
          rect.top >= 0 &&
          rect.bottom <= innerHeight + 1,
        header: header.top >= rect.top && header.bottom <= rect.bottom,
        footer: footer.top >= rect.top && footer.bottom <= rect.bottom,
        scrolls: body.scrollHeight > body.clientHeight,
      };
    });
    assert.deepEqual(geometry, {
      inside: true,
      header: true,
      footer: true,
      scrolls: true,
    });
    modalGeometry.push({ theme, width, height, ...geometry });
    for (let i = 0; i < 8; i++) {
      await page.keyboard.press("Tab");
      assert.equal(
        await confirm.evaluate(
          (e) =>
            Boolean(e.contains(document.activeElement)) ||
            document.activeElement === document.body,
        ),
        true,
        "native keyboard focus cannot reach background controls",
      );
    }
    await confirm.getByRole("button", { name: "Cancel", exact: true }).click();
    await confirm.waitFor({ state: "hidden" });
    assert.equal(
      await deleteTrigger.evaluate((e) => document.activeElement === e),
      true,
    );
  }
  await page.setViewportSize({ width: 1440, height: 900 });
  deleteFailure = "";
  holdDelete = true;
  const deletionStarted = new Promise((resolve) => (deleteStarted = resolve));
  deleteGate = new Promise((resolve) => (releaseDelete = resolve));
  await deleteTrigger.click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Delete rule" })
    .click();
  await deletionStarted;
  const beforeDuplicate = apiRequests.filter(
    (r) => r.method === "DELETE",
  ).length;
  assert.equal(
    await confirm
      .getByRole("button", { name: "Deleting…", exact: true })
      .isDisabled(),
    true,
  );
  assert.equal(
    await confirm
      .getByRole("button", { name: "Cancel", exact: true })
      .isDisabled(),
    true,
  );
  assert.equal(
    await confirm
      .getByRole("button", { name: "Close delete confirmation" })
      .isDisabled(),
    true,
  );
  await confirm
    .getByRole("button", { name: "Deleting…", exact: true })
    .evaluate((e) =>
      e.dispatchEvent(new MouseEvent("click", { bubbles: true })),
    );
  await page.keyboard.press("Escape");
  assert.equal(
    await confirm.isVisible(),
    true,
    "pending write cannot be dismissed with Escape",
  );
  assert.equal(
    apiRequests.filter((r) => r.method === "DELETE").length,
    beforeDuplicate,
    "synchronous duplicate dispatch is fenced",
  );
  releaseDelete();
  await page.getByText("No attachment rules.", { exact: true }).waitFor();
  await page.waitForFunction(
    () => document.activeElement?.id === "attachment-rules-title",
  );
  assert.equal(
    apiRequests.filter((request) => request.method === "DELETE").length,
    5,
  );

  const detailRequestCount = apiRequests.filter(
    (request) =>
      request.path.startsWith("/v1/issues/") && request.method === "GET",
  ).length;
  await page.goto(`${base}/issues/not-an-id`);
  await page.getByRole("heading", { name: "Invalid issue ID" }).waitFor();
  assert.equal(
    apiRequests.filter(
      (request) =>
        request.path.startsWith("/v1/issues/") && request.method === "GET",
    ).length,
    detailRequestCount,
    "malformed IDs do not reach the API",
  );
  await page.goto(`${base}/issues/74`);
  await page.getByRole("heading", { name: "Unable to load issue" }).waitFor();
  await page
    .getByText("The issues API returned an invalid issue detail response.", {
      exact: true,
    })
    .waitFor();
  await page.goto(`${base}/issues/75`);
  await page.getByRole("heading", { name: "Unable to load issue" }).waitFor();
  await page
    .getByText("The issues API returned an invalid issue detail response.", {
      exact: true,
    })
    .waitFor();
  await page.goto(`${base}/issues/999`);
  await page.getByRole("heading", { name: "Issue not found" }).waitFor();
  await page.goto(`${base}/issues/500`);
  await page.getByRole("heading", { name: "Unable to load issue" }).waitFor();
  await page.getByText("Service unavailable", { exact: true }).waitFor();

  await page.goto(`${base}/issues/73`);
  await page
    .getByRole("heading", { name: detail.title, exact: true })
    .waitFor();
  await page.evaluate((base) => {
    // eslint-disable-next-line @typescript-eslint/unbound-method -- Rebound to the actual response with call below.
    const readJson = Response.prototype.json;
    Response.prototype.json = function () {
      if (this.status !== 503) return readJson.call(this);
      return new Promise((resolve, reject) => {
        window.__releaseIssueDetailError = () =>
          readJson.call(this).then(resolve, reject);
      });
    };
    for (const id of [500, 73]) {
      const link = document.createElement("a");
      link.id = `qa-issue-navigation-${id}`;
      link.href = `${base}/issues/${id}`;
      link.textContent = `QA issue ${id}`;
      document.body.append(link);
    }
  }, base);
  await page.locator("#qa-issue-navigation-500").click();
  await page.waitForFunction(() => !!window.__releaseIssueDetailError);
  await page.locator("#qa-issue-navigation-73").click();
  await page
    .getByRole("heading", { name: detail.title, exact: true })
    .waitFor();
  await page.evaluate(() => window.__releaseIssueDetailError());
  await page.evaluate(() => new Promise(requestAnimationFrame));
  assert.equal(
    await page.getByRole("heading", { name: "Unable to load issue" }).count(),
    0,
    "an old error body cannot overwrite the newly loaded issue",
  );
  assert.deepEqual(pageErrors, []);
  process.stdout.write(
    `Mocked delete-modal geometry: ${JSON.stringify(modalGeometry)}\n`,
  );
  process.stdout.write(
    "Issue detail Chromium smoke: PASS (deep link, invalid/not-found/error states, expansion, base-aware filters, enable/disable and confirmed deletion; API mocked only).\n",
  );
} finally {
  if (browser) await browser.close();
  await server.close();
}
