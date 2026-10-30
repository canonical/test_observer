// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

// Real SvelteKit routing/disclosures/focus in Chromium; every API request,
// including mutations in the action regression, is intercepted, never live.
/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-argument, @typescript-eslint/no-unsafe-return */
import assert from "node:assert/strict";
import { before, after, test } from "node:test";
import { createServer } from "vite";

const apiOrigin = "http://localhost:30000";
let server;
let browser;
let base;
const rule = (id) => ({
  id,
  enabled: true,
  families: [],
  artefacts: [],
  artefact_versions: [],
  artefact_stages: [],
  artefact_tracks: [],
  environment_names: [],
  test_plans: [],
  test_case_names: ["target criteria"],
  template_ids: [],
  test_result_statuses: ["FAILED"],
  execution_metadata: {},
});
const issue = (id) => ({
  id,
  source: "github",
  project: "canonical/test-observer",
  key: String(id),
  title: `Issue ${id} rule targeting`,
  status: "open",
  labels: [],
  url: `https://github.com/canonical/test-observer/issues/${id}`,
  auto_rerun_enabled: false,
  // Plenty of collapsed disclosures put the target below the first viewport.
  attachment_rules: Array.from({ length: 20 }, (_, i) => rule(i + 1)),
});

before(async () => {
  server = await createServer({ server: { host: "127.0.0.1", port: 0 } });
  await server.listen();
  base = `http://127.0.0.1:${server.httpServer.address().port}/wip`;
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
});
after(async () => {
  await browser?.close();
  await server?.close();
});

async function fixture() {
  const page = await browser.newPage({
    viewport: { width: 1440, height: 900 },
  });
  const requests = [];
  const errors = [];
  const issues = new Map([
    [73, issue(73)],
    [80, issue(80)],
  ]);
  page.on("pageerror", (error) => errors.push(error.message));
  // Hold actual successful Response.json bodies, rather than only delaying the
  // HTTP headers. This exercises the page's async GET ownership fence.
  await page.addInitScript(() => {
    window.__ruleHoldIssue = 0;
    window.__ruleBodyReleases = [];
    window.__ruleFocus = [];
    document.addEventListener("focusin", (event) => {
      const summary = event.target.closest?.("details.rule > summary");
      if (summary)
        window.__ruleFocus.push({
          path: location.pathname,
          text: summary.textContent,
        });
    });
    // eslint-disable-next-line @typescript-eslint/unbound-method -- Explicitly rebound below.
    const read = Response.prototype.json;
    Response.prototype.json = function () {
      if (
        !window.__ruleHoldIssue ||
        !this.url.endsWith(`/v1/issues/${window.__ruleHoldIssue}`)
      )
        return read.call(this);
      return new Promise((resolve, reject) => {
        window.__ruleBodyReleases.push(() =>
          read.call(this).then(resolve, reject),
        );
      });
    };
  });
  await page.route(`${apiOrigin}/**`, async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const method = request.method();
    const headers = {
      "access-control-allow-origin":
        request.headers().origin ?? new URL(base).origin,
      "access-control-allow-credentials": "true",
      "access-control-allow-headers": "content-type,x-csrf-token",
      "access-control-allow-methods": "GET,PATCH,DELETE,OPTIONS",
    };
    if (method === "OPTIONS") return route.fulfill({ status: 204, headers });
    requests.push({ path: url.pathname, method, body: request.postData() });
    let body;
    let status = 200;
    if (url.pathname === "/v1/users/me") body = null;
    else if (url.pathname === "/v1/test-results/search-page")
      body = { count: 0, limit: 50, offset: 0, rows: [] };
    else {
      const match =
        /^\/v1\/issues\/(73|80)(?:\/attachment-rules\/(\d+))?$/.exec(
          url.pathname,
        );
      const current = match && issues.get(Number(match[1]));
      if (current && !match[2] && method === "GET") body = current;
      else if (current && match[2] && method === "PATCH") {
        const selected = current.attachment_rules.find(
          (r) => r.id === Number(match[2]),
        );
        selected.enabled = JSON.parse(request.postData()).enabled;
        body = selected;
      } else if (current && match[2] && method === "DELETE") {
        current.attachment_rules = current.attachment_rules.filter(
          (r) => r.id !== Number(match[2]),
        );
        return route.fulfill({ status: 204, headers });
      } else {
        status = 404;
        body = { detail: `Unmocked endpoint: ${method} ${url.pathname}` };
      }
    }
    await route.fulfill({
      status,
      headers,
      contentType: "application/json",
      body: JSON.stringify(body),
    });
  });
  return {
    page,
    requests,
    async close(allowWrites = false) {
      try {
        assert.deepEqual(errors, []);
        if (!allowWrites)
          assert.ok(
            requests.every((r) => r.method === "GET"),
            "targeting never mutates",
          );
      } finally {
        await page.close();
      }
    },
  };
}

