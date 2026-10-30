// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0
// Actual Chromium/SvelteKit route and installed controls. ALL API calls/writes
// are intercepted; no live stack, credentials or application test hooks.
/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-argument, @typescript-eslint/no-unsafe-return */
import assert from "node:assert/strict";
import { before, after, test } from "node:test";
import { createServer } from "vite";
import { resolve } from "node:path";

let server, browser, base;
const profile = (id) => ({
  id,
  name: "Synthetic reader",
  teams: [],
  is_admin: false,
});
const row = (id) => ({
  id,
  source: "github",
  project: "A",
  key: String(id),
  title: `Fixture issue ${id}`,
  status: "open",
  url: `https://example.invalid/${id}`,
  labels: [],
  auto_rerun_enabled: false,
  attachment_rules: [],
});
before(async () => {
  server = await createServer({
    cacheDir: resolve(
      process.env.QA_ARTIFACT_DIR ?? "/tmp/opencode/issues-focus",
      "vite-cache",
    ),
    server: { host: "127.0.0.1", port: 0 },
  });
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
const frames = (page) =>
  page.evaluate(
    () =>
      new Promise((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(resolve)),
      ),
  );
async function idle(page) {
  await page.waitForFunction(
    () => !document.querySelector(".page-content[inert], .loading-overlay"),
  );
  await frames(page);
}
async function tabsTo(page, control) {
  for (let count = 0; count < 30; count++) {
    if (await control.evaluate((e) => document.activeElement === e)) return;
    await page.keyboard.press("Tab");
  }
  assert.fail("control must be reachable by actual Tab");
}
async function fixture(t) {
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });
  const page = await context.newPage();
  page.setDefaultTimeout(15000);
  const state = {
    total: 150,
    fail: new Set(),
    hold: /** @type {Promise<void> | null} */ (null),
    holdOffset: /** @type {number | null} */ (null),
    me: profile(21),
    calls: [],
    errors: [],
  };
  page.on("pageerror", (error) => state.errors.push(error.message));
  await context.route("**/wip/families.json", (route) =>
    route.fulfill({
      json: {
        families: [
          {
            name: "configured-focus",
            api_name: "snap",
            stages: [],
            columns: [],
            filters: [],
          },
        ],
      },
    }),
  );
  await context.route("http://localhost:30000/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const headers = {
      "access-control-allow-origin": new URL(base).origin,
      "access-control-allow-credentials": "true",
      "access-control-allow-headers": "content-type,x-csrf-token",
      "access-control-allow-methods": "GET,OPTIONS",
    };
    if (request.method() === "OPTIONS")
      return route.fulfill({ status: 204, headers });
    state.calls.push({
      method: request.method(),
      path: url.pathname,
      params: [...url.searchParams],
    });
    const reply = (json, status = 200) =>
      route.fulfill({ headers, status, json });
    if (request.method() !== "GET")
      return reply({ detail: "Unexpected mocked write rejected" }, 405);
    if (url.pathname === "/v1/users/me") return reply(state.me);
    if (url.pathname === "/v1/issues") {
      const offset = Number(url.searchParams.get("offset"));
      if (state.holdOffset === offset && state.hold) await state.hold;
      if (state.fail.has(offset))
        return reply({ detail: "Synthetic issue read failure" }, 503);
      return reply({
        issues: Array.from(
          { length: Math.min(50, state.total - offset) },
          (_, index) => row(offset + index + 1),
        ),
        count: state.total,
        offset,
        limit: 50,
      });
    }
    if (/^\/v1\/issues\/\d+$/.test(url.pathname))
      return reply(row(Number(url.pathname.split("/").at(-1))));
    if (url.pathname === "/v1/test-results/search-page")
      return reply({ rows: [], count: 0, limit: 50, offset: 0 });
    if (url.pathname === "/v1/notifications/unread-count")
      return reply({ count: 0 });
    return reply({ detail: "Unexpected mocked endpoint" }, 404);
  });
  t.after(async () => {
    assert.deepEqual(state.errors, []);
    assert.ok(state.calls.every((call) => call.method === "GET"));
    await context.close();
  });
  const hold = (offset) => {
    let release;
    state.holdOffset = offset;
    state.hold = new Promise((resolve) => (release = resolve));
    return () => {
      state.holdOffset = null;
      state.hold = null;
      release();
    };
  };
  const goto = (path) =>
    page.evaluate(async (path) => {
      const resource = performance
        .getEntriesByType("resource")
        .find((entry) =>
          entry.name.includes("/runtime/app/navigation/index.js"),
        );
      const navigation = await import(resource.name);
      await navigation.goto(path, { reset: false });
    }, `${base}${path}`);
  const refresh = () =>
    page.evaluate(async () => {
      const { userStore } = await import("/wip/src/lib/stores/user.svelte.ts");
      await userStore.refresh(fetch);
    });
  return { page, state, hold, goto, refresh };
}
const focused = (control) =>
  control.evaluate((e) => document.activeElement === e);

