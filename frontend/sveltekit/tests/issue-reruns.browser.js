// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

// Opt-in Chromium integration. ALL API calls, including writes, are intercepted.
// External Playwright only; no live/shared data or credentials are used.
/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-argument, @typescript-eslint/no-unsafe-return */
import assert from "node:assert/strict";
import { before, after, test } from "node:test";
import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";
import { createServer } from "vite";

const artifacts = resolve(
  process.env.QA_ARTIFACT_DIR ?? "/tmp/opencode/issue-reruns-browser",
);
let server, browser, base;
const user = {
  id: 21,
  name: "Ordinary rerun editor",
  is_admin: false,
  teams: [{ permissions: ["change_rerun", "change_rerun_bulk"] }],
};
const issue = (id) => ({
  id,
  source: "github",
  project: "qa",
  key: String(id),
  title: `Issue ${id}`,
  status: "open",
  url: `https://example.invalid/${id}`,
  labels: [],
  auto_rerun_enabled: false,
  attachment_rules: [],
});
/** @param {number} index @param {number} id */
const row = (index, id) => ({
  test_result: {
    id: id * 1000 + index,
    name: "case",
    category: "smoke",
    status: "FAILED",
    created_at: "2026-10-25T12:00:00Z",
    template_id: "template",
    issues: [{ id, key: String(id), title: `Issue ${id}` }],
  },
  test_execution: {
    id: 7000 + index,
    status: "FAILED",
    environment: { name: "lab" },
    test_plan: "smoke",
    rerun_is_requested: false,
    execution_is_latest: true,
    execution_metadata: [],
  },
  artefact: {
    id: 42,
    name: "applied artefact",
    version: "1",
    track: "stable",
    family: "generic",
    stage: "",
    archived: false,
    reviewers: [],
  },
  artefact_build: { architecture: "amd64" },
});
before(async () => {
  await mkdir(artifacts, { recursive: true });
  server = await createServer({
    cacheDir: resolve(artifacts, "vite-cache"),
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

async function fixture() {
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const state = {
    me: structuredClone(user),
    count: 125,
    previewStatus: 200,
    writeStatus: 200,
    calls: [],
    writes: [],
    write:
      /** @type {null | ((request: {call: unknown; respond: (body: unknown, status?: number) => Promise<void>; route: {abort(error: string): Promise<void>}}) => Promise<void> | void)} */ (
        null
      ),
  };
  await page.route("**/wip/families.json", (route) =>
    route.fulfill({
      json: {
        families: [
          {
            name: "configured-route",
            api_name: "generic",
            stages: [],
            filters: [],
            columns: [],
          },
        ],
      },
    }),
  );
  await page.route("http://localhost:30000/**", (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const method = request.method();
    const headers = {
      "access-control-allow-origin":
        request.headers().origin ?? new URL(base).origin,
      "access-control-allow-credentials": "true",
      "access-control-allow-headers": "content-type,x-csrf-token",
      "access-control-allow-methods": "GET,POST,DELETE,OPTIONS",
    };
    if (method === "OPTIONS") return route.fulfill({ status: 204, headers });
    state.calls.push({
      path: url.pathname,
      params: [...url.searchParams],
      method,
    });
    const respond = (body, status = 200) =>
      route.fulfill({ status, headers, json: body });
    if (url.pathname === "/v1/users/me") return respond(state.me);
    const id = Number(/^\/v1\/issues\/(\d+)$/.exec(url.pathname)?.[1]);
    if (id && method === "GET") return respond(issue(id));
    if (
      url.pathname === "/v1/test-executions/reruns" &&
      ["POST", "DELETE"].includes(method)
    ) {
      const call = {
        method,
        params: [...url.searchParams],
        body: request.postDataJSON(),
      };
      state.writes.push(call);
      return state.write
        ? state.write({ call, respond, route })
        : respond({ detail: "Mocked write response" }, state.writeStatus);
    }
    assert.equal(
      method,
      "GET",
      `Unexpected mutation ${method} ${url.pathname}`,
    );
    if (url.pathname === "/v1/test-results") {
      assert.deepEqual(url.searchParams.getAll("issues"), ["73"]);
      return respond(
        state.previewStatus === 200
          ? { count: state.count }
          : { detail: "Mocked preview failure" },
        state.previewStatus,
      );
    }
    if (url.pathname === "/v1/test-results/search-page") {
      const pinned = Number(url.searchParams.get("issues"));
      assert.deepEqual(url.searchParams.getAll("issues"), [String(pinned)]);
      const offset = Number(url.searchParams.get("offset"));
      const limit = Number(url.searchParams.get("limit"));
      return respond({
        count: url.searchParams.get("include_count") === "false" ? null : 625,
        offset,
        limit,
        rows: Array.from({ length: Math.min(limit, 625 - offset) }, (_, n) =>
          row(offset + n, pinned),
        ),
      });
    }
    if (url.pathname === "/v1/artefacts/search")
      return respond({ artefacts: [] });
    if (url.pathname === "/v1/environments")
      return respond({ environments: [] });
    if (url.pathname === "/v1/test-cases") return respond({ test_cases: [] });
    return respond({ detail: `Unmocked ${url.pathname}` }, 404);
  });
  await page.goto(`${base}/issues/73`);
  await page
    .getByText("625 matching test results on the server.", { exact: false })
    .waitFor();
  await page.evaluate(() => {
    // Hold parsed bodies after a real mocked HTTP response; aborting transport
    // cannot substitute for ownership checks at the subsequent await boundary.
    const original = window.fetch.bind(window);
    window.__rerunHold = null;
    window.__rerunReleases = [];
    window.fetch = async (input, options) => {
      const response = await original(input, options);
      const hold = window.__rerunHold;
      const url = new URL(
        input instanceof Request ? input.url : input.toString(),
      );
      if (
        url.pathname === hold?.path &&
        (options?.method ?? "GET") === hold.method
      ) {
        const read = response.json.bind(response);
        response.json = async () => {
          const value = await read();
          await new Promise((resolve) => window.__rerunReleases.push(resolve));
          return value;
        };
      }
      return response;
    };
  });
  const open = async (action = "Create") => {
    await page
      .locator(".rerun-actions")
      .getByRole("button", { name: `${action} rerun requests`, exact: true })
      .click();
    const review = page.locator("dialog.bulk-rerun-review[open]");
    await review
      .getByRole("heading", { name: `${action} Rerun Requests`, exact: true })
      .waitFor();
    return review;
  };
  const refresh = () =>
    page.evaluate(async () => {
      const { userStore } = await import("/wip/src/lib/stores/user.svelte.ts");
      await userStore.refresh(fetch);
    });
  const release = () =>
    page.evaluate(() => {
      window.__rerunHold = null;
      window.__rerunReleases.splice(0).forEach((release) => release());
    });
  return {
    page,
    state,
    open,
    refresh,
    release,
    close: async () => {
      assert.deepEqual(errors, []);
      await context.close();
    },
  };
}
const submit = (review, action = "Create") =>
  review.getByRole("button", { name: `${action} rerun requests`, exact: true });
const ack = (review) =>
  review.getByRole("checkbox", { name: /I have reviewed the scope/ });
const previews = (state) =>
  state.calls.filter((call) => call.path === "/v1/test-results");
async function waitEnabled(locator) {
  await locator
    .page()
    .waitForFunction(
      (button) => !button.disabled,
      await locator.elementHandle(),
    );
}

void test("native issue create uses all applied filters beyond loaded rows, not drafts; priority/options reset >50 acknowledgment and payload equals preview", async () => {
  const f = await fixture();
  try {
    const { page, state } = f;
    await page.getByRole("button", { name: /Optional filters/ }).click();
    const artefact = page.getByRole("region", {
      name: "Artefact filter",
      exact: true,
    });
    await artefact.locator("input").fill("applied artefact");
    await artefact
      .getByRole("button", { name: "Add exact value", exact: true })
      .click();
    await page
      .locator('input[name="until_date"]')
      .fill("2026-10-25T12:00:00.123456Z");
    await page
      .getByRole("button", { name: "Apply filters", exact: true })
      .click();
    await page.waitForFunction(
      () => !document.querySelector(".rerun-actions button").disabled,
    );
    await artefact.locator("input").fill("draft only");
    await artefact
      .getByRole("button", { name: "Add exact value", exact: true })
      .click();
    const review = await f.open();
    await review.getByText(/Matches 125 test results/).waitFor();
    assert.equal(await submit(review).isEnabled(), false);
    assert.equal((await review.textContent()).includes("draft only"), false);
    await ack(review).check();
    await review
      .getByRole("textbox", { name: "Priority", exact: true })
      .fill("42");
    assert.equal(await submit(review).isEnabled(), false);
    await review.getByText(/Matches 125 test results/).waitFor();
    await ack(review).check();
    await review
      .getByRole("checkbox", {
        name: "Only latest test executions",
        exact: true,
      })
      .uncheck();
    await review.getByText(/Matches 125 test results/).waitFor();
    assert.equal(await ack(review).isChecked(), false);
    await ack(review).check();
    await waitEnabled(submit(review));
    await submit(review).click();
    await page.getByText(/Create rerun request completed/).waitFor();
    assert.equal(state.writes.length, 1);
    const write = state.writes[0];
    assert.equal(write.method, "POST");
    assert.deepEqual(write.params, [["silent", "true"]]);
    assert.deepEqual(write.body, {
      priority: 42,
      test_results_filters: {
        issues: [73],
        artefacts: ["applied artefact"],
        until_date: "2026-10-25T12:00:00.123456Z",
        rerun_is_requested: false,
        artefact_is_archived: false,
      },
    });
    const preview = new URLSearchParams(previews(state).at(-1).params);
    for (const [key, value] of Object.entries(write.body.test_results_filters))
      assert.deepEqual(
        preview.getAll(key),
        (Array.isArray(value) ? value : [value]).map(String),
      );
    assert.equal(preview.get("limit"), "0");
    assert.ok(
      state.calls.filter(
        (call) =>
          call.path.endsWith("search-page") &&
          new URLSearchParams(call.params).get("offset") === "0",
      ).length >= 3,
    );
    assert.equal(
      await page.getByRole("link", { name: "View matching results" }).count(),
      0,
    );
  } finally {
    await f.close();
  }
});

void test("native deletion defaults exclude creation guards and submits only the correct issue query", async () => {
  const f = await fixture();
  try {
    const review = await f.open("Delete");
    await review.getByText(/Matches 125 test results/).waitFor();
    assert.equal(
      await review
        .getByRole("checkbox", {
          name: "Only latest test executions",
          exact: true,
        })
        .isChecked(),
      false,
    );
    assert.equal(
      await review
        .getByRole("checkbox", {
          name: "Exclude archived artefacts",
          exact: true,
        })
        .isChecked(),
      false,
    );
    assert.equal(
      await review.getByRole("textbox", { name: "Priority" }).count(),
      0,
    );
    await ack(review).check();
    await submit(review, "Delete").click();
    await f.page.getByText(/Delete rerun request completed/).waitFor();
    assert.deepEqual(f.state.writes, [
      {
        method: "DELETE",
        params: [],
        body: {
          test_results_filters: { issues: [73], rerun_is_requested: true },
        },
      },
    ]);
  } finally {
    await f.close();
  }
});

void test("native zero and failed previews cannot write; a rejected write is terminal with an explicit refresh path", async () => {
  const f = await fixture();
  try {
    f.state.count = 0;
    let review = await f.open();
    await review.getByText(/Matches 0 test results/).waitFor();
    assert.equal(await submit(review).isEnabled(), false);
    await review.getByRole("button", { name: "Cancel", exact: true }).click();
    f.state.previewStatus = 403;
    review = await f.open();
    await review.getByText(/Count preview failed/).waitFor();
    assert.equal(await submit(review).isEnabled(), false);
    await review
      .getByRole("button", { name: "Close and refresh results", exact: true })
      .click();
    f.state.previewStatus = 200;
    f.state.count = 50;
    f.state.writeStatus = 403;
    review = await f.open();
    await waitEnabled(submit(review));
    await submit(review).click();
    await review.getByText(/Refresh results or permissions/).waitFor();
    assert.equal(await submit(review).isEnabled(), false);
    assert.equal(f.state.writes.length, 1);
    await review
      .getByRole("button", { name: "Close and refresh results", exact: true })
      .click();
    f.state.write = ({ route }) => route.abort("failed");
    review = await f.open();
    await waitEnabled(submit(review));
    await submit(review).click();
    await review.getByText(/Outcome unknown/).waitFor();
    assert.equal(await submit(review).isEnabled(), false);
    assert.equal(f.state.writes.length, 2);
  } finally {
    await f.close();
  }
});

void test("native in-flight write locks Escape and SPA navigation, confirms hard-leave warning and refreshes only after success", async () => {
  const f = await fixture();
  let respond;
  try {
    f.state.count = 1;
    f.state.write = (request) => {
      respond = () => request.respond({});
    };
    const review = await f.open();
    await waitEnabled(submit(review));
    await submit(review).click();
    await review.getByText(/Submitting… Closing is disabled/).waitFor();
    await f.page.keyboard.press("Escape");
    assert.equal(await review.isVisible(), true);
    await f.page.evaluate(async () => {
      const resource = performance
        .getEntriesByType("resource")
        .find((entry) =>
          entry.name.includes("/runtime/app/navigation/index.js"),
        );
      const { goto } = await import(resource.name);
      await goto("/wip/issues/80").catch(() => undefined);
    });
    assert.equal(new URL(f.page.url()).pathname, "/wip/issues/73");
    const nativeWarning = f.page.waitForEvent("dialog");
    const leave = f.page.evaluate(() => {
      location.assign("about:blank");
    });
    const warning = await nativeWarning;
    assert.equal(warning.type(), "beforeunload");
    await warning.dismiss();
    await leave;
    assert.equal(f.state.writes.length, 1);
    await respond();
    await f.page.getByText(/Create rerun request completed/).waitFor();
  } finally {
    await f.close();
  }
});

void test("native navigation and session changes fence held parsed preview and mutation error bodies without replay", async () => {
  const f = await fixture();
  try {
    await f.page.evaluate(
      () => (window.__rerunHold = { path: "/v1/test-results", method: "GET" }),
    );
    await f.open();
    await f.page.waitForFunction(() => window.__rerunReleases.length === 1);
    await f.page.evaluate(async () => {
      const resource = performance
        .getEntriesByType("resource")
        .find((entry) =>
          entry.name.includes("/runtime/app/navigation/index.js"),
        );
      const { goto } = await import(resource.name);
      await goto("/wip/issues/80");
      await goto("/wip/issues/73");
    });
    await f.release();
    assert.equal(
      await f.page.locator("dialog.bulk-rerun-review[open]").count(),
      0,
    );
    f.state.count = 1;
    f.state.writeStatus = 422;
    await f.page.evaluate(
      () =>
        (window.__rerunHold = {
          path: "/v1/test-executions/reruns",
          method: "POST",
        }),
    );
    const review = await f.open();
    await waitEnabled(submit(review));
    await submit(review).click();
    await f.page.waitForFunction(() => window.__rerunReleases.length === 1);
    f.state.me = null;
    await f.refresh();
    f.state.me = structuredClone(user);
    await f.refresh();
    await f.release();
    await f.page
      .getByRole("heading", { name: "Issue 73", exact: true })
      .waitFor();
    assert.equal(
      await f.page.locator("dialog.bulk-rerun-review[open]").count(),
      0,
    );
    assert.equal(
      (await f.page.locator(".issue-test-results").textContent()).includes(
        "Mocked write response",
      ),
      false,
    );
    assert.equal(f.state.writes.length, 1);
  } finally {
    await f.close();
  }
});

void test("native review retains Pragma controls, modal focus and reachable actions in light/dark and narrow viewports", async () => {
  const f = await fixture();
  try {
    for (const [width, height, theme] of [
      [1440, 900, "light"],
      [800, 600, "dark"],
      [390, 700, "light"],
    ]) {
      await f.page.setViewportSize({ width, height });
      await f.page.emulateMedia({ colorScheme: theme });
      await f.page.evaluate((theme) => {
        document.documentElement.classList.remove("light", "dark");
        document.documentElement.classList.add(theme);
      }, theme);
      const review = await f.open();
      await review.getByText(/Matches 125 test results/).waitFor();
      assert.equal(
        await review.evaluate((dialog) => dialog.matches(":modal")),
        true,
      );
      assert.equal(await review.locator("input.ds.checkbox").count(), 3);
      assert.equal(await review.locator("input.ds.text-input").count(), 1);
      await ack(review).check();
      await submit(review).focus();
      await f.page.keyboard.press("Tab");
      assert.equal(
        await review.evaluate((dialog) =>
          dialog.contains(document.activeElement),
        ),
        true,
      );
      const bounds =
        /** @type {{x: number; y: number; width: number; height: number}} */ (
          await review.boundingBox()
        );
      assert.ok(bounds.width <= width && bounds.height <= height);
      assert.ok(
        bounds.x >= 0 &&
          bounds.y >= 0 &&
          bounds.x + bounds.width <= width &&
          bounds.y + bounds.height <= height,
      );
      await review
        .getByRole("button", { name: "Cancel", exact: true })
        .scrollIntoViewIfNeeded();
      await f.page.screenshot({
        path: resolve(artifacts, `review-${width}-${theme}.png`),
      });
      await f.page.keyboard.press("Escape");
      assert.equal(
        await f.page.locator("dialog.bulk-rerun-review[open]").count(),
        0,
      );
      assert.equal(
        await f.page
          .locator(".rerun-actions button")
          .first()
          .evaluate((button) => document.activeElement === button),
        true,
      );
    }
    assert.equal(f.state.writes.length, 0);
  } finally {
    await f.close();
  }
});