function disclosure(page, id) {
  return page
    .locator("details.rule")
    .filter({ has: page.getByText(`Attachment Rule #${id}`, { exact: true }) });
}
async function attended(page, id, issueId = 73) {
  await page.waitForFunction(
    ({ id, issueId }) => {
      const summary = document.activeElement;
      return (
        location.pathname.endsWith(`/issues/${issueId}`) &&
        summary?.matches("details.rule[open] > summary") &&
        summary.textContent.includes(`Attachment Rule #${id}`) &&
        !summary.closest("[inert]")
      );
    },
    { id, issueId },
  );
  const summary = disclosure(page, id).locator("summary");
  const bounds = await summary.boundingBox();
  assert.ok(
    bounds && bounds.y >= 0 && Number(bounds.y) + Number(bounds.height) <= 900,
    "target summary is in the viewport",
  );
  assert.equal(
    await disclosure(page, id).evaluate((node) =>
      node.classList.contains("rule-targeted"),
    ),
    true,
  );
}
async function navigate(page, path, shallow = false) {
  await page.evaluate(
    async ({ path, shallow }) => {
      const resource = performance
        .getEntriesByType("resource")
        .find((entry) =>
          entry.name.includes("/runtime/app/navigation/index.js"),
        );
      const { goto } = await import(resource.name);
      await goto(path, { shallow });
    },
    { path, shallow },
  );
}
async function frames(page) {
  await page.evaluate(
    () =>
      new Promise((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(resolve)),
      ),
  );
}

void test("direct and reload targets expand a normally collapsed below-fold rule with native focus, scroll and token highlighting", async () => {
  const f = await fixture();
  try {
    await f.page.goto(`${base}/issues/73`);
    await disclosure(f.page, 19).waitFor();
    assert.equal(
      await disclosure(f.page, 19).evaluate((node) => node.open),
      false,
    );
    await f.page.goto(`${base}/issues/73?attachmentRule=19`);
    await attended(f.page, 19);
    assert.equal(
      await disclosure(f.page, 18).evaluate((node) => node.open),
      false,
    );
    const style = await disclosure(f.page, 19)
      .locator("summary")
      .evaluate((node) => ({
        ring: getComputedStyle(node).outlineColor,
        token: getComputedStyle(node)
          .getPropertyValue("--lp-color-border-focus")
          .trim(),
        margin: getComputedStyle(node).scrollMarginBlockStart,
      }));
    assert.ok(style.token);
    assert.notEqual(style.margin, "0px");
    await f.page.reload();
    await attended(f.page, 19);
    // Native keyboard toggle remains in control after the one targeting event.
    await f.page.keyboard.press("Enter");
    await frames(f.page);
    assert.equal(
      await disclosure(f.page, 19).evaluate((node) => node.open),
      false,
    );
    await f.page.keyboard.press("Space");
    assert.equal(
      await disclosure(f.page, 19).evaluate((node) => node.open),
      true,
    );
  } finally {
    await f.close();
  }
});

void test("normal query navigation and native Back/Forward target only the new rule without refetch or repeated manual override", async () => {
  const f = await fixture();
  try {
    await f.page.goto(`${base}/issues/73?attachmentRule=19`);
    await attended(f.page, 19);
    const count = f.requests.length;
    await navigate(f.page, "/wip/issues/73?attachmentRule=20");
    await attended(f.page, 20);
    await f.page.keyboard.press("Enter");
    await navigate(f.page, "/wip/issues/73?attachmentRule=20&unrelated=1");
    await frames(f.page);
    assert.equal(
      await disclosure(f.page, 20).evaluate((node) => node.open),
      false,
    );
    await f.page.goBack(); // same target, unrelated parameter only
    await frames(f.page);
    assert.equal(
      await disclosure(f.page, 20).evaluate((node) => node.open),
      false,
    );
    await f.page.goBack();
    await attended(f.page, 19);
    await f.page.goForward();
    await attended(f.page, 20);
    assert.equal(
      f.requests.length,
      count,
      "query-only targeting needs no issue/results refetch",
    );
  } finally {
    await f.close();
  }
});

