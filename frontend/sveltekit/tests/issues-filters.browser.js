// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0
// Opt-in native Chromium coverage of the real route. Every API call, including
// unexpected writes, is intercepted. No live database or project tooling needed.
/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-argument, @typescript-eslint/no-unsafe-return */
import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { test } from "node:test";
import { createServer } from "vite";

const apiOrigin = "http://localhost:30000";
const rows = Array.from({ length: 54 }, (_, i) => ({
  id: i + 1,
  source: i < 50 ? "github" : "jira",
  project:
    i < 50 ? "canonical/Alpha" : ["Beta", "Gamma", "Delta", "Closed"][i - 50],
  key: String(i + 1),
  title: `Fixture issue ${i + 1}`,
  status: i === 52 ? "unknown" : i === 53 ? "closed" : "open",
  url: `https://github.com/canonical/test-observer/issues/${i + 1}`,
  family: i % 2 ? "deb" : "snap",
}));
const requests = [];
const createdRequests = [];
let holdFreshFacetAfterCreate = false;
let holdNextFacet = false;
let mode = "normal";
let browser;
const server = await createServer({ server: { host: "127.0.0.1", port: 0 } });
try {
  await server.listen();
  const origin = `http://127.0.0.1:${server.httpServer.address().port}`;
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
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.setDefaultTimeout(15000);
  await page.addInitScript(() => {
    window.__heldIssueBodies = [];
    // eslint-disable-next-line @typescript-eslint/unbound-method -- Rebound to the actual response below.
    const read = Response.prototype.json;
    Response.prototype.json = function () {
      if (!this.headers.get("x-qa-hold")) return read.call(this);
      return new Promise((resolve, reject) => {
        window.__heldIssueBodies.push(() =>
          read.call(this).then(resolve, reject),
        );
      });
    };
  });
  await page.route(`${apiOrigin}/**`, async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const headers = {
      "access-control-allow-origin": request.headers().origin ?? origin,
      "access-control-allow-credentials": "true",
      "access-control-allow-headers": "content-type,x-csrf-token",
      "access-control-allow-methods": "GET,PUT,OPTIONS",
      "access-control-expose-headers": "x-qa-hold",
    };
    if (request.method() === "OPTIONS")
      return route.fulfill({ status: 204, headers });
    requests.push({ method: request.method(), url });
    if (url.pathname === "/v1/users/me")
      return route.fulfill({
        status: 200,
        headers,
        contentType: "application/json",
        body: "null",
      });
    if (url.pathname === "/v1/issues" && request.method() === "PUT") {
      const body = JSON.parse(request.postData());
      const id = 500 + createdRequests.length;
      createdRequests.push(body);
      const created = {
        ...rows[0],
        id,
        key: String(id),
        source: "github",
        status: "open",
        family: "snap",
        project: "canonical/CreatedProject",
        title: `Fixture created issue ${id}`,
        url: body.url,
      };
      rows.unshift(created);
      mode = "normal";
      holdNextFacet = holdFreshFacetAfterCreate;
      return route.fulfill({
        status: 200,
        headers,
        contentType: "application/json",
        body: JSON.stringify(created),
      });
    }
    if (url.pathname !== "/v1/issues" || request.method() !== "GET")
      return route.fulfill({
        status: 404,
        headers,
        body: "Mock rejects unexpected endpoint/write",
      });
    const params = url.searchParams;
    const project = params.get("project");
    const query = params.get("q");
    const offset = Number(params.get("offset"));
    const statuses = params.getAll("status");
    const families = params.getAll("families");
    const source = params.get("source");
    const preCreateFacet =
      mode.startsWith("pre-create-facet") && !project && offset === 50;
    const freshFacet = holdNextFacet && !project && offset === 0;
    if (freshFacet) holdNextFacet = false;
    const hold =
      query === "obsolete" ||
      mode === "hold-session" ||
      (mode === "hold-facet" && !project) ||
      preCreateFacet;
    if (hold || freshFacet) headers["x-qa-hold"] = "true";
    if (
      (mode === "facet-error" && !project) ||
      (mode === "late-error" && hold) ||
      (mode === "pre-create-facet-error" && preCreateFacet)
    )
      return route.fulfill({
        status: 503,
        headers,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Obsolete or local facet failure" }),
      });
    let matches = rows.filter(
      (row) =>
        (!project || row.project === project) &&
        (!source || row.source === source) &&
        (!statuses.length || statuses.includes(row.status)) &&
        (!families.length || families.includes(row.family)),
    );
    if (query === "nothing") matches = [];
    let pageRows = matches.slice(offset, offset + 50);
    if (hold)
      pageRows = [
        {
          ...rows[0],
          id: 999,
          project: "Obsolete/project",
          title: "Obsolete issue",
        },
      ];
    if (mode === "overlap" && offset === 50)
      pageRows = [rows[0], rows[50], rows[51]];
    if (mode === "overlap" && offset === 53) pageRows = [rows[52]];
    await route.fulfill({
      status: 200,
      headers,
      contentType: "application/json",
      body: JSON.stringify({
        issues: pageRows,
        count: mode === "overlap" ? 54 : matches.length,
        offset,
        limit: 50,
      }),
    });
  });
  const settle = () =>
    page.evaluate(
      () =>
        new Promise((resolve) =>
          requestAnimationFrame(() => requestAnimationFrame(resolve)),
        ),
    );
  const listRequests = () =>
    requests.filter((request) => request.url.pathname === "/v1/issues");
  const broadRequests = () =>
    listRequests().filter(
      (request) => !request.url.searchParams.has("project"),
    );
  const navigate = (path) =>
    page.evaluate(async (path) => {
      const resource = performance
        .getEntriesByType("resource")
        .find((entry) =>
          entry.name.includes("/runtime/app/navigation/index.js"),
        );
      const { goto } = await import(resource.name);
      await goto(path, { reset: false });
    }, path);
  const open = async (query = "") => {
    mode = "normal";
    await page.goto(`${base}/issues${query}`);
    await page
      .getByRole("button", { name: "Hide filters", exact: true })
      .waitFor();
    await page.locator(".issue-title").first().waitFor();
    await page
      .getByLabel("Project options", { exact: true })
      .getByLabel("canonical/Alpha", { exact: true })
      .waitFor();
  };

  await test("disclosure hides layout/tab stops without losing drafts, option substring, URL or applied indicator", async () => {
    await open();
    await page.getByText("0 active filter groups", { exact: true }).waitFor();
    const start = listRequests().length;
    await page
      .getByLabel("Search issues", { exact: true })
      .fill("unapplied issue draft");
    await page
      .getByLabel("Search project options", { exact: true })
      .fill("lPhA");
    await page
      .getByRole("button", { name: "Hide filters", exact: true })
      .click();
    assert.equal(await page.locator("#issue-filters").isVisible(), false);
    assert.equal(
      await page
        .locator("#issue-filters")
        .evaluate((element) => getComputedStyle(element).display),
      "none",
    );
    assert.equal(
      await page
        .getByRole("button", { name: "Show filters" })
        .getAttribute("aria-expanded"),
      "false",
    );
    assert.equal(new URL(page.url()).search, "");
    await page.setViewportSize({ width: 800, height: 900 });
    assert.equal(
      await page
        .locator("#issue-filters")
        .evaluate((element) => getComputedStyle(element).display),
      "none",
      "responsive display rules must not override hidden",
    );
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.getByText("0 active filter groups", { exact: true }).waitFor();
    await page.getByRole("button", { name: "Show filters" }).press("Enter");
    assert.equal(
      await page.getByLabel("Search issues", { exact: true }).inputValue(),
      "unapplied issue draft",
    );
    assert.equal(
      await page
        .getByLabel("Search project options", { exact: true })
        .inputValue(),
      "lPhA",
    );
    assert.equal(listRequests().length, start);
    await page.goto(
      `${base}/issues?source=github&status=closed&family=snap&project=unloaded&q=applied`,
    );
    await page.getByText("5 active filter groups", { exact: true }).waitFor();
    await page
      .getByRole("button", { name: "Hide filters", exact: true })
      .click();
    assert.equal(new URL(page.url()).searchParams.get("q"), "applied");
    await page.getByText("5 active filter groups", { exact: true }).waitFor();
    await page.goto(`${base}/issues?status=`);
    await page.getByText("1 active filter group", { exact: true }).waitFor();
    await page.getByText("All statuses", { exact: true }).waitFor();
    await page.goto(`${base}/issues?status=unknown&status=open`);
    await page.getByText("0 active filter groups", { exact: true }).waitFor();
  });

  await test("native substring search, pointer/Space multi-selection and Enter removal use singular API and independent facets", async () => {
    await open("?project=Beta");
    await page
      .getByRole("link", { name: "Fixture issue 51", exact: true })
      .waitFor();
    const broadCount = broadRequests().length;
    const search = page.getByLabel("Search project options", { exact: true });
    await search.fill("ALpHa");
    const option = page.getByRole("checkbox", {
      name: "canonical/Alpha",
      exact: true,
    });
    assert.equal(
      await page
        .getByLabel("Project options", { exact: true })
        .getByRole("checkbox")
        .count(),
      1,
    );
    await option.focus();
    await option.press("Space");
    await page.waitForURL(
      (url) => url.searchParams.getAll("project").length === 2,
    );
    await page
      .getByRole("link", { name: "Fixture issue 1", exact: true })
      .waitFor();
    assert.equal(listRequests().at(-1).url.searchParams.has("project"), false);
    assert.equal(listRequests().at(-1).url.searchParams.get("offset"), "0");
    assert.equal(
      broadRequests().length,
      broadCount + 1,
      "only the main multi-project query is added",
    );
    await page
      .getByRole("button", {
        name: "Remove project canonical/Alpha",
        exact: true,
      })
      .focus();
    await page
      .getByRole("button", {
        name: "Remove project canonical/Alpha",
        exact: true,
      })
      .press("Enter");
    await page.waitForURL(
      (url) => url.searchParams.getAll("project").join() === "Beta",
    );
    await page
      .getByRole("link", { name: "Fixture issue 51", exact: true })
      .waitFor();
    assert.equal(listRequests().at(-1).url.searchParams.get("project"), "Beta");
    assert.equal(listRequests().at(-1).url.searchParams.get("offset"), "0");
    assert.equal(await search.inputValue(), "ALpHa");
    assert.equal(
      await search.evaluate((element) => element === document.activeElement),
      true,
    );
    await search.fill("");
    await page
      .getByRole("checkbox", { name: "canonical/Alpha", exact: true })
      .check();
    await page.waitForURL(
      (url) => url.searchParams.getAll("project").length === 2,
    );
  });

  await test("URL/reload and native history restore selections, rapid toggles compose without dropping earlier values", async () => {
    await open("?project=Beta");
    await page
      .getByRole("checkbox", { name: "canonical/Alpha", exact: true })
      .check();
    await page.waitForURL(
      (url) => url.searchParams.getAll("project").length === 2,
    );
    await page.goBack();
    await page.waitForURL(
      (url) => url.searchParams.getAll("project").join() === "Beta",
    );
    await page
      .getByRole("link", { name: "Fixture issue 51", exact: true })
      .waitFor();
    assert.equal(
      await page
        .getByRole("checkbox", { name: "canonical/Alpha", exact: true })
        .isChecked(),
      false,
    );
    await page.goForward();
    await page.waitForURL(
      (url) => url.searchParams.getAll("project").length === 2,
    );
    await page.reload();
    await page
      .getByRole("button", { name: "Remove project Beta", exact: true })
      .waitFor();
    assert.equal(
      await page
        .getByRole("checkbox", { name: "canonical/Alpha", exact: true })
        .isChecked(),
      true,
    );
    await page
      .getByRole("button", { name: "Load more project options", exact: true })
      .click();
    await page.getByRole("checkbox", { name: "Gamma", exact: true }).waitFor();
    await page.evaluate(() => {
      const inputs = [...document.querySelectorAll('input[type="checkbox"]')];
      inputs.find((element) => element.value === "Gamma").click();
      inputs.find((element) => element.value === "Delta").click();
    });
    await page.waitForURL(
      (url) => url.searchParams.getAll("project").length === 4,
    );
    assert.deepEqual(
      new URL(page.url()).searchParams.getAll("project").sort(),
      ["Beta", "Delta", "Gamma", "canonical/Alpha"].sort(),
    );
    await page.goto(`${base}/issues?project=unloaded/kept`);
    await page
      .getByRole("button", {
        name: "Remove project unloaded/kept",
        exact: true,
      })
      .waitFor();
    await page
      .getByRole("checkbox", { name: "unloaded/kept", exact: true })
      .waitFor();
    assert.equal(
      await page
        .getByRole("checkbox", { name: "unloaded/kept", exact: true })
        .isChecked(),
      true,
    );
  });

  await test("bounded project discovery pages independently, keeps progress on selection, and resets for other applied filters", async () => {
    await open("?project=Beta");
    await page.getByText(/Discovery is incomplete/).waitFor();
    assert.equal(
      await page.getByRole("checkbox", { name: "Gamma", exact: true }).count(),
      0,
    );
    const before = listRequests().length;
    await page
      .getByRole("button", { name: "Load more project options", exact: true })
      .click();
    await page.getByRole("checkbox", { name: "Gamma", exact: true }).waitFor();
    assert.equal(listRequests().length, before + 1);
    assert.equal(listRequests().at(-1).url.searchParams.get("offset"), "50");
    assert.equal(listRequests().at(-1).url.searchParams.has("project"), false);
    await page.getByText(/All 53 issue rows in this discovery/).waitFor();
    assert.equal(await page.locator(".issue-title").count(), 1);
    await page.getByRole("checkbox", { name: "Gamma", exact: true }).check();
    await page.waitForURL(
      (url) => url.searchParams.getAll("project").length === 2,
    );
    await page.getByText(/All 53 issue rows in this discovery/).waitFor();
    await page.getByLabel("JIRA", { exact: true }).check();
    await page
      .getByRole("link", { name: "Fixture issue 51", exact: true })
      .waitFor();
    await page.getByText(/All 3 issue rows in this discovery/).waitFor();
    assert.equal(
      await page
        .getByRole("checkbox", { name: "canonical/Alpha", exact: true })
        .count(),
      0,
    );
    assert.equal(listRequests().at(-1).url.searchParams.get("offset"), "0");
    assert.equal(listRequests().at(-1).url.searchParams.get("source"), "jira");
  });

  await test("facet failure/retry stays local and retains selected values and valid issue rows", async () => {
    mode = "facet-error";
    await page.goto(`${base}/issues?project=Beta`);
    await page
      .getByRole("link", { name: "Fixture issue 51", exact: true })
      .waitFor();
    await page.getByText(/Unable to load project options/).waitFor();
    await page
      .getByRole("button", { name: "Remove project Beta", exact: true })
      .waitFor();
    assert.equal(
      await page.getByText("No issues found.", { exact: true }).count(),
      0,
    );
    const resultCount = listRequests().filter((request) =>
      request.url.searchParams.has("project"),
    ).length;
    mode = "normal";
    await page
      .getByRole("button", { name: "Retry project options", exact: true })
      .click();
    await page
      .getByRole("checkbox", { name: "canonical/Alpha", exact: true })
      .waitFor();
    assert.equal(await page.getByRole("alert").count(), 0);
    assert.equal(
      listRequests().filter((request) =>
        request.url.searchParams.has("project"),
      ).length,
      resultCount,
    );
  });

  await test("a pending independent facet survives project selection, but an unmounted list cannot reuse its late bodies", async () => {
    mode = "hold-facet";
    await page.goto(`${base}/issues?project=Beta`);
    await page
      .getByRole("link", { name: "Fixture issue 51", exact: true })
      .waitFor();
    await page.waitForFunction(() => window.__heldIssueBodies.length === 1);
    const before = broadRequests().length;
    await page
      .getByRole("button", { name: "Remove project Beta", exact: true })
      .click();
    await page.waitForURL((url) => !url.searchParams.has("project"));
    await page.waitForFunction(() => window.__heldIssueBodies.length === 2);
    assert.equal(
      broadRequests().length,
      before + 1,
      "only the new result stream starts, not a second facet stream",
    );
    await page.evaluate(() =>
      window.__heldIssueBodies.splice(0).forEach((release) => release()),
    );
    await page
      .getByRole("checkbox", { name: "Obsolete/project", exact: true })
      .waitFor();
    await page
      .getByRole("link", { name: "Obsolete issue", exact: true })
      .waitFor();
    mode = "hold-session";
    await page.goto(`${base}/issues?project=Beta`);
    await page.waitForFunction(() => window.__heldIssueBodies.length === 2);
    await navigate(`${base}/issues/900`);
    mode = "normal";
    await navigate(`${base}/issues?project=Beta`);
    await page
      .getByRole("link", { name: "Fixture issue 51", exact: true })
      .waitFor();
    await page
      .getByRole("checkbox", { name: "canonical/Alpha", exact: true })
      .waitFor();
    await page.evaluate(() =>
      window.__heldIssueBodies.splice(0).forEach((release) => release()),
    );
    await settle();
    assert.equal(
      await page
        .getByRole("checkbox", { name: "Obsolete/project", exact: true })
        .count(),
      0,
    );
    assert.equal(
      await page
        .getByRole("link", { name: "Obsolete issue", exact: true })
        .count(),
      0,
    );
    assert.equal(await page.getByRole("alert").count(), 0);
  });

  await test("local project OR is not a false global empty result; paging uses raw offsets and deduplicates overlaps", async () => {
    mode = "overlap";
    await page.goto(`${base}/issues?project=Beta&project=Gamma`);
    await page
      .getByText("No matching issues on the loaded pages yet.", { exact: true })
      .waitFor();
    assert.equal(
      await page.getByText("No issues found.", { exact: true }).count(),
      0,
    );
    await page.getByRole("button", { name: /Load more issues/ }).click();
    await page
      .getByRole("link", { name: "Fixture issue 51", exact: true })
      .waitFor();
    await page
      .getByRole("link", { name: "Fixture issue 52", exact: true })
      .waitFor();
    assert.equal(await page.locator(".issue-title").count(), 2);
    await page.getByRole("button", { name: /Load more issues/ }).click();
    await page
      .getByRole("button", { name: /Load more issues/ })
      .waitFor({ state: "hidden" });
    assert.equal(listRequests().at(-1).url.searchParams.get("offset"), "53");
    assert.equal(await page.locator(".issue-title").count(), 2);
    assert.equal(listRequests().at(-1).url.searchParams.has("project"), false);
  });

  await test("held row/facet successes and parsed errors cannot replace a newer query or session", async () => {
    for (const lateMode of ["normal", "late-error"]) {
      mode = lateMode;
      await page.goto(`${base}/issues?project=Beta&q=obsolete`);
      await page.waitForFunction(() => window.__heldIssueBodies.length === 2);
      await page.getByLabel("Search issues", { exact: true }).fill("fresh");
      await page.getByRole("button", { name: "Search", exact: true }).click();
      await page
        .getByRole("link", { name: "Fixture issue 51", exact: true })
        .waitFor();
      await page
        .getByRole("checkbox", { name: "canonical/Alpha", exact: true })
        .waitFor();
      await page.evaluate(() =>
        window.__heldIssueBodies.splice(0).forEach((release) => release()),
      );
      await settle();
      assert.equal(await page.getByRole("alert").count(), 0);
      assert.equal(
        await page
          .getByRole("link", { name: "Obsolete issue", exact: true })
          .count(),
        0,
      );
      assert.equal(
        await page
          .getByRole("checkbox", { name: "Obsolete/project", exact: true })
          .count(),
        0,
      );
    }
    mode = "hold-session";
    await page.goto(`${base}/issues?project=Beta`);
    await page.waitForFunction(() => window.__heldIssueBodies.length === 2);
    mode = "normal";
    await page.evaluate(async () => {
      const { userStore } = await import("/wip/src/lib/stores/user.svelte.ts");
      userStore.current = {
        id: 43,
        name: "Fixture session",
        is_admin: false,
        teams: [],
      };
    });
    await page
      .getByRole("link", { name: "Fixture issue 51", exact: true })
      .waitFor();
    await page
      .getByRole("checkbox", { name: "canonical/Alpha", exact: true })
      .waitFor();
    await page.evaluate(() =>
      window.__heldIssueBodies.splice(0).forEach((release) => release()),
    );
    await settle();
    assert.equal(
      await page
        .getByRole("checkbox", { name: "Obsolete/project", exact: true })
        .count(),
      0,
    );
    assert.equal(
      await page
        .getByRole("link", { name: "Obsolete issue", exact: true })
        .count(),
      0,
    );
    assert.equal(await page.getByRole("alert").count(), 0);
    assert.equal(
      requests.some((request) => request.method !== "GET"),
      false,
    );
    assert.deepEqual(errors, []);
  });

  await test("native checkbox restoration respects intervening focus intent across real navigation and inert cleanup", async () => {
    await open("?project=Beta");
    const audits = [];
    try {
      for (let trial = 0; trial < 5; trial++) {
        await page.evaluate(() => {
          const option = document.querySelector(
            'input[value="canonical/Alpha"]',
          );
          const issueSearch = document.querySelector("#issue-search");
          const content = document.querySelector(".page-content");
          const events = [];
          const snapshot = (type, target) => ({
            type,
            time: performance.now(),
            id: target?.id,
            value: target?.value,
            source: target === option,
            inert: content.inert,
          });
          const focus = (event) =>
            events.push(snapshot("focusin", event.target));
          const observer = new MutationObserver(() =>
            events.push(snapshot("inert")),
          );
          document.addEventListener("focusin", focus, true);
          observer.observe(content, {
            attributes: true,
            attributeFilter: ["inert"],
          });
          option.focus();
          option.click();
          issueSearch.focus();
          window.__pickerFocusAudit = {
            events,
            secondFocusSucceeded:
              document.activeElement === issueSearch && !content.inert,
            stop: () => {
              document.removeEventListener("focusin", focus, true);
              observer.disconnect();
            },
          };
        });
        await page.waitForURL(
          (url) =>
            url.searchParams.getAll("project").length === (trial % 2 ? 1 : 2),
        );
        await page.waitForFunction(
          () => !document.querySelector(".page-content").inert,
        );
        await settle();
        const audit = await page.evaluate(() => {
          const audit = window.__pickerFocusAudit;
          audit.stop();
          return {
            events: audit.events,
            secondFocusSucceeded: audit.secondFocusSucceeded,
            finalValue: document.activeElement?.value,
            finalId: document.activeElement?.id,
          };
        });
        audits.push({ trial, ...audit });
        assert.equal(
          audit.secondFocusSucceeded,
          true,
          "the deliberate second focus must actually succeed before navigation makes content inert",
        );
        const secondFocus = /** @type {number} */ (
          audit.events.findIndex(
            (event) => event.type === "focusin" && event.id === "issue-search",
          )
        );
        assert.ok(
          secondFocus >= 0,
          "record the native focusin on the user's destination",
        );
        assert.equal(
          audit.events
            .slice(secondFocus + 1)
            .some((event) => event.type === "focusin" && event.source),
          false,
          "never restore the old checkbox after the intervening control intent",
        );
        assert.notEqual(audit.finalValue, "canonical/Alpha");
        assert.ok(
          audit.events.some((event) => event.type === "inert" && event.inert),
          "exercise the actual shell navigation inert interval",
        );
        assert.ok(
          audit.events.some((event) => event.type === "inert" && !event.inert),
          "observe native navigation cleanup",
        );
      }
      // When no other control receives focus, the native navigation-only blur
      // must still restore the source checkbox (rather than disabling restoration).
      await page.evaluate(() => {
        const option = document.querySelector('input[value="canonical/Alpha"]');
        option.focus();
        option.click();
      });
      await page.waitForURL(
        (url) => url.searchParams.getAll("project").length === 1,
      );
      await page.waitForFunction(
        () => !document.querySelector(".page-content").inert,
      );
      await settle();
      assert.equal(
        await page
          .getByRole("checkbox", { name: "canonical/Alpha", exact: true })
          .evaluate((element) => element === document.activeElement),
        true,
        "owned restoration survives actual navigation",
      );
    } finally {
      await page.evaluate(() => window.__pickerFocusAudit?.stop());
      const directory =
        process.env.QA_ARTIFACT_DIR ?? "/tmp/opencode/issues-filters-browser";
      await mkdir(directory, { recursive: true });
      await writeFile(
        join(directory, "focus-intent-audits.json"),
        JSON.stringify(audits, null, 2),
      );
    }
  });

  await test("confirmed creation refreshes exhausted discovery and retains applied filters, hidden state and drafts", async () => {
    await open("?source=github&status=open&family=snap&q=Fixture");
    await page.getByText(/All 25 issue rows in this discovery/).waitFor();
    assert.equal(
      await page
        .getByRole("button", { name: "Load more project options", exact: true })
        .count(),
      0,
    );
    assert.equal(
      await page
        .getByRole("checkbox", {
          name: "canonical/CreatedProject",
          exact: true,
        })
        .count(),
      0,
    );
    await page
      .getByLabel("Search issues", { exact: true })
      .fill("unapplied issue draft");
    await page
      .getByLabel("Search project options", { exact: true })
      .fill("createdPROJ");
    await page
      .getByRole("button", { name: "Hide filters", exact: true })
      .click();
    const appliedUrl = page.url();
    const before = requests.length;
    const writes = createdRequests.length;
    const id = 500 + writes;
    const issueUrl = `https://github.com/canonical/new-project/issues/${id}`;
    try {
      await page
        .getByRole("button", { name: "Add issue", exact: true })
        .click();
      const dialog = page.getByRole("dialog", {
        name: "Add issue",
        exact: true,
      });
      await dialog.getByLabel("External issue URL").fill(issueUrl);
      await dialog
        .getByRole("button", { name: "Add issue", exact: true })
        .click();
      await dialog.waitFor({ state: "hidden" });
      await page
        .getByRole("link", { name: `Fixture created issue ${id}`, exact: true })
        .waitFor();
      assert.equal(page.url(), appliedUrl);
      assert.equal(await page.locator("#issue-filters").isVisible(), false);
      await page
        .getByRole("button", { name: "Show filters", exact: true })
        .click();
      await page
        .getByRole("checkbox", {
          name: "canonical/CreatedProject",
          exact: true,
        })
        .waitFor();
      await page.getByText(/All 26 issue rows in this discovery/).waitFor();
      assert.equal(
        await page.getByLabel("Search issues", { exact: true }).inputValue(),
        "unapplied issue draft",
      );
      assert.equal(
        await page
          .getByLabel("Search project options", { exact: true })
          .inputValue(),
        "createdPROJ",
      );
      for (const value of ["github", "open", "snap"])
        assert.equal(
          await page.locator(`input[value="${value}"]`).isChecked(),
          true,
        );
      assert.equal(
        await page
          .getByRole("checkbox", {
            name: "canonical/CreatedProject",
            exact: true,
          })
          .isChecked(),
        false,
      );
      await page.getByText("4 active filter groups", { exact: true }).waitFor();
      assert.deepEqual(createdRequests.slice(writes), [{ url: issueUrl }]);
      const refreshes = requests
        .slice(before)
        .filter(
          (request) =>
            request.method === "GET" && request.url.pathname === "/v1/issues",
        );
      assert.equal(
        refreshes.length,
        2,
        "both result and independent facet streams refresh once",
      );
      for (const request of refreshes) {
        const params = request.url.searchParams;
        assert.equal(params.get("offset"), "0");
        assert.equal(params.get("source"), "github");
        assert.deepEqual(params.getAll("status"), ["open"]);
        assert.deepEqual(params.getAll("families"), ["snap"]);
        assert.equal(
          params.get("q"),
          "Fixture",
          "pending issue text is not applied on create",
        );
      }
      assert.deepEqual(errors, []);
    } finally {
      const createdIndex = rows.findIndex((row) => row.id === id);
      if (createdIndex >= 0) rows.splice(createdIndex, 1);
    }
  });

  await test("confirmed creation invalidates pre-create facet pages and parsed errors without extending Add pending state", async () => {
    for (const oldMode of [
      "pre-create-facet-success",
      "pre-create-facet-error",
    ]) {
      await open("?project=Beta");
      mode = oldMode;
      await page
        .getByRole("button", { name: "Load more project options", exact: true })
        .click();
      await page.waitForFunction(() => window.__heldIssueBodies.length === 1);
      const writes = createdRequests.length;
      const id = 500 + writes;
      holdFreshFacetAfterCreate = true;
      try {
        await page
          .getByRole("button", { name: "Add issue", exact: true })
          .click();
        const dialog = page.getByRole("dialog", {
          name: "Add issue",
          exact: true,
        });
        await dialog
          .getByLabel("External issue URL")
          .fill(`https://github.com/canonical/new-project/issues/${id}`);
        await dialog
          .getByRole("button", { name: "Add issue", exact: true })
          .click();
        await dialog.waitFor({ state: "hidden" });
        await page.waitForFunction(() => window.__heldIssueBodies.length === 2);
        await page
          .getByRole("link", { name: "Fixture issue 51", exact: true })
          .waitFor();
        // The new facet request is still parsing. Creating must finish with the
        // result refresh, just as before, not wait for this independent stream.
        await page
          .getByRole("button", { name: "Add issue", exact: true })
          .click();
        await dialog.waitFor();
        await page.waitForFunction(
          () =>
            !document.querySelector('.dialog-actions button[type="submit"]')
              .disabled,
        );
        await dialog.press("Escape");
        await dialog.waitFor({ state: "hidden" });
        await page.evaluate(() => window.__heldIssueBodies.pop()());
        await page
          .getByRole("checkbox", {
            name: "canonical/CreatedProject",
            exact: true,
          })
          .waitFor();
        await page
          .getByRole("checkbox", { name: "Beta", exact: true })
          .waitFor();
        assert.equal(
          await page
            .getByRole("checkbox", { name: "Beta", exact: true })
            .isChecked(),
          true,
        );
        await page.evaluate(() => window.__heldIssueBodies.shift()());
        await settle();
        assert.equal(
          await page
            .getByRole("checkbox", { name: "Obsolete/project", exact: true })
            .count(),
          0,
        );
        assert.equal(await page.getByRole("alert").count(), 0);
        assert.equal(
          await page
            .getByRole("checkbox", {
              name: "canonical/CreatedProject",
              exact: true,
            })
            .count(),
          1,
        );
        await page.getByText(/Discovery is incomplete/).waitFor();
        await page
          .getByRole("button", {
            name: "Load more project options",
            exact: true,
          })
          .click();
        await page.getByText(/All 54 issue rows in this discovery/).waitFor();
        assert.equal(new URL(page.url()).searchParams.get("project"), "Beta");
        assert.equal(createdRequests.length, writes + 1);
        assert.deepEqual(errors, []);
      } finally {
        holdFreshFacetAfterCreate = false;
        holdNextFacet = false;
        const createdIndex = rows.findIndex((row) => row.id === id);
        if (createdIndex >= 0) rows.splice(createdIndex, 1);
      }
    }
  });
} finally {
  if (browser) await browser.close();
  await server.close();
}