void test("source/status/family retain actual Tab/Space focus and a second Space reverses each filter; Search Enter retains input/button in light/dark", async (t) => {
  const { page } = await fixture(t);
  for (const [colorScheme, width, height] of [
    ["light", 1440, 900],
    ["dark", 800, 420],
  ]) {
    await page.emulateMedia({ colorScheme });
    await page.setViewportSize({ width, height });
    for (const [name, key] of [
      ["GITHUB", "source"],
      ["Closed", "status"],
      ["Configured-focus", "family"],
    ]) {
      await page.goto(`${base}/issues`);
      await page.locator(".issue-title").first().waitFor();
      await page.getByRole("searchbox", { name: "Search issues" }).focus();
      const control = page.getByRole("checkbox", { name, exact: true });
      await tabsTo(page, control);
      await page.keyboard.press("Space");
      await page.waitForURL((url) => url.searchParams.has(key));
      await idle(page);
      assert.equal(await control.isChecked(), true);
      assert.equal(
        await focused(control),
        true,
        `${name} survives its own navigation`,
      );
      const selected = page.url();
      await page.keyboard.press("Space");
      await page.waitForURL((url) => url.href !== selected);
      await idle(page);
      assert.equal(await control.isChecked(), false);
      assert.equal(
        await focused(control),
        true,
        `${name} remains operable with Space`,
      );
    }
    await page.goto(`${base}/issues`);
    const input = page.getByRole("searchbox", { name: "Search issues" });
    await input.fill("explicit query");
    await page.keyboard.press("Enter");
    await page.waitForURL(
      (url) => url.searchParams.get("q") === "explicit query",
    );
    await idle(page);
    assert.equal(await focused(input), true);
    const button = page.getByRole("button", { name: "Search", exact: true });
    await tabsTo(page, button);
    await page.keyboard.press("Enter");
    await idle(page);
    assert.equal(
      await focused(button),
      true,
      "explicit Search button also survives unchanged-query submit",
    );
  }
});

