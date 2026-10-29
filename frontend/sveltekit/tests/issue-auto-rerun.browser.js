// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

// Native Pragma Switch/route regressions. Every API request is intercepted;
// writes affect only per-test memory, never any shared backend/database.
/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-argument, @typescript-eslint/no-unsafe-return */
import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { createServer } from "vite";

let server, browser, base;
const user = {
  id: 21,
  name: "Ordinary issue editor",
  is_admin: false,
  teams: [{ permissions: ["change_issue", "change_auto_rerun"] }],
};
const issue = (id, enabled = false) => ({
  id,
  source: "github",
  project: "canonical/test-observer",
  key: String(id),
  title: `Issue ${id}`,
  status: "open",
  url: `https://github.com/canonical/test-observer/issues/${id}`,
  labels: [],
  auto_rerun_enabled: enabled,
  attachment_rules: [],
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
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const state = {
    me: structuredClone(user),
    values: { 73: false, 80: false },
    patches: [],
    patch:
      /** @type {null | ((request: {id: number; body: {auto_rerun_enabled: boolean}; respond: (body: unknown, status?: number) => Promise<void>}) => Promise<void>)} */ (
        null
      ),
    resultStatus: 403,
  };
  await page.route("http://localhost:30000/**", (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const headers = {
      "access-control-allow-origin":
        request.headers().origin ?? new URL(base).origin,
      "access-control-allow-credentials": "true",
      "access-control-allow-headers": "content-type,x-csrf-token",
      "access-control-allow-methods": "GET,PATCH,OPTIONS",
    };
    const respond = (body, status = 200) =>
      route.fulfill({
        status,
        headers,
        contentType: "application/json",
        body: JSON.stringify(body),
      });
    if (request.method() === "OPTIONS")
      return route.fulfill({ status: 204, headers });
    if (path === "/v1/users/me") return respond(state.me);
    if (path === "/v1/test-results/search-page")
      return respond(
        { detail: "No result access in this fixture" },
        state.resultStatus,
      );
    const id = Number(/^\/v1\/issues\/(\d+)$/.exec(path)?.[1]);
    if (id && request.method() === "GET")
      return respond(issue(id, state.values[id]));
    if (id && request.method() === "PATCH") {
      const body = request.postDataJSON();
      assert.deepEqual(Object.keys(body), ["auto_rerun_enabled"]);
      assert.equal(typeof body.auto_rerun_enabled, "boolean");
      state.patches.push({ id, body });
      if (state.patch) return state.patch({ id, body, respond });
      state.values[id] = body.auto_rerun_enabled;
      return respond(issue(id, state.values[id]));
    }
    return respond({ detail: `Unmocked ${path}` }, 404);
  });
  await page.goto(`${base}/issues/73`);
  await page
    .getByRole("switch", { name: "Auto-rerun on new matches" })
    .waitFor();
  await page.evaluate((base) => {
    for (const id of [73, 80]) {
      const link = document.createElement("a");
      link.href = `${base}/issues/${id}`;
      link.id = `qa-auto-${id}`;
      link.textContent = `QA navigate ${id}`;
      document.body.append(link);
    }
    // Hold parsed bodies, not transport: guards must survive successful parsing
    // even when AbortSignal would be too late or ignored.
    const fetch = window.fetch.bind(window);
    window.__autoHold = null;
    window.__autoReleases = [];
    window.fetch = async (input, options) => {
      const response = await fetch(input, options);
      const hold = window.__autoHold;
      if (
        hold &&
        (input instanceof Request ? input.url : input.toString()).endsWith(
          hold.path,
        ) &&
        (options?.method ?? "GET") === hold.method
      ) {
        const read = response.json.bind(response);
        response.json = async () => {
          const value = await read();
          await new Promise((resolve) => window.__autoReleases.push(resolve));
          return value;
        };
      }
      return response;
    };
  }, base);
  const control = () =>
    page.getByRole("switch", { name: "Auto-rerun on new matches" });
  const navigate = async (id) => {
    await page.locator(`#qa-auto-${id}`).click();
    await page
      .getByRole("heading", { name: `Issue ${id}`, exact: true })
      .waitFor();
  };
  const refresh = () =>
    page.evaluate(async () => {
      const { userStore } = await import("/wip/src/lib/stores/user.svelte.ts");
      await userStore.refresh(fetch);
    });
  const release = () =>
    page.evaluate(() => {
      window.__autoHold = null;
      window.__autoReleases.splice(0).forEach((release) => release());
    });
  return {
    page,
    state,
    control,
    navigate,
    refresh,
    release,
    close: async () => {
      assert.deepEqual(errors, []);
      await context.close();
    },
  };
}

void test("auto-rerun spacing and Switch track retain installed token sizes in the default layout", async (t) => {
  const f = await fixture();
  try {
    for (const [width, height, colorScheme] of [
      [1440, 900, "light"],
      [1440, 900, "dark"],
      [800, 600, "light"],
      [800, 600, "dark"],
      [390, 844, "dark"],
      [390, 844, "light"],
    ]) {
      await f.page.setViewportSize({ width, height });
      await f.page.emulateMedia({ colorScheme });
      await f.page.evaluate((theme) => {
        document.documentElement.classList.remove("light", "dark");
        document.documentElement.classList.add(theme);
      }, colorScheme);
      assert.equal(
        await f.page
          .getByRole("button", { name: "Collapse navigation", exact: true })
          .count(),
        1,
        "geometry must be checked with the default expanded navigation",
      );
      const { spacing, track } = await f.page
        .getByRole("region", { name: "Automatic reruns", exact: true })
        .evaluate((section) => {
          const label = section.querySelector("label");
          const probe = document.createElement("span");
          section.append(probe);
          const measure = (element, property, token) => {
            probe.style.marginBlockStart = `var(${token})`;
            return {
              property,
              token,
              definition: getComputedStyle(section)
                .getPropertyValue(token)
                .trim(),
              expected: getComputedStyle(probe).marginBlockStart,
              actual: getComputedStyle(element).getPropertyValue(property),
            };
          };
          const values = [
            measure(
              section,
              "margin-block-end",
              "--lp-dimension-spacing-block-xxl",
            ),
            measure(label, "column-gap", "--lp-dimension-spacing-inline-s"),
            ...[...section.querySelectorAll("p")].flatMap((paragraph) =>
              ["margin-block-start", "margin-block-end"].map((property) =>
                measure(paragraph, property, "--lp-dimension-spacing-block-s"),
              ),
            ),
          ];
          const control = section.querySelector('input[role="switch"]');
          // Resolve the installed track size without copying its dimensions or
          // applying a browser-only sizing workaround to the actual input.
          probe.style.cssText =
            "position: fixed; display: block; width: var(--lp-dimension-size-l);";
          const track = {
            definition: getComputedStyle(control)
              .getPropertyValue("--lp-dimension-size-l")
              .trim(),
            expectedWidth: probe.getBoundingClientRect().width,
            actualWidth: control.getBoundingClientRect().width,
          };
          probe.remove();
          return { spacing: values, track };
        });
      t.diagnostic(
        JSON.stringify({ width, height, colorScheme, spacing, track }),
      );
      for (const value of spacing) {
        assert.ok(
          value.definition,
          `${value.token} must be defined at ${width}px`,
        );
        assert.equal(
          value.actual,
          value.expected,
          `${value.property} must resolve ${value.token} at ${width}px`,
        );
        assert.ok(
          Number.parseFloat(value.actual) > 0,
          `${value.property} must render positive spacing at ${width}px`,
        );
      }
      assert.ok(
        track.definition,
        "the installed Switch size token must be defined",
      );
      assert.ok(
        track.expectedWidth > 0,
        "the installed Switch size must resolve to a positive width",
      );
      assert.equal(
        track.actualWidth,
        track.expectedWidth,
        `Switch track must retain its installed token width at ${width}px/${colorScheme}`,
      );
    }
    assert.equal(
      f.state.patches.length,
      0,
      "spacing checks do not toggle the setting",
    );
  } finally {
    await f.close();
  }
});

void test("native labelled Switch retains checked/aria state on pointer and Space pending/failure/retry independently of denied results", async () => {
  const f = await fixture();
  try {
    await f.page
      .getByText(/don't have permission to view these test results/)
      .waitFor();
    let finish;
    f.state.patch = ({ respond }) =>
      new Promise((resolve) => {
        finish = async () => {
          await respond({ detail: "Mock rejected" }, 403);
          resolve();
        };
      });
    await f.control().click();
    await f.page
      .getByText("Saving… Showing the last confirmed setting.", { exact: true })
      .waitFor();
    assert.equal(await f.control().isChecked(), false);
    assert.equal(await f.control().getAttribute("aria-checked"), "false");
    assert.equal(await f.control().isDisabled(), true);
    assert.equal(f.state.patches.length, 1);
    await finish();
    await f.page
      .getByRole("alert")
      .filter({ hasText: "Mock rejected" })
      .waitFor();
    assert.equal(await f.control().isChecked(), false);
    f.state.patch = null;
    await f.control().focus();
    await f.page.keyboard.press("Space");
    await f.page.getByText("Confirmed: On.", { exact: true }).waitFor();
    assert.equal(await f.control().isChecked(), true);
    assert.equal(await f.control().getAttribute("aria-checked"), "true");
    assert.equal(f.state.patches.length, 2);
    f.state.me = { ...user, teams: [{ permissions: ["change_issue"] }] };
    await f.control().click();
    await f.page
      .getByRole("heading", { name: "Issue 73", exact: true })
      .waitFor();
    assert.equal(
      f.state.patches.length,
      2,
      "freshly revoked second grant blocks the write",
    );
    await f.control().click();
    await f.page
      .getByRole("alert")
      .filter({ hasText: "change_auto_rerun" })
      .waitFor();
    assert.equal(f.state.patches.length, 2);
    await f.page.setViewportSize({ width: 800, height: 600 });
    await f.page.emulateMedia({ colorScheme: "dark" });
    assert.ok(await f.control().isVisible());
  } finally {
    await f.close();
  }
});

void test("late A PATCH cannot change B; A/B/A reconciles both fresh GET and GET begun before completion", async () => {
  const f = await fixture();
  try {
    let finish;
    f.state.patch = ({ id, body, respond }) =>
      new Promise((resolve) => {
        finish = async () => {
          f.state.values[id] = body.auto_rerun_enabled;
          await respond(issue(id, f.state.values[id]));
          resolve();
        };
      });
    await f.control().click();
    await f.page.getByText(/Saving…/).waitFor();
    await f.navigate(80);
    await finish();
    assert.equal(await f.control().isChecked(), false, "B stays Off");
    await f.navigate(73);
    await f.page.getByText("Confirmed: On.", { exact: true }).waitFor();
    await f.control().click();
    await f.page.getByText(/Saving…/).waitFor();
    await f.navigate(80);
    await f.page.evaluate(
      () => (window.__autoHold = { path: "/v1/issues/73", method: "GET" }),
    );
    await f.page.locator("#qa-auto-73").click();
    await f.page.waitForFunction(() => window.__autoReleases.length === 1);
    await finish();
    await f.release();
    await f.page.getByText("Confirmed: Off.", { exact: true }).waitFor();
    assert.equal(
      await f.control().isChecked(),
      false,
      "old parsed GET cannot revert confirmed PATCH",
    );
  } finally {
    await f.close();
  }
});

void test("returning before PATCH settles keeps A locked and receives its confirmation", async () => {
  const f = await fixture();
  try {
    let finish;
    f.state.patch = ({ id, respond }) =>
      new Promise((resolve) => {
        finish = async () => {
          await respond(issue(id, true));
          resolve();
        };
      });
    await f.control().click();
    await f.page.getByText(/Saving…/).waitFor();
    await f.navigate(80);
    await f.navigate(73);
    assert.equal(await f.control().isDisabled(), true);
    assert.equal(await f.control().isChecked(), false);
    await finish();
    await f.page.getByText("Confirmed: On.", { exact: true }).waitFor();
    assert.equal(await f.control().isChecked(), true);
  } finally {
    await f.close();
  }
});

void test("session changes discard held PATCH confirmations and late parsed errors across navigation", async () => {
  const f = await fixture();
  try {
    await f.page.evaluate(
      () => (window.__autoHold = { path: "/v1/issues/73", method: "PATCH" }),
    );
    f.state.patch = ({ id, respond }) => respond(issue(id, true));
    await f.control().click();
    await f.page.waitForFunction(() => window.__autoReleases.length === 1);
    f.state.me = { ...user, id: 22 };
    await f.refresh();
    await f.page.getByText("Confirmed: Off.", { exact: true }).waitFor();
    f.state.me = structuredClone(user);
    await f.refresh();
    await f.page.getByText("Confirmed: Off.", { exact: true }).waitFor();
    await f.release();
    assert.equal(await f.control().isChecked(), false);
    await f.page.evaluate(
      () => (window.__autoHold = { path: "/v1/issues/73", method: "PATCH" }),
    );
    f.state.patch = ({ respond }) =>
      respond({ detail: "Obsolete parsed denial" }, 403);
    await f.control().click();
    await f.page.waitForFunction(() => window.__autoReleases.length === 1);
    await f.navigate(80);
    await f.release();
    assert.equal(await f.page.getByText(/Obsolete parsed denial/).count(), 0);
    assert.equal(await f.control().isChecked(), false);
  } finally {
    await f.close();
  }
});
