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
      created_at: new Date(
        Date.UTC(2026, 9, 25, 12) - index * 1000,
      ).toISOString(),
      template_id: "template",
      issues: [{ id: issue, key: `QA-${issue}`, title: `Issue ${issue}` }],
    },
    test_execution: {
      id: 7000 + index,
      status: "FAILED",
      environment: { name: index % 2 === 0 ? "test lab" : "other lab" },
      test_plan: "smoke",
      rerun_is_requested: false,
      execution_is_latest: true,
      execution_metadata: [{ category: "literal <metadata>", value: "λ 🧪" }],
    },
    artefact: {
      id: 42,
      name: index % 3 === 0 ? "example artefact" : "other artefact",
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
/** Synthetic server predicate over ALL rows, not just the requested block.
 * Date precision/wire validation is separately exercised by model/mounted tests.
 * @param {ReturnType<typeof row>} item @param {URLSearchParams} params */
function matches(item, params) {
  for (const [key, value] of [
    ["families", item.artefact.family],
    ["artefacts", item.artefact.name],
    ["environments", item.test_execution.environment.name],
    ["test_cases", item.test_result.name],
  ]) {
    const selected = params.getAll(key);
    if (selected.length && !selected.includes(value)) return false;
  }
  const created = Date.parse(item.test_result.created_at);
  if (params.has("from_date") && created < Date.parse(params.get("from_date")))
    return false;
  if (
    params.has("until_date") &&
    created > Date.parse(params.get("until_date"))
  )
    return false;
  return true;
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
    if (url.pathname === "/v1/artefacts/search")
      return reply({ artefacts: ["example artefact", "other artefact"] });
    if (url.pathname === "/v1/environments")
      return reply({ environments: ["test lab", "other lab"] });
    if (url.pathname === "/v1/test-cases")
      return reply({ test_cases: [{ test_case: "issue-73-case-0" }] });
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
      const all =
        issue === 81
          ? []
          : Array.from({ length: total }, (_, n) => row(n, issue)).filter(
              (item) => matches(item, url.searchParams),
            );
      return reply({
        count:
          url.searchParams.get("include_count") === "true" ? all.length : null,
        offset,
        limit,
        rows: all.slice(offset, offset + limit),
      });
    }
    if (/search-page\/\d+$/.test(url.pathname))
      return reply(
        details(Number(url.pathname.split("/").at(-1))),
        detailsStatus,
      );
    // The configured route differs from the API family. Include a newer run so
    // following either View Run must expand the exact older execution/result,
    // not merely navigate to the correct artefact or its latest run.
    if (url.pathname === "/v1/artefacts/42")
      return reply({
        ...row(125).artefact,
        status: "UNDECIDED",
        created_at: "2026-10-25T12:00:00Z",
        due_date: null,
        comment: "",
        all_environment_reviews_count: 0,
        completed_environment_reviews_count: 0,
      });
    if (url.pathname === "/v1/artefacts/42/builds")
      return reply([
        {
          id: 88,
          architecture: "amd64",
          revision: 1,
          test_executions: [8000, 7125].map((id) => ({
            id,
            status: "FAILED",
            test_plan: "smoke",
            created_at: "2026-10-25T12:00:00Z",
            environment: { id: 5, name: "test lab", architecture: "amd64" },
            ci_link: null,
            c3_link: null,
            relevant_links: [],
            execution_metadata: {},
            is_triaged: false,
          })),
        },
      ]);
    if (/^\/v1\/test-executions\/\d+\/test-results$/.test(url.pathname)) {
      const execution = Number(url.pathname.split("/")[3]);
      return reply([
        {
          id: execution === 7125 ? 73125 : 73999,
          name: `Deep linked case ${execution}`,
          status: "FAILED",
          created_at: "2026-10-25T12:00:00Z",
          category: "smoke",
          comment: "",
          template_id: "template",
          io_log: `Exact run target ${execution}`,
          previous_results: [],
          issues: [],
        },
      ]);
    }
    if (
      url.pathname.startsWith("/v1/artefacts/42/") ||
      [
        "/v1/environments/reported-issues",
        "/v1/test-cases/reported-issues",
      ].includes(url.pathname) ||
      url.pathname.endsWith("/status_update")
    )
      return reply([]);
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

  // The actual Pragma disclosure and leaf editors batch every optional group.
  const filters = page.locator(".issue-result-filters");
  const disclosure = filters.getByRole("button", { name: /^Optional filters/ });
  const apply = filters.getByRole("button", {
    name: "Apply filters",
    exact: true,
  });
  const clearDrafts = filters.getByRole("button", {
    name: "Clear optional drafts",
    exact: true,
  });
  const resultReads = () =>
    requests.filter((r) => r.path.endsWith("search-page"));
  const group = (name) =>
    filters.getByRole("region", { name: `${name} filter`, exact: true });
  async function exact(name, field, value) {
    const section = group(name);
    await section.locator(`input[name="${field}"]`).fill(value);
    await section
      .getByRole("button", { name: "Add exact value", exact: true })
      .click();
  }
  async function appliedCount(count) {
    await page
      .getByText(`${count} matching test results on the server.`, {
        exact: false,
      })
      .waitFor();
  }
  async function clearApplied() {
    await clearDrafts.click();
    await apply.click();
    await appliedCount(625);
  }
  await disclosure.focus();
  await page.keyboard.press("Enter");
  assert.equal(await disclosure.getAttribute("aria-expanded"), "true");
  let beforeDraft = resultReads().length;
  const artefactInput = group("Artefact").locator('input[name="artefacts"]');
  await artefactInput.fill("example");
  await group("Artefact")
    .getByRole("button", { name: "example artefact", exact: true })
    .waitFor();
  assert.equal(resultReads().length, beforeDraft);
  assert.equal(await apply.isDisabled(), true);
  await artefactInput.press("Enter");
  assert.equal(
    await apply.isDisabled(),
    true,
    "Enter does not select pending lookup text",
  );
  await group("Artefact")
    .getByRole("button", { name: "example artefact", exact: true })
    .click();
  assert.equal(
    resultReads().length,
    beforeDraft,
    "suggestion selection is not Apply",
  );
  await disclosure.click();
  await disclosure.click();
  assert.equal(
    await group("Artefact")
      .getByText("example artefact", { exact: true })
      .count(),
    1,
  );
  await apply.click();
  await appliedCount(209);
  assert.match(await disclosure.textContent(), /1 applied groups/);
  await clearApplied();

  // Each dimension works independently; the synthetic endpoint filters before paging.
  await group("Family").getByRole("checkbox").first().check();
  await apply.click();
  await appliedCount(624);
  await clearApplied();
  await exact("Environment", "environments", "test lab");
  await apply.click();
  await appliedCount(313);
  // Filtered row 125 is original result 250, beyond both first-page ceilings.
  await grid.evaluate(
    /** @param {HTMLElement} element */ (element) => {
      const scroller = [...element.querySelectorAll("*")]
        .filter(
          (e) =>
            e.scrollHeight > e.clientHeight + 1 &&
            /auto|scroll/.test(getComputedStyle(e).overflowY),
        )
        .sort(
          (a, b) =>
            b.scrollHeight - b.clientHeight - (a.scrollHeight - a.clientHeight),
        )[0];
      scroller.scrollTop = 125 * 30;
    },
  );
  await grid.locator('button[data-test-result-id="73250"]').waitFor();
  assert.ok(
    resultReads().some((r) => {
      const p = new URLSearchParams(r.query);
      return (
        p.get("offset") === "100" &&
        p.get("environments") === "test lab" &&
        p.get("include_count") === "false"
      );
    }),
  );
  await appliedCount(313);
  await clearApplied();
  await exact("Test Case", "test_cases", "issue-73-case-125");
  await apply.click();
  await appliedCount(1);
  await grid.locator('button[data-test-result-id="73125"]').waitFor();
  await clearApplied();

  const from = filters.locator('input[name="from_date"]');
  const until = filters.locator('input[name="until_date"]');
  await from.fill("2026-10-25T12:56:40.000000000+01:00");
  await apply.click();
  await appliedCount(201);
  assert.equal(
    new URLSearchParams(resultReads().at(-1).query).get("from_date"),
    "2026-10-25T12:56:40.000000000+01:00",
  );
  beforeDraft = resultReads().length;
  for (const invalid of [
    "bad",
    "2026-02-30T00:00:00Z",
    "2026-10-25T11:56:40.1234561Z",
    "2026-10-25T11:56:40",
  ]) {
    await from.fill(invalid);
    assert.equal(await apply.isDisabled(), true);
    await filters
      .getByRole("alert")
      .filter({ hasText: "Correct or clear this bound" })
      .waitFor();
    assert.equal(resultReads().length, beforeDraft);
  }
  await from.fill("2026-10-25T12:00:00.123457Z");
  await until.fill("2026-10-25T13:00:00.123456+01:00");
  assert.equal(await apply.isDisabled(), true);
  await filters
    .getByText(/From must not be after Until/)
    .first()
    .waitFor();
  await from.fill("");
  await until.fill("2026-10-25T11:58:20Z");
  await apply.click();
  await appliedCount(525);
  assert.equal(
    new URLSearchParams(resultReads().at(-1).query).has("from_date"),
    false,
  );
  assert.match(await disclosure.textContent(), /1 applied groups/);
  await clearApplied();

  await group("Family").getByRole("checkbox").first().check();
  await exact("Artefact", "artefacts", "example artefact");
  await exact("Environment", "environments", "test lab");
  await exact("Test Case", "test_cases", "issue-73-case-0");
  await from.fill("2026-10-25T13:00:00.000000+01:00");
  await until.fill("2026-10-25T12:00:00.000000Z");
  beforeDraft = resultReads().length;
  await page
    .getByRole("button", {
      name: "View details for issue-73-case-0",
      exact: true,
    })
    .click();
  await dialog.locator("pre").waitFor();
  assert.equal(resultReads().length, beforeDraft);
  assert.equal(await dialog.isVisible(), true);
  // A real native modal prevents background edits; closing retains the draft.
  await page.keyboard.press("Escape");
  await apply.click();
  await appliedCount(1);
  assert.match(await disclosure.textContent(), /5 applied groups/);
  assert.equal(await page.locator("dialog[open]").count(), 0);
  const combined = new URLSearchParams(resultReads().at(-1).query);
  for (const field of [
    "families",
    "artefacts",
    "environments",
    "test_cases",
    "from_date",
    "until_date",
  ])
    assert.ok(combined.has(field));
  assert.deepEqual(combined.getAll("issues"), ["73"]);
  beforeDraft = resultReads().length;
  await clearDrafts.click();
  assert.equal(resultReads().length, beforeDraft);
  assert.match(await disclosure.textContent(), /5 applied groups/);
  await appliedCount(1);
  await apply.click();
  await appliedCount(625);
  assert.match(await disclosure.textContent(), /0 applied groups/);
  assert.deepEqual(
    [...new URLSearchParams(resultReads().at(-1).query).keys()].sort(),
    ["include_count", "issues", "limit", "offset"],
  );
  await disclosure.click();

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
  await disclosure.click();
  await page.evaluate(() => (window.__issueQaHold = "families=api-family"));
  await group("Family").getByRole("checkbox").first().check();
  await apply.click();
  await page.waitForFunction(() => window.__issueQaReleases.length === 1);
  await clearDrafts.click();
  await apply.click();
  await appliedCount(625);
  await page.evaluate(() => {
    window.__issueQaHold = "";
    window.__issueQaReleases.splice(0).forEach((release) => release());
  });
  await appliedCount(625);
  assert.match(await disclosure.textContent(), /0 applied groups/);

  await exact("Environment", "environments", "test lab");
  await page.evaluate(() => (window.__issueQaHold = "search-page/73000"));
  await page
    .getByRole("button", {
      name: "View details for issue-73-case-0",
      exact: true,
    })
    .click();
  await page.waitForFunction(() => window.__issueQaReleases.length === 1);
  // Model-level Apply during a native modal (background pointer use is blocked).
  // This exercises actual dialog teardown before an already-parsed body resumes.
  await apply.evaluate((element) => element.click());
  await appliedCount(313);
  assert.equal(await page.locator("dialog[open]").count(), 0);
  await page.evaluate(() => {
    window.__issueQaHold = "";
    window.__issueQaReleases.splice(0).forEach((release) => release());
  });
  assert.equal(await page.locator("dialog[open]").count(), 0);
  await clearApplied();
  await page.evaluate(() => (window.__issueQaHold = "artefacts/search"));
  await group("Artefact").locator('input[name="artefacts"]').fill("obsolete");
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
  assert.match(await disclosure.textContent(), /0 applied groups/);
  await disclosure.click();
  assert.equal(
    await group("Artefact").locator('input[name="artefacts"]').inputValue(),
    "",
  );
  assert.equal(
    await group("Artefact")
      .getByRole("button", { name: "example artefact", exact: true })
      .count(),
    0,
  );
  await disclosure.click();
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
  const narrowReadCount = resultReads().length;
  await disclosure.focus();
  await page.keyboard.press("Enter");
  assert.equal(await disclosure.getAttribute("aria-expanded"), "true");
  await group("Environment")
    .locator('input[name="environments"]')
    .fill("pending narrow");
  assert.equal(await apply.isDisabled(), true);
  await clearDrafts.click();
  assert.equal(resultReads().length, narrowReadCount);
  const filterBounds = await filters.boundingBox();
  assert.ok(
    filterBounds &&
      filterBounds.x >= 0 &&
      Number(filterBounds.x) + Number(filterBounds.width) <= 800,
  );
  await page.screenshot({
    path: resolve(artifacts, "issue-results-narrow-dark.png"),
    fullPage: true,
  });
  for (const source of ["grid", "Details"]) {
    await page.goto(`${base}/issues/73`);
    await page
      .getByRole("button", {
        name: "View details for issue-73-case-0",
        exact: true,
      })
      .waitFor();
    await scrollTo(125);
    let target = grid.getByRole("link", {
      name: "View Run for issue-73-case-125",
      exact: true,
    });
    if (source === "Details") {
      await trigger.click();
      await dialog.locator("pre").waitFor();
      target = dialog.getByRole("link", {
        name: "View Run for issue-73-case-125",
        exact: true,
      });
    }
    await target.click();
    await page.waitForURL(
      `${base}/configured-route/42?testExecutionId=7125&testResultId=73125`,
    );
    await page
      .getByRole("heading", { name: "other artefact", exact: true })
      .waitFor();
    const literal = page.getByText("Exact run target 7125", { exact: true });
    await literal.waitFor({ state: "visible" });
    assert.equal(
      await literal.evaluate((e) => {
        for (
          let parent = e.parentElement;
          parent;
          parent = parent.parentElement
        )
          if (parent.tagName === "DETAILS" && !parent.open) return false;
        return true;
      }),
      true,
      "actual artefact page expands every target ancestor",
    );
    assert.equal(
      await page.locator("dialog[open]").count(),
      0,
      "Details top layer is removed on actual Run navigation",
    );
  }
  assert.ok(
    requests.some((r) => r.path === "/v1/test-executions/7125/test-results"),
  );
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