void test("held result paging restores the surviving button; failed/exhausted pages and successful retry focus the current result region", async (t) => {
  const { page, state, hold } = await fixture(t);
  await page.goto(`${base}/issues`);
  const more = page.getByRole("button", {
    name: "Load more issues (50 at a time)",
    exact: true,
  });
  await more.waitFor();
  await page.locator(".issue-title").last().focus();
  await tabsTo(page, more);
  let release = hold(50);
  await page.keyboard.press("Space");
  const loading = page.getByRole("button", {
    name: "Loading more…",
    exact: true,
  });
  await loading.waitFor();
  assert.equal(await loading.isDisabled(), true);
  await page.keyboard.press("Space");
  release();
  await page.locator(".issue-title").nth(99).waitFor();
  await frames(page);
  assert.equal(
    await focused(more),
    true,
    "a disabled but surviving page trigger returns focus",
  );
  state.fail.add(100);
  release = hold(100);
  await page.keyboard.press("Enter");
  await loading.waitFor();
  release();
  const retry = page.getByRole("button", { name: "Try again", exact: true });
  await retry.waitFor();
  const region = page.locator("section.issue-results");
  await frames(page);
  assert.equal(
    await focused(region),
    true,
    "removed Load more has a current result fallback",
  );
  await tabsTo(page, retry);
  state.fail.clear();
  release = hold(100);
  await page.keyboard.press("Enter");
  await retry.waitFor({ state: "hidden" });
  release();
  await page.locator(".issue-title").nth(149).waitFor();
  await frames(page);
  assert.equal(
    await focused(region),
    true,
    "removed successful retry returns to the current results",
  );
  assert.equal(await more.count(), 0);
  // Direct successful exhaustion removes a paging invoker too, without an
  // intervening error/retry branch. Initial retry takes a different DOM branch.
  state.total = 100;
  await page.goto(`${base}/issues`);
  await more.focus();
  release = hold(50);
  await page.keyboard.press("Space");
  await loading.waitFor();
  release();
  await page.locator(".issue-title").nth(99).waitFor();
  await frames(page);
  assert.equal(await focused(region), true);
  state.fail.add(0);
  await page.goto(`${base}/issues`);
  await retry.focus();
  state.fail.clear();
  release = hold(0);
  await page.keyboard.press("Enter");
  await page.getByText("Loading issues…", { exact: true }).waitFor();
  release();
  await page.locator(".issue-title").first().waitFor();
  await frames(page);
  assert.equal(
    await focused(region),
    true,
    "initial retry also has a persistent current-owner destination",
  );
});

void test("held project discovery restores surviving paging and uses project search after error/retry/exhaustion", async (t) => {
  const { page, state, hold } = await fixture(t);
  await page.goto(`${base}/issues`);
  const search = page.getByRole("textbox", { name: "Search project options" });
  const more = page.getByRole("button", {
    name: "Load more project options",
    exact: true,
  });
  await more.waitFor();
  await search.focus();
  await tabsTo(page, more);
  let release = hold(50);
  await page.keyboard.press("Space");
  await page
    .getByRole("button", { name: "Loading project options…", exact: true })
    .waitFor();
  release();
  await more.waitFor();
  await frames(page);
  assert.equal(await focused(more), true);
  state.fail.add(100);
  release = hold(100);
  await page.keyboard.press("Enter");
  await page
    .getByRole("button", { name: "Loading project options…", exact: true })
    .waitFor();
  release();
  const retry = page.getByRole("button", {
    name: "Retry project options",
    exact: true,
  });
  await retry.waitFor();
  await frames(page);
  assert.equal(await focused(search), true);
  await tabsTo(page, retry);
  state.fail.clear();
  release = hold(100);
  await page.keyboard.press("Enter");
  await retry.waitFor({ state: "hidden" });
  release();
  await page
    .getByText("All 150 issue rows in this discovery have been checked.", {
      exact: false,
    })
    .waitFor();
  await frames(page);
  assert.equal(await focused(search), true);
});

void test("URL navigation never revives source focus after deliberate other-control focus later blurred by native inert", async (t) => {
  const { page } = await fixture(t);
  for (let trial = 0; trial < 3; trial++) {
    await page.goto(`${base}/issues`);
    const source = page.getByRole("checkbox", { name: "GITHUB", exact: true });
    await source.focus();
    const witness = await source.evaluate((input) => {
      window.__listFocusEvents = [];
      window.__listInertObserved = false;
      const content = document.querySelector(".page-content");
      new MutationObserver(() => {
        if (content.hasAttribute("inert")) window.__listInertObserved = true;
      }).observe(content, { attributes: true, attributeFilter: ["inert"] });
      document.addEventListener(
        "focusin",
        (event) =>
          window.__listFocusEvents.push(
            event.target === input ? "source" : event.target.id,
          ),
        true,
      );
      input.checked = true;
      input.dispatchEvent(new Event("change", { bubbles: true }));
      const other = document.querySelector("#issue-search");
      other.focus();
      return document.activeElement === other;
    });
    assert.equal(
      witness,
      true,
      "second destination actually receives native focus before inert",
    );
    await page.waitForURL((url) => url.searchParams.has("source"));
    await idle(page);
    assert.equal(await focused(source), false);
    assert.equal(
      await page.evaluate(() => window.__listInertObserved),
      true,
      "the real shell actually became inert after the intervening focus",
    );
    assert.equal(
      await page.evaluate(() => window.__listFocusEvents.includes("source")),
      false,
      "old intent is never restored, even after inert blurs the destination",
    );
  }
});

