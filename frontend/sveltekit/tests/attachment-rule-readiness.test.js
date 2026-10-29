// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { resolve } from "node:path";
import { build } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { Window } from "happy-dom";

/** @type {typeof import('./attachment-rule-readiness-entry.svelte.js')} */
let app;
/** @type {Window} */
let browser;
/** @type {Map<string, PropertyDescriptor | undefined>} */
const globals = new Map();
const originalFetch = globalThis.fetch;
const json = (/** @type {unknown} */ body, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
const flush = () => new Promise((resolve) => setTimeout(resolve, 15));

function deferred() {
  /** @type {(value: Response) => void} */
  let complete;
  const promise = new Promise(
    /** @param {(value: Response) => void} resolve */ (resolve) => {
      complete = resolve;
    },
  );
  return {
    promise,
    resolve: (/** @type {Response} */ response) => {
      complete(response);
    },
  };
}

const bulkAdmin = { id: 500, name: "Bulk reviewer", teams: [], is_admin: true };
const bulkIssue = {
  id: 123,
  source: "github",
  project: "qa/project",
  key: "123",
  title: "Known issue 🐧",
  url: "https://github.com/qa/project/issues/123",
};
const response = () =>
  json({ count: 0, limit: 50, offset: 0, test_results: [] });

/** Transport fixture for the standalone reusable attachment-rule component.
 * @param {(request: URL, options: RequestInit) => Response | Promise<Response> | undefined} [override]
 */
function bulkTransport(override) {
  /** @type {{url: URL; options: RequestInit}[]} */
  const calls = [];
  globalThis.fetch = (input, options = {}) => {
    const request = new URL(input instanceof Request ? input.url : input);
    calls.push({ url: request, options });
    const special = override?.(request, options);
    if (special) return Promise.resolve(special);
    if (request.pathname.endsWith("/users/me"))
      return Promise.resolve(json(bulkAdmin));
    if (request.pathname.endsWith("/issues/123"))
      return Promise.resolve(
        json({
          ...bulkIssue,
          attachment_rules: [{ id: 77, enabled: true }],
        }),
      );
    if (request.pathname.endsWith("/issues"))
      return Promise.resolve(
        options.method === "PUT"
          ? json(bulkIssue)
          : json({ issues: [bulkIssue], count: 1 }),
      );
    if (request.pathname.endsWith("/attachment-rules"))
      return Promise.resolve(json({ id: 77, enabled: true }));
    return Promise.resolve(response());
  };
  return {
    calls,
    mutations: () =>
      calls.filter(({ options }) =>
        ["POST", "PUT", "DELETE"].includes(options.method ?? "GET"),
      ),
  };
}

/** @param {(request: URL, options: RequestInit) => Response | Promise<Response> | undefined} [override] */
function ruleTransport(override) {
  return bulkTransport(override);
}

function ruleDialog() {
  const dialog = browser.document.querySelector(
    "dialog.attachment-rule-review",
  );
  assert.ok(dialog, "An applied-query rule review is open");
  return /** @type {import('happy-dom').HTMLDialogElement} */ (dialog);
}

/** @param {import('happy-dom').HTMLElement} target @param {string} text */
function button(target, text) {
  const found = Array.from(target.querySelectorAll("button")).find((item) =>
    item.textContent.includes(text),
  );
  assert.ok(found, `Missing button ${text}`);
  return /** @type {import('happy-dom').HTMLButtonElement} */ (found);
}

/** @param {import('happy-dom').HTMLElement} target @param {string} selector @param {string} value */
async function enter(target, selector, value) {
  const input = /** @type {import('happy-dom').HTMLInputElement | null} */ (
    target.querySelector(selector)
  );
  assert.ok(input, selector);
  input.value = value;
  input.dispatchEvent(new browser.Event("input", { bubbles: true }));
  await flush();
  return input;
}

/** @param {import('happy-dom').HTMLElement} target */
async function openRule(target) {
  button(target, "Create Attachment Rule…").click();
  await flush();
  return ruleDialog();
}

/** @param {import('happy-dom').HTMLElement} dialog @param {string} [reference] */
async function pickBulkIssue(dialog, reference = "123") {
  await enter(dialog, 'input[name="bulk-issue"]', reference);
  button(dialog, "Use issue reference").click();
  await flush();
}

before(async () => {
  const built = /** @type {{output: {type: string; code: string}[]}[]} */ (
    /** @type {unknown} */ (
      await build({
        configFile: false,
        logLevel: "silent",
        plugins: [svelte({ compilerOptions: { runes: true } })],
        resolve: { alias: { $lib: resolve("src/lib") } },
        build: {
          write: false,
          lib: {
            entry: "tests/attachment-rule-readiness-entry.svelte.js",
            formats: ["es"],
          },
          rolldownOptions: { output: { codeSplitting: false } },
        },
      })
    )
  );
  const bundle = built[0].output.find((item) => item.type === "chunk");
  assert.ok(bundle);
  browser = new Window({ url: "http://localhost/" });
  for (const name of [
    "window",
    "document",
    "navigator",
    "Comment",
    "Text",
    "Node",
    "Element",
    "HTMLElement",
    "HTMLDialogElement",
    "HTMLInputElement",
    "HTMLMediaElement",
    "Event",
    "KeyboardEvent",
    "MouseEvent",
    "getComputedStyle",
    "requestAnimationFrame",
    "cancelAnimationFrame",
  ]) {
    globals.set(name, Object.getOwnPropertyDescriptor(globalThis, name));
    Object.defineProperty(globalThis, name, {
      configurable: true,
      value: name === "window" ? browser : Reflect.get(browser, name),
    });
  }
  browser.HTMLDialogElement.prototype.showModal = function () {
    this.open = true;
    this.setAttribute("open", "");
  };
  browser.HTMLDialogElement.prototype.close = function () {
    this.open = false;
    this.removeAttribute("open");
    this.dispatchEvent(new browser.Event("close"));
  };
  const imported = /** @type {unknown} */ (
    await import(
      `data:text/javascript;base64,${Buffer.from(bundle.code).toString("base64")}`
    )
  );
  app =
    /** @type {typeof import('./attachment-rule-readiness-entry.svelte.js')} */ (
      imported
    );
});

after(async () => {
  globalThis.fetch = originalFetch;
  await browser.happyDOM.abort();
  for (const [name, descriptor] of globals) {
    if (descriptor) Object.defineProperty(globalThis, name, descriptor);
    else Reflect.deleteProperty(globalThis, name);
  }
});

void test("standalone attachment-rule readiness revocation remains covered", async () => {
  for (const phase of [
    "open",
    "authorize",
    "create",
    "created-authorize",
    "post",
    "verify",
    "error-body",
  ]) {
    for (const flag of [
      "unapplied",
      "loading",
      "moving",
      "accessError",
      "available",
      "mutating",
    ]) {
      const pending = deferred();
      let sessions = 0;
      let reads = 0;
      const api = ruleTransport((request, options) => {
        if (request.pathname.endsWith("/users/me")) {
          sessions++;
          if (
            (phase === "open" && sessions === 1) ||
            (phase === "authorize" && sessions === 2) ||
            (phase === "created-authorize" && sessions === 3)
          )
            return pending.promise;
        }
        if (phase === "create" && options.method === "PUT")
          return pending.promise;
        if (request.pathname.endsWith("/attachment-rules")) {
          if (phase === "post") return pending.promise;
          if (phase === "error-body") {
            const result = json({}, 422);
            result.json = () =>
              pending.promise.then(() => ({ detail: "Slow rejection" }));
            return result;
          }
        }
        if (
          phase === "verify" &&
          request.pathname.endsWith("/issues/123") &&
          ++reads > 1
        )
          return pending.promise;
        return undefined;
      });
      const target = browser.document.createElement("div");
      browser.document.body.append(target);
      const ui = app.mountRule(
        /** @type {HTMLElement} */ (/** @type {unknown} */ (target)),
        [
          {
            name: "snaps",
            api_name: "snap",
            stages: [],
            columns: [],
            filters: [],
          },
        ],
      );
      try {
        const dialog = await openRule(target);
        if (phase !== "open") {
          await pickBulkIssue(
            dialog,
            ["create", "created-authorize"].includes(phase)
              ? bulkIssue.url
              : "123",
          );
          button(dialog, "Create enabled rule").click();
          await flush();
        }
        const count = api.mutations().length;
        ui.setReadiness(flag, flag !== "available");
        await flush();
        ui.setReadiness(flag, flag === "available");
        await flush();
        assert.match(
          dialog.textContent,
          /readiness or session changed/,
          `${phase}/${flag}`,
        );
        if (phase !== "open")
          assert.equal(
            button(dialog, "Cancel").disabled,
            true,
            "revocation retains in-flight guard",
          );
        pending.resolve(
          phase === "create"
            ? json(bulkIssue)
            : phase === "post"
              ? json({ id: 77, enabled: true })
              : phase === "verify"
                ? json({
                    ...bulkIssue,
                    attachment_rules: [{ id: 77, enabled: true }],
                  })
                : json(bulkAdmin),
        );
        await flush();
        await flush();
        assert.equal(api.mutations().length, count, `${phase}/${flag}`);
        assert.equal(button(dialog, "Create enabled rule").disabled, true);
        assert.deepEqual(ui.messages, []);
        assert.equal(
          ui.busyChanges.at(-1),
          phase === "open" ? undefined : false,
        );
      } finally {
        pending.resolve(json(bulkAdmin));
        await ui.destroy();
        target.remove();
      }
    }
  }
});