void test("installed shallow URL state and native shallow Back/Forward restore current targeting", async () => {
  const f = await fixture();
  try {
    await f.page.goto(`${base}/issues/73?attachmentRule=19`);
    await attended(f.page, 19);
    const count = f.requests.length;
    await navigate(f.page, "/wip/issues/73?attachmentRule=20", true);
    await attended(f.page, 20);
    await f.page.goBack();
    await attended(f.page, 19);
    await f.page.goForward();
    await attended(f.page, 20);
    assert.equal(f.requests.length, count);
    await f.page.keyboard.press("Enter");
    await navigate(
      f.page,
      "/wip/issues/73?attachmentRule=20&unrelated=2",
      true,
    );
    await frames(f.page);
    assert.equal(
      await disclosure(f.page, 20).evaluate((node) => node.open),
      false,
    );
  } finally {
    await f.close();
  }
});

void test("a shallow pathname change cannot attend a rule in the wrong still-loaded issue", async () => {
  const f = await fixture();
  try {
    await f.page.goto(`${base}/issues/73?attachmentRule=19`);
    await attended(f.page, 19);
    await f.page.keyboard.press("Enter");
    const count = f.requests.length;
    const focusCount = await f.page.evaluate(() => window.__ruleFocus.length);
    await navigate(f.page, "/wip/issues/80?attachmentRule=20", true);
    await frames(f.page);
    assert.equal(await f.page.locator(".rule-targeted").count(), 0);
    assert.equal(
      await disclosure(f.page, 20).evaluate((node) => node.open),
      false,
    );
    assert.equal(
      await f.page.evaluate(() => window.__ruleFocus.length),
      focusCount,
    );
    assert.equal(f.requests.length, count);
    await f.page.goBack();
    await attended(f.page, 19);
  } finally {
    await f.close();
  }
});

void test("delayed parsed bodies honor a changed target, then A/B/A ownership never focuses a stale same-ID rule", async () => {
  const f = await fixture();
  try {
    await f.page.goto(`${base}/issues/73`);
    await disclosure(f.page, 19).waitFor();
    await f.page.evaluate(() => (window.__ruleHoldIssue = 80));
    await navigate(f.page, "/wip/issues/80?attachmentRule=19");
    await f.page.waitForFunction(() => window.__ruleBodyReleases.length === 1);
    assert.equal(await f.page.locator("details.rule").count(), 0);
    await navigate(f.page, "/wip/issues/80?attachmentRule=20");
    await f.page.evaluate(() => {
      window.__ruleHoldIssue = 0;
      window.__ruleBodyReleases.splice(0).forEach((release) => release());
    });
    await attended(f.page, 20, 80);
    const focused = await f.page.evaluate(() => window.__ruleFocus);
    assert.ok(
      !focused.some(
        (entry) => entry.path.endsWith("/80") && entry.text.includes("#19"),
      ),
    );
    await f.page.evaluate(() => (window.__ruleHoldIssue = 73));
    await navigate(f.page, "/wip/issues/73?attachmentRule=19");
    await f.page.waitForFunction(() => window.__ruleBodyReleases.length === 1);
    await navigate(f.page, "/wip/issues/80?attachmentRule=20");
    await attended(f.page, 20, 80);
    const before = await f.page.evaluate(() => window.__ruleFocus.length);
    await f.page.evaluate(() => {
      window.__ruleHoldIssue = 0;
      window.__ruleBodyReleases.splice(0).forEach((release) => release());
    });
    await frames(f.page);
    assert.equal(
      await f.page.evaluate(() => window.__ruleFocus.length),
      before,
    );
    await navigate(f.page, "/wip/issues/73?attachmentRule=19");
    await attended(f.page, 19);
    await navigate(f.page, "/wip/issues/80");
    await disclosure(f.page, 19).waitFor();
    await frames(f.page);
    assert.equal(
      await disclosure(f.page, 19).evaluate((node) => node.open),
      false,
      "another issue without a target never inherits it",
    );
  } finally {
    await f.close();
  }
});