void test("same-query held paging remembers other-control intent after that destination blurs to body", async (t) => {
  const { page, hold } = await fixture(t);
  await page.goto(`${base}/issues`);
  const more = page.getByRole("button", {
    name: "Load more issues (50 at a time)",
    exact: true,
  });
  await more.focus();
  const release = hold(50);
  await page.keyboard.press("Space");
  await page
    .getByRole("button", { name: "Loading more…", exact: true })
    .waitFor();
  const input = page.getByRole("searchbox", { name: "Search issues" });
  await input.focus();
  assert.equal(await focused(input), true);
  await input.blur();
  release();
  await page.locator(".issue-title").nth(99).waitFor();
  await frames(page);
  assert.equal(
    await more.evaluate(() => document.activeElement === document.body),
    true,
  );
});

void test("a superseding Search intent owns focus after an old held page completes", async (t) => {
  const { page, hold } = await fixture(t);
  await page.goto(`${base}/issues`);
  const more = page.getByRole("button", {
    name: "Load more issues (50 at a time)",
    exact: true,
  });
  await more.focus();
  const release = hold(50);
  await page.keyboard.press("Space");
  await page
    .getByRole("button", { name: "Loading more…", exact: true })
    .waitFor();
  const input = page.getByRole("searchbox", { name: "Search issues" });
  await input.fill("new owner");
  await page.keyboard.press("Enter");
  await page.waitForURL((url) => url.searchParams.get("q") === "new owner");
  await idle(page);
  assert.equal(await focused(input), true);
  release();
  await frames(page);
  assert.equal(await focused(input), true);
  assert.equal(await page.locator(".issue-title").count(), 50);
});

void test("query/navigation A/B/A, session A/B/A, hidden filters and unmount invalidate held read focus without stealing", async (t) => {
  const { page, state, hold, goto, refresh } = await fixture(t);
  for (const variant of ["query-ABA", "session-ABA", "hidden", "unmount"]) {
    await page.goto(`${base}/issues`);
    const facet = variant === "hidden";
    const more = page.getByRole("button", {
      name: facet
        ? "Load more project options"
        : "Load more issues (50 at a time)",
      exact: true,
    });
    await more.focus();
    const release = hold(50);
    await page.keyboard.press("Space");
    await page
      .getByRole("button", {
        name: facet ? "Loading project options…" : "Loading more…",
        exact: true,
      })
      .waitFor();
    if (variant === "query-ABA") {
      await goto("/issues?q=B");
      await idle(page);
      await goto("/issues");
      await idle(page);
    } else if (variant === "session-ABA") {
      state.me = profile(22);
      await refresh();
      await frames(page);
      state.me = profile(21);
      await refresh();
      await page.locator(".issue-title").first().waitFor();
      await frames(page);
    } else if (variant === "hidden") {
      await page
        .getByRole("button", { name: "Hide filters", exact: true })
        .evaluate((button) => button.click());
    } else {
      await goto("/issues/80");
      await page
        .getByRole("heading", { name: "Fixture issue 80", exact: true })
        .waitFor();
      await idle(page);
    }
    const before = await page.evaluate(() => ({
      tag: document.activeElement.tagName,
      id: document.activeElement.id,
    }));
    release();
    await frames(page);
    assert.deepEqual(
      await page.evaluate(() => ({
        tag: document.activeElement.tagName,
        id: document.activeElement.id,
      })),
      before,
      variant,
    );
  }
});
