// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0
// Opt-in native Chromium tests: every API endpoint/write is intercepted. No
// tracker record or shared database is contacted by this runner.
/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-argument, @typescript-eslint/no-unsafe-return */
import assert from "node:assert/strict";
import { test } from "node:test";
import { createServer } from "vite";

const apiOrigin = "http://localhost:30000";
const row = (id, project = "Alpha") => ({
  id,
  project,
  source: "github",
  key: String(id),
  title: `Fixture issue ${id}`,
  status: "open",
  url: `https://github.com/canonical/test-observer/issues/${id}`,
});
const requests = [];
let put = { status: 200, body: row(1), hold: false };
let reads = "normal";
let profile = null;
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
  page.setDefaultTimeout(15000);
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.addInitScript(() => {
    window.__heldAddBodies = [];
    // eslint-disable-next-line @typescript-eslint/unbound-method -- Rebound to actual Response below.
    const read = Response.prototype.json;
    Response.prototype.json = function () {
      if (!this.headers.get("x-qa-hold")) return read.call(this);
      return new Promise((resolve, reject) => {
        window.__heldAddBodies.push(() =>
          read.call(this).then(resolve, reject),
        );
      });
    };
  });
  await page.route(`${apiOrigin}/**`, (route) => {
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
    requests.push({ method: request.method(), url, body: request.postData() });
    const reply = (body, status = 200) =>
      route.fulfill({
        status,
        headers,
        contentType: "application/json",
        body: JSON.stringify(body),
      });
    if (url.pathname === "/v1/users/me") return reply(profile);
    if (url.pathname === "/v1/issues" && request.method() === "PUT") {
      if (put.status === 0) return route.abort("failed");
      if (put.hold) headers["x-qa-hold"] = "true";
      return reply(put.body, put.status);
    }
    if (url.pathname === "/v1/issues" && request.method() === "GET") {
      if (reads === "hold") headers["x-qa-hold"] = "true";
      if (reads === "error")
        return reply({ detail: "Fixture read failure" }, 503);
      let rows = [row(1), row(2, "Beta")];
      // Facet-only ID must never count as a known main-result duplicate.
      if (url.searchParams.get("project") === "Beta") rows = [row(2, "Beta")];
      else if (!url.searchParams.has("project"))
        rows.push(row(99, "FacetOnly"));
      return reply({ issues: rows, count: rows.length, offset: 0, limit: 50 });
    }
    return reply({ detail: "Mock rejects unexpected endpoint/write" }, 404);
  });
  const settle = () =>
    page.evaluate(
      () =>
        new Promise((resolve) =>
          requestAnimationFrame(() => requestAnimationFrame(resolve)),
        ),
    );
  const getCount = () =>
    requests.filter(
      (r) => r.method === "GET" && r.url.pathname === "/v1/issues",
    ).length;
  const writes = () => requests.filter((r) => r.method !== "GET");
  const trigger = () =>
    page
      .locator(".page-header")
      .getByRole("button", { name: "Add issue", exact: true });
  const dialog = () =>
    page.getByRole("dialog", { name: "Add issue", exact: true });
  const open = async (query = "") => {
    reads = "normal";
    profile = null;
    put = { status: 200, body: row(1), hold: false };
    await page.goto(`${base}/issues${query}`);
    await page.locator(".issue-title").first().waitFor();
    await page
      .getByLabel("Project options", { exact: true })
      .getByLabel("Alpha", { exact: true })
      .waitFor();
  };
  const show = async () => {
    await trigger().click();
    await dialog().waitFor();
  };
  const submit = async () => {
    await dialog()
      .getByLabel("External issue URL")
      .fill("https://github.com/canonical/test-observer/issues/7");
    await dialog().getByLabel("External issue URL").press("Enter");
  };
  const release = () =>
    page.evaluate(() => window.__heldAddBodies.splice(0).forEach((fn) => fn()));
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
  const refreshSession = () =>
    page.evaluate(async () => {
      const { userStore } = await import("/wip/src/lib/stores/user.svelte.ts");
      await userStore.refresh(window.fetch.bind(window));
    });

  await test("actual Pragma Modal supports pointer/Enter opening, native containment, Escape/cancel/X/outside and native focus return", async () => {
    await open();
    const start = writes().length;
    for (const action of ["escape", "cancel", "header", "outside"]) {
      await trigger().focus();
      await trigger().press("Enter");
      await dialog().waitFor();
      assert.equal(
        await dialog().evaluate((el) => el.matches("dialog.ds.modal:modal")),
        true,
      );
      assert.equal(
        await page.evaluate(
          () => getComputedStyle(document.documentElement).overflow,
        ),
        "hidden",
      );
      await page.locator("#issue-search").evaluate((el) => el.focus());
      assert.equal(
        await dialog().evaluate((el) => el.contains(document.activeElement)),
        true,
      );
      for (let i = 0; i < 10; i++) {
        await page.keyboard.press(i % 2 ? "Shift+Tab" : "Tab");
        assert.equal(
          await dialog().evaluate((el) => el.contains(document.activeElement)),
          true,
        );
      }
      if (action === "escape") await page.keyboard.press("Escape");
      if (action === "cancel")
        await dialog()
          .getByRole("button", { name: "Cancel", exact: true })
          .click();
      if (action === "header")
        await dialog()
          .getByRole("button", { name: "Close Add issue", exact: true })
          .click();
      if (action === "outside") await page.mouse.click(2, 2);
      await dialog().waitFor({ state: "hidden" });
      assert.equal(
        await trigger().evaluate((el) => el === document.activeElement),
        true,
        action,
      );
      assert.notEqual(
        await page.evaluate(
          () => getComputedStyle(document.documentElement).overflow,
        ),
        "hidden",
      );
    }
    await show();
    await dialog().getByRole("button", { name: "Cancel", exact: true }).click();
    await dialog().waitFor({ state: "hidden" });
    assert.equal(writes().length, start);
  });

  await test("known ID hidden by local project OR gets persistent accessible already-added feedback before both refreshes", async () => {
    await open("?project=Beta&project=Gamma");
    assert.equal(
      await page
        .getByRole("link", { name: "Fixture issue 1", exact: true })
        .count(),
      0,
    );
    const start = getCount();
    const writeStart = writes().length;
    await show();
    reads = "hold";
    await submit();
    await dialog().waitFor({ state: "hidden" });
    await page.waitForFunction(() => window.__heldAddBodies.length === 2);
    await page
      .getByRole("status")
      .filter({ hasText: "Issue 1 is already added to Test Observer." })
      .waitFor();
    assert.equal(getCount(), start + 2);
    assert.equal(writes().length, writeStart + 1);
    assert.equal(writes().at(-1).method, "PUT");
    assert.deepEqual(JSON.parse(writes().at(-1).body), {
      url: "https://github.com/canonical/test-observer/issues/7",
    });
    assert.equal(
      await trigger().evaluate((el) => el === document.activeElement),
      true,
    );
    // Reopening/cancelling does not clear confirmed feedback or wait for reads.
    await show();
    await dialog().getByRole("button", { name: "Cancel", exact: true }).click();
    await dialog().waitFor({ state: "hidden" });
    await release();
    await settle();
    await page
      .getByRole("status")
      .filter({ hasText: "Issue 1 is already added to Test Observer." })
      .waitFor();
  });

  await test("unseen/facet-only IDs use neutral wording; confirmed feedback survives failed refreshes and clears on context navigation", async () => {
    for (const id of [99, 1234]) {
      await open("?project=Beta");
      put.body = row(id);
      await show();
      reads = "error";
      await submit();
      await dialog().waitFor({ state: "hidden" });
      await page.getByText(/Unable to load issues/).waitFor();
      const feedback = page.locator(".add-feedback");
      assert.equal(
        await feedback.textContent(),
        `Issue ${id} is available in Test Observer.`,
      );
      assert.doesNotMatch(await feedback.textContent(), /already|new|created/i);
      await page.getByText(/Unable to load project options/).waitFor();
      reads = "normal";
      await navigate(`${base}/issues?q=changed`);
      assert.equal(await feedback.textContent(), "");
    }
  });

  await test("invalid URL/403/transport/invalid ID recovery has no automatic retries or premature refresh; pending blocks every close and repeated form event", async () => {
    await open();
    await show();
    const start = writes().length;
    const beforeReads = getCount();
    await dialog()
      .getByLabel("External issue URL")
      .fill("https://example.test/7");
    await dialog().getByLabel("External issue URL").press("Enter");
    await dialog().getByRole("alert").waitFor();
    assert.equal(writes().length, start);
    for (const body of [
      { detail: '<img src=x onerror="bad()"> denied' },
      { id: 0 },
    ]) {
      put = { body, status: body.id === 0 ? 200 : 403, hold: false };
      await submit();
      await dialog().getByRole("alert").waitFor();
      assert.equal(await dialog().locator("img").count(), 0);
      assert.equal(
        await dialog().getByLabel("External issue URL").isEnabled(),
        true,
      );
      assert.equal(getCount(), beforeReads);
      assert.equal(await page.locator(".add-feedback").textContent(), "");
    }
    assert.equal(writes().length, start + 2);
    put = { body: row(1), status: 0, hold: false };
    await submit();
    await dialog().getByRole("alert").waitFor();
    assert.equal(getCount(), beforeReads);
    assert.equal(
      await dialog().getByLabel("External issue URL").isEnabled(),
      true,
    );
    assert.equal(
      writes().length,
      start + 3,
      "transport failure is not automatically replayed",
    );
    put = { body: row(1), status: 200, hold: true };
    await submit();
    await page.waitForFunction(() => window.__heldAddBodies.length === 1);
    assert.equal(
      await dialog().getByLabel("External issue URL").isDisabled(),
      true,
    );
    for (const name of ["Cancel", "Close Add issue", "Adding…"])
      assert.equal(
        await dialog().getByRole("button", { name, exact: true }).isDisabled(),
        true,
      );
    await page.evaluate(() => {
      const form = document.querySelector(".add-issue-form");
      for (let i = 0; i < 4; i++)
        form.dispatchEvent(
          new Event("submit", { bubbles: true, cancelable: true }),
        );
      document.querySelector('[aria-label="Close Add issue"]').click();
    });
    await page.keyboard.press("Escape");
    await page.mouse.click(2, 2);
    await settle();
    assert.equal(await dialog().isVisible(), true);
    assert.equal(writes().length, start + 4);
    assert.equal(getCount(), beforeReads);
    await release();
    await dialog().waitFor({ state: "hidden" });
    await page
      .getByText("Issue 1 is already added to Test Observer.", { exact: true })
      .waitFor();
  });

  await test("actual session refresh preserves identical profile but A/B/A invalidates held success/error and cannot unlock or close newer pending owner", async () => {
    for (const status of [200, 503]) {
      await open();
      profile = { id: 21, name: "Editor A", is_admin: false, teams: [] };
      await refreshSession();
      await show();
      await dialog().getByLabel("External issue URL").fill("draft kept");
      await refreshSession();
      assert.equal(
        await dialog().getByLabel("External issue URL").inputValue(),
        "draft kept",
      );
      put = {
        status,
        body: status === 200 ? row(1) : { detail: "Obsolete parsed error" },
        hold: true,
      };
      await submit();
      await page.waitForFunction(() => window.__heldAddBodies.length === 1);
      profile = { ...profile, id: 22, name: "Editor B" };
      await refreshSession();
      await dialog().waitFor({ state: "hidden" });
      profile = { ...profile, id: 21, name: "Editor A" };
      await refreshSession();
      await page.locator(".issue-title").first().waitFor();
      await show();
      put = { status: 200, body: row(2), hold: true };
      await submit();
      await page.waitForFunction(() => window.__heldAddBodies.length === 2);
      const before = getCount();
      await page.evaluate(() => window.__heldAddBodies.shift()());
      await settle();
      assert.equal(await dialog().isVisible(), true);
      assert.equal(
        await dialog()
          .getByRole("button", { name: "Adding…", exact: true })
          .isDisabled(),
        true,
      );
      assert.equal(await dialog().getByRole("alert").count(), 0);
      assert.equal(getCount(), before);
      assert.equal(await page.locator(".add-feedback").textContent(), "");
      await release();
      await dialog().waitFor({ state: "hidden" });
      await page
        .getByText("Issue 2 is already added to Test Observer.", {
          exact: true,
        })
        .waitFor();
    }
  });

  await test("Add remains available with failed results/facets and no cached grants; backend 401 is authoritative and recoverable", async () => {
    reads = "error";
    profile = null;
    await page.goto(`${base}/issues`);
    await page.getByText(/Unable to load issues/).waitFor();
    await page.getByText(/Unable to load project options/).waitFor();
    await show();
    put = { status: 401, body: { detail: "Session expired" }, hold: false };
    const before = getCount();
    const writeStart = writes().length;
    await submit();
    await dialog()
      .getByRole("alert")
      .filter({ hasText: "Session expired" })
      .waitFor();
    assert.equal(writes().length, writeStart + 1);
    assert.equal(getCount(), before);
    assert.equal(
      await dialog().getByLabel("External issue URL").isEnabled(),
      true,
    );
    await page.keyboard.press("Escape");
    await dialog().waitFor({ state: "hidden" });
    assert.equal(
      await trigger().evaluate((el) => el === document.activeElement),
      true,
    );
  });

  await test("native Back and real SPA unmount fence late parsed mutation bodies from a new dialog/context", async () => {
    for (const status of [200, 503]) {
      await open();
      await navigate(`${base}/issues?q=second`);
      await page.locator(".issue-title").first().waitFor();
      await show();
      put = {
        status,
        body: status === 200 ? row(1) : { detail: "Obsolete navigation error" },
        hold: true,
      };
      await submit();
      await page.waitForFunction(() => window.__heldAddBodies.length === 1);
      await page.goBack();
      await page.waitForURL((url) => !url.searchParams.has("q"));
      await dialog().waitFor({ state: "hidden" });
      await show();
      const before = getCount();
      await release();
      await settle();
      assert.equal(await dialog().isVisible(), true);
      assert.equal(await dialog().getByRole("alert").count(), 0);
      assert.equal(getCount(), before);
      await dialog()
        .getByRole("button", { name: "Cancel", exact: true })
        .click();
      await dialog().waitFor({ state: "hidden" });
      // Actual route leave/unmount, not just changing a model ownership flag.
      await show();
      await submit();
      await page.waitForFunction(() => window.__heldAddBodies.length === 1);
      await navigate(`${base}/issues/900`);
      await navigate(`${base}/issues`);
      await page.locator(".issue-title").first().waitFor();
      await show();
      await release();
      await settle();
      assert.equal(await dialog().isVisible(), true);
      assert.equal(await dialog().getByRole("alert").count(), 0);
      assert.equal(await page.locator(".add-feedback").textContent(), "");
    }
  });

  await test("real modal small-viewport light/dark long literal error scrolls only its body with reachable header/footer", async () => {
    for (const colorScheme of ["light", "dark"]) {
      await page.emulateMedia({ colorScheme });
      await page.setViewportSize({ width: 800, height: 420 });
      await open();
      await show();
      const literal =
        "<script>not executable</script> " + "long-error ".repeat(900);
      put = { status: 503, body: { detail: literal }, hold: false };
      await submit();
      await dialog().getByRole("alert").waitFor();
      assert.equal(await dialog().locator("script").count(), 0);
      const geometry = await dialog().evaluate((el) => {
        const body = el.querySelector(".add-issue-body");
        const rect = el.getBoundingClientRect();
        const footer = el
          .querySelector(".dialog-content-footer")
          .getBoundingClientRect();
        return {
          top: rect.top,
          bottom: rect.bottom,
          footerBottom: footer.bottom,
          scrollable: body.scrollHeight > body.clientHeight,
          overflow: getComputedStyle(body).overflowY,
          shellOverflow: getComputedStyle(el).overflowY,
        };
      });
      assert.ok(geometry.top >= 0 && geometry.bottom <= 420);
      assert.ok(geometry.footerBottom <= 420);
      assert.equal(geometry.scrollable, true);
      assert.equal(geometry.overflow, "auto");
      assert.equal(geometry.shellOverflow, "hidden");
      await dialog().getByRole("region", { name: "Add issue content" }).focus();
      await page.keyboard.press("End");
      await page.waitForFunction(
        () => document.querySelector(".add-issue-body").scrollTop > 0,
      );
      await dialog()
        .getByRole("button", { name: "Cancel", exact: true })
        .click();
      await dialog().waitFor({ state: "hidden" });
      assert.equal(
        await trigger().evaluate((el) => el === document.activeElement),
        true,
      );
    }
    assert.deepEqual(errors, []);
  });
} finally {
  if (browser) await browser.close();
  await server.close();
}