void test("missing, malformed, repeated and nonexistent targets stay functional, clear highlighting and send no writes", async () => {
  const f = await fixture();
  try {
    await f.page.goto(`${base}/issues/73?attachmentRule=19`);
    await attended(f.page, 19);
    for (const query of [
      "",
      "attachmentRule=0",
      "attachmentRule=01",
      "attachmentRule=1.5",
      "attachmentRule=9007199254740992",
      "attachmentRule=19&attachmentRule=20",
      "attachmentRule=999",
    ]) {
      await navigate(f.page, `/wip/issues/73?${query}`);
      await frames(f.page);
      assert.equal(await f.page.locator(".rule-targeted").count(), 0);
      await disclosure(f.page, 1).locator("summary").click();
      assert.equal(
        await disclosure(f.page, 1).evaluate((node) => node.open),
        true,
      );
      await disclosure(f.page, 1).locator("summary").click();
      assert.equal(
        await disclosure(f.page, 1).evaluate((node) => node.open),
        false,
      );
    }
    await navigate(f.page, "/wip/issues/80?attachmentRule=bad");
    await disclosure(f.page, 19).waitFor();
    assert.equal(
      await disclosure(f.page, 19).evaluate((node) => node.open),
      false,
    );
  } finally {
    await f.close();
  }
});

void test("targeted rule actions and View filters are preserved, rule updates never re-attend a collapsed target, modal focus remains owned", async () => {
  const f = await fixture();
  try {
    await f.page.goto(`${base}/issues/73?attachmentRule=19`);
    await attended(f.page, 19);
    const target = disclosure(f.page, 19);
    const href = await target
      .getByRole("link", { name: "View filters" })
      .getAttribute("href");
    const url = new URL(href, base);
    assert.equal(url.pathname, "/wip/test-results");
    assert.equal(url.searchParams.get("issues"), "73");
    assert.equal(url.searchParams.get("test_cases"), "target criteria");
    await target.getByRole("button", { name: "Disable", exact: true }).click();
    await target.getByRole("button", { name: "Enable", exact: true }).waitFor();
    await target.locator("summary").click();
    await disclosure(f.page, 18).locator("summary").click();
    await disclosure(f.page, 18)
      .getByRole("button", { name: "Disable", exact: true })
      .click();
    await disclosure(f.page, 18)
      .getByRole("button", { name: "Enable", exact: true })
      .waitFor();
    await frames(f.page);
    assert.equal(await target.evaluate((node) => node.open), false);
    await disclosure(f.page, 18)
      .getByRole("button", { name: "Delete", exact: true })
      .click();
    const dialog = f.page.getByRole("dialog", {
      name: "Delete attachment rule?",
    });
    await dialog.waitFor();
    await navigate(f.page, "/wip/issues/73?attachmentRule=20", true);
    await frames(f.page);
    assert.equal(
      await disclosure(f.page, 20).evaluate((node) => node.open),
      true,
    );
    assert.equal(
      await dialog.evaluate((node) => node.contains(document.activeElement)),
      true,
    );
    await dialog.getByRole("button", { name: "Cancel", exact: true }).click();
    await frames(f.page);
    assert.equal(
      await disclosure(f.page, 20)
        .locator("summary")
        .evaluate((node) => node === document.activeElement),
      false,
    );
    await disclosure(f.page, 20)
      .getByRole("button", { name: "Delete", exact: true })
      .click();
    await dialog
      .getByRole("button", { name: "Delete rule", exact: true })
      .click();
    await disclosure(f.page, 20).waitFor({ state: "detached" });
    assert.deepEqual(
      f.requests
        .filter((r) => r.method !== "GET")
        .map(({ path, method }) => ({ path, method })),
      [
        { path: "/v1/issues/73/attachment-rules/19", method: "PATCH" },
        { path: "/v1/issues/73/attachment-rules/18", method: "PATCH" },
        { path: "/v1/issues/73/attachment-rules/20", method: "DELETE" },
      ],
    );
  } finally {
    await f.close(true);
  }
});
