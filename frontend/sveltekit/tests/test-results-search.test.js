// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { build } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { Window } from "happy-dom";

/** @type {typeof import('./test-results-search-entry.svelte.js')} */
let app;
/** @type {Window} */
let browser;
/** @type {Map<string, PropertyDescriptor | undefined>} */
const globals = new Map();
const originalFetch = globalThis.fetch;
const ORIGINAL_LIST_FILTERS = [
  "families",
  "test_result_statuses",
  "artefacts",
  "artefact_versions",
  "artefact_tracks",
  "environments",
  "test_plans",
  "test_cases",
];

const families = [
  {
    name: "configured-route",
    api_name: "snap",
    stages: ["alpha", "shared"],
    columns: [],
    filters: [],
  },
  {
    name: "another-route",
    api_name: "another-api-family",
    stages: ["beta", "shared"],
    columns: [],
    filters: [],
  },
];
const url = (/** @type {string} */ query = "") =>
  new URL(
    `https://observer.example/custom/base/test-results${query ? `?${query}` : ""}`,
  );
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

function result(id = 1) {
  return {
    test_result: {
      id,
      name: `case ${id}`,
      status: "FAILED",
      created_at: "2026-01-01T00:00:00Z",
    },
    artefact: {
      id: 42,
      name: "example artefact",
      version: "1.2",
      track: "stable",
      family: "snap",
    },
    artefact_build: { id: 3, architecture: "amd64", revision: 1 },
    test_execution: {
      id: 7,
      status: "FAILED",
      environment: { id: 5, name: "test lab", architecture: "amd64" },
      test_plan: "smoke",
    },
  };
}
const response = (ids = [1], count = ids.length, limit = 50, offset = 0) =>
  json({ count, limit, offset, test_results: ids.map(result) });

const bulkAdmin = { id: 500, name: "Bulk reviewer", teams: [], is_admin: true };
const bulkIssue = {
  id: 123,
  source: "github",
  project: "qa/project",
  key: "123",
  title: "Known issue 🐧",
  url: "https://github.com/qa/project/issues/123",
};
/** Mock only transport: all tests mount the actual page, Pragma and SvGrid.
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
      return Promise.resolve(json(bulkIssue));
    if (request.pathname.endsWith("/issues"))
      return Promise.resolve(
        options.method === "PUT"
          ? json(bulkIssue)
          : json({ issues: [bulkIssue], count: 1 }),
      );
    if (/\/issues\/\d+\/(attach|detach)$/.test(request.pathname))
      return Promise.resolve(json(bulkIssue));
    return Promise.resolve(response([1, 2], 120));
  };
  return {
    calls,
    mutations: () =>
      calls.filter(({ options }) =>
        ["POST", "PUT"].includes(options.method ?? "GET"),
      ),
    sessions: () =>
      calls.filter(({ url }) => url.pathname.endsWith("/users/me")),
    searches: () =>
      calls.filter(({ url }) => url.pathname.endsWith("/test-results")),
  };
}
function bulkDialog() {
  const dialog = browser.document.querySelector("dialog.bulk-issue-review");
  assert.ok(dialog);
  return /** @type {import('happy-dom').HTMLDialogElement} */ (dialog);
}

/** @param {import('happy-dom').HTMLElement} target @param {string} mode */
async function restoreChangedBulkContext(target, mode) {
  if (mode === "session") {
    await app.userStore.refresh(() => Promise.resolve(json(null)));
    await flush();
    assert.equal(
      app.userStore.current,
      null,
      "logout is observed before the same user returns",
    );
    await app.userStore.refresh(() => Promise.resolve(json(bulkAdmin)));
    await flush();
    assert.equal(app.userStore.current?.id, bulkAdmin.id);
  } else {
    selectionRow(target, 2).click();
    await flush();
    assert.match(target.textContent, /2 selected by result ID/);
    selectionRow(target, 2).click();
    await flush();
    assert.match(target.textContent, /1 selected by result ID/);
  }
}

void test("unrelated session refresh immediately revokes displayed gates, missing lookup is separate, and dialog authorization can be superseded", async () => {
  for (const mode of ["superseded", "lookup", "later-unknown"]) {
    const pending = deferred();
    let sessions = 0;
    const api = bulkTransport((request) => {
      if (!request.pathname.endsWith("/users/me")) return undefined;
      sessions++;
      if (mode === "lookup")
        return json({
          ...bulkAdmin,
          is_admin: false,
          teams: [{ permissions: ["change_issue_attachment"] }],
        });
      return mode === "superseded" && sessions === 2
        ? pending.promise
        : undefined;
    });
    const ui = mounted("artefacts=one");
    try {
      await flush();
      selectionRow(ui.target, 1).click();
      await flush();
      button(ui.target, "Bulk actions").click();
      await flush();
      button(ui.target, "Attach Issue…").click();
      await flush();
      const dialog = bulkDialog();
      if (mode === "superseded") {
        assert.match(dialog.textContent, /Checking permissions/);
        await app.userStore.refresh(() => Promise.resolve(json(bulkAdmin)));
        pending.resolve(json(bulkAdmin));
        await flush();
        assert.match(dialog.textContent, /superseded/);
      } else if (mode === "lookup") {
        assert.match(
          dialog.textContent,
          /Issue lookup: Missing confirmed global permission: view_issue/,
        );
        assert.equal(dialog.querySelector('input[name="bulk-issue"]'), null);
      } else {
        await pickBulkIssue(dialog);
        assert.equal(button(dialog, "Attach issue").disabled, false);
        await app.userStore.refresh(() => Promise.resolve(json({}, 503)));
        await flush();
        assert.equal(
          button(dialog, "Attach issue").disabled,
          true,
          "even a same-profile inconclusive later refresh revokes the reactive gate",
        );
      }
      assert.equal(api.mutations().length, 0);
    } finally {
      pending.resolve(json(bulkAdmin));
      await ui.destroy();
    }
  }
});

void test("creation errors/unknown outcomes never auto-retry or hide a known issue; slow creation cannot attach a changed scope", async () => {
  for (const mode of [
    "create-validation",
    "create-network",
    "attach-5xx",
    "changed-scope",
  ]) {
    const pending = deferred();
    const api = bulkTransport((_request, options) => {
      if (options.method === "PUT") {
        if (mode === "create-validation")
          return json({ detail: "Unrecognized issue URL" }, 422);
        if (mode === "create-network")
          return Promise.reject(new Error("Creation response lost"));
        if (mode === "changed-scope") return pending.promise;
      }
      return options.method === "POST" && mode === "attach-5xx"
        ? json({}, 503)
        : undefined;
    });
    const ui = mounted("artefacts=one");
    try {
      await flush();
      selectionRow(ui.target, 1).click();
      await flush();
      const dialog = await openBulk(ui.target);
      await pickBulkIssue(dialog, bulkIssue.url);
      button(dialog, "Attach issue").click();
      await flush();
      if (mode === "changed-scope") {
        selectionRow(ui.target, 2).click();
        await flush();
        pending.resolve(json(bulkIssue));
        await flush();
      }
      if (mode === "create-validation")
        assert.match(dialog.textContent, /Unrecognized issue URL/);
      else if (mode === "changed-scope")
        assert.match(
          dialog.textContent,
          /selection, applied query or session changed/,
        );
      else assert.match(dialog.textContent, /Outcome unknown/);
      assert.equal(
        api.mutations().filter(({ options }) => options.method === "PUT")
          .length,
        1,
      );
      assert.equal(
        api.mutations().filter(({ options }) => options.method === "POST")
          .length,
        mode === "attach-5xx" ? 1 : 0,
      );
      if (["attach-5xx", "changed-scope"].includes(mode))
        assert.match(dialog.textContent, /Issue #123 was created or found/);
      if (mode === "attach-5xx")
        assert.equal(
          button(dialog, "Retry attachment with this issue").disabled,
          true,
        );
      if (mode === "create-network")
        assert.equal(button(dialog, "Attach issue").disabled, true);
    } finally {
      pending.resolve(json(bulkIssue));
      await ui.destroy();
    }
  }
});

void test("observed logout or selection changes stay revoked after restoration during a slow creation PUT, retaining the created issue for renewed review", async () => {
  for (const mode of ["session", "selection"]) {
    const creation = deferred();
    const api = bulkTransport((_request, options) =>
      options.method === "PUT" ? creation.promise : undefined,
    );
    const ui = mounted("artefacts=one");
    try {
      await flush();
      selectionRow(ui.target, 1).click();
      await flush();
      const dialog = await openBulk(ui.target);
      await pickBulkIssue(dialog, bulkIssue.url);
      button(dialog, "Attach issue").click();
      await flush();
      assert.equal(api.mutations().length, 1, "the creation PUT is in flight");
      await restoreChangedBulkContext(ui.target, mode);
      assert.equal(
        button(dialog, "Cancel").disabled,
        true,
        "invalidation must not unlock closing while the PUT is still in flight",
      );
      creation.resolve(json(bulkIssue));
      await flush();
      await flush();
      assert.equal(
        api.mutations().length,
        1,
        "restoration must never authorize an attachment POST from the old review",
      );
      assert.equal(api.mutations()[0].options.method, "PUT");
      assert.match(dialog.textContent, /Issue #123 was created or found/);
      assert.match(
        dialog.textContent,
        /Close.*review.*again|Close.*review.*open Bulk actions again/,
      );
      assert.equal(
        button(dialog, "Retry attachment with this issue").disabled,
        true,
      );
      button(dialog, "Retry attachment with this issue").click();
      await flush();
      assert.equal(api.mutations().length, 1);
      assert.equal(button(dialog, "Cancel").disabled, false);
      button(dialog, "Cancel").click();
      await flush();
      const renewed = await openBulk(ui.target);
      await pickBulkIssue(renewed, String(bulkIssue.id));
      assert.equal(
        button(renewed, "Attach issue").disabled,
        false,
        "only a renewed user review can submit again",
      );
      assert.equal(
        api.mutations().length,
        1,
        "renewing review remains read-only",
      );
    } finally {
      creation.resolve(json(bulkIssue));
      await ui.destroy();
    }
  }
});

void test("review revocation survives restored context across submission authorization, post-creation authorization and attachment awaits", async () => {
  for (const phase of ["authorize", "created-authorize", "attach"]) {
    for (const mode of ["session", "selection"]) {
      const pending = deferred();
      let sessions = 0;
      const api = bulkTransport((request, options) => {
        if (request.pathname.endsWith("/users/me")) {
          sessions++;
          if (
            sessions === (phase === "created-authorize" ? 4 : 3) &&
            phase !== "attach"
          )
            return pending.promise;
        }
        return phase === "attach" && options.method === "POST"
          ? pending.promise
          : undefined;
      });
      const ui = mounted("artefacts=one");
      try {
        await flush();
        selectionRow(ui.target, 1).click();
        await flush();
        const dialog = await openBulk(ui.target);
        await pickBulkIssue(
          dialog,
          phase === "attach" ? String(bulkIssue.id) : bulkIssue.url,
        );
        button(dialog, "Attach issue").click();
        await flush();
        assert.equal(api.mutations().length, phase === "authorize" ? 0 : 1);
        await restoreChangedBulkContext(ui.target, mode);
        assert.equal(button(dialog, "Cancel").disabled, true);
        pending.resolve(json(phase === "attach" ? bulkIssue : bulkAdmin));
        await flush();
        await flush();
        assert.equal(
          api.mutations().length,
          phase === "authorize" ? 0 : 1,
          "no further mutation after any revoked await",
        );
        if (phase === "created-authorize") {
          assert.equal(api.mutations()[0].options.method, "PUT");
          assert.match(dialog.textContent, /Issue #123 was created or found/);
        }
        assert.match(
          dialog.textContent,
          /Close this review and open Bulk actions again/,
        );
        assert.equal(
          button(
            dialog,
            phase === "created-authorize"
              ? "Retry attachment with this issue"
              : "Attach issue",
          ).disabled,
          true,
        );
        assert.equal(button(dialog, "Cancel").disabled, false);
        assert.match(
          ui.target.textContent,
          /1 selected by result ID/,
          "a revoked completion cannot clear the restored selection",
        );
        assert.equal(
          api.searches().length,
          1,
          "a revoked completion cannot trigger success refresh",
        );
        if (phase === "attach")
          assert.match(
            dialog.textContent,
            /submitted request completed, but its review was revoked/,
          );
      } finally {
        pending.resolve(json(bulkAdmin));
        await ui.destroy();
      }
    }
  }
});

void test("a review blocks details stacking and becomes unusable after selection changes or explicit same-query Search", async () => {
  const api = bulkTransport();
  const ui = mounted("artefacts=one");
  try {
    await flush();
    selectionRow(ui.target, 1).click();
    await flush();
    const dialog = await openBulk(ui.target);
    await pickBulkIssue(dialog);
    detailsButton(ui.target, 1).click();
    await flush();
    assert.equal(
      detailsDialog().open,
      false,
      "stale/programmatic details cannot stack with review",
    );
    selectionRow(ui.target, 2).click();
    await flush();
    assert.match(
      dialog.textContent,
      /selection, applied query or session changed/,
    );
    assert.equal(button(dialog, "Attach issue").disabled, true);
    button(dialog, "Cancel").click();
    await flush();
    const next = await openBulk(ui.target);
    await pickBulkIssue(next);
    const staleSubmit = button(next, "Attach issue");
    button(ui.target, "Search").click();
    await flush();
    staleSubmit.click();
    await flush();
    assert.equal(api.mutations().length, 0);
    assert.equal(ui.target.querySelector(".selection-summary"), null);
    assert.equal(api.searches().length, 2);
  } finally {
    await ui.destroy();
  }
});

void test("a late post-success refresh cannot overwrite the next query, its view, confirmed drafts or selection", async () => {
  const oldRefresh = deferred();
  let finished = false;
  const api = bulkTransport((request, options) => {
    if (options.method === "POST") {
      finished = true;
      return json(bulkIssue);
    }
    if (finished && request.pathname.endsWith("/test-results"))
      return request.searchParams.get("artefacts") === "one"
        ? oldRefresh.promise
        : response([9], 1);
    return undefined;
  });
  const ui = mounted("artefacts=one");
  try {
    await flush();
    selectionRow(ui.target, 1).click();
    await flush();
    const dialog = await openBulk(ui.target);
    await pickBulkIssue(dialog);
    button(dialog, "Attach issue").click();
    await flush();
    const view = app.encodeView({ globalFilter: "case 9" });
    ui.handle.restore(url(`artefacts=two&view=${view}`));
    await flush();
    selectionRow(ui.target, 9).click();
    await flush();
    await chooseFilter(ui.target, "Template ID");
    await enter(
      ui.target,
      'input[name="template_ids"]',
      "next confirmed draft",
    );
    await confirmEditor(ui.target);
    oldRefresh.resolve(response([1, 2]));
    await flush();
    assert.equal(ui.handle.currentUrl.searchParams.get("artefacts"), "two");
    assert.equal(ui.handle.currentUrl.searchParams.get("view"), view);
    assert.match(ui.target.textContent, /1 selected by result ID/);
    assert.ok(ui.target.textContent.includes("next confirmed draft"));
    assert.ok(detailsButton(ui.target, 9));
    assert.equal(api.mutations().length, 1);
  } finally {
    oldRefresh.resolve(response([1, 2]));
    await ui.destroy();
  }
});
/** @param {import('happy-dom').HTMLElement} target @param {"attach" | "detach"} [operation] */
async function openBulk(target, operation = "attach") {
  button(target, "Bulk actions").click();
  await flush();
  button(
    target,
    operation === "attach" ? "Attach Issue…" : "Detach Issue…",
  ).click();
  await flush();
  const dialog = bulkDialog();
  assert.equal(dialog.open, true);
  return dialog;
}
/** @param {import('happy-dom').HTMLElement} dialog @param {string} [reference] */
async function pickBulkIssue(dialog, reference = "123") {
  await enter(dialog, 'input[name="bulk-issue"]', reference);
  button(dialog, "Use issue reference").click();
  await flush();
}

void test("contextual Pragma bulk menu has only attach/detach, refreshes lazily and restores keyboard focus without mutations", async () => {
  const api = bulkTransport();
  const ui = mounted("artefacts=one");
  try {
    await flush();
    assert.equal(
      [...ui.target.querySelectorAll("button")].some((b) =>
        b.textContent.includes("Bulk actions"),
      ),
      false,
    );
    selectionRow(ui.target, 1).click();
    await flush();
    assert.equal(api.sessions().length, 0);
    const trigger = button(ui.target, "Bulk actions");
    assert.equal(trigger.getAttribute("aria-haspopup"), "menu");
    assert.ok(trigger.querySelector("svg"), "labelled trigger has a chevron");
    trigger.dispatchEvent(
      new browser.KeyboardEvent("keydown", {
        key: "ArrowDown",
        bubbles: true,
        cancelable: true,
      }),
    );
    await flush();
    const menu = ui.target.querySelector('[role="menu"]');
    assert.ok(menu);
    assert.equal(menu.getAttribute("data-test-open"), "");
    assert.deepEqual(
      [...menu.querySelectorAll('[role="menuitem"]')].map((b) =>
        b.textContent.trim(),
      ),
      ["Attach Issue…", "Detach Issue…"],
    );
    assert.equal(api.sessions().length, 1);
    assert.equal(browser.document.activeElement, button(menu, "Attach Issue…"));
    button(menu, "Attach Issue…").dispatchEvent(
      new browser.KeyboardEvent("keydown", {
        key: "ArrowDown",
        bubbles: true,
        cancelable: true,
      }),
    );
    assert.equal(browser.document.activeElement, button(menu, "Detach Issue…"));
    button(menu, "Detach Issue…").click();
    await flush();
    assert.equal(api.sessions().length, 2);
    assert.match(bulkDialog().textContent, /1 test results/);
    assert.match(
      bulkDialog().textContent,
      /frozen preview, not a server transaction/,
    );
    assert.equal(detailsDialog().open, false);
    button(bulkDialog(), "Cancel").click();
    await flush();
    assert.equal(browser.document.activeElement, trigger);
    assert.equal(api.mutations().length, 0);
  } finally {
    await ui.destroy();
  }
});

void test("unsupported all-query exclusions/date-only and unapplied drafts explain disabled actions and send zero mutations", async () => {
  for (const mode of ["exclusions", "date", "draft"]) {
    const api = bulkTransport();
    const ui = mounted(
      mode === "date" ? "from_date=2026-01-01T00:00:00Z" : "artefacts=one",
    );
    try {
      await flush();
      selectionHeader(ui.target).click();
      await flush();
      if (mode !== "draft") {
        allMatchesCheckbox(ui.target)?.click();
        await flush();
      }
      if (mode === "exclusions") {
        selectionRow(ui.target, 2).click();
        await flush();
      }
      if (mode === "draft") {
        await chooseFilter(ui.target, "Template ID");
        await enter(ui.target, 'input[name="template_ids"]', "draft");
        await confirmEditor(ui.target);
      }
      button(ui.target, "Bulk actions").click();
      await flush();
      const action = button(ui.target, "Attach Issue…");
      assert.equal(action.disabled, true);
      assert.ok(action.getAttribute("aria-describedby"));
      assert.match(
        ui.target.textContent,
        mode === "exclusions"
          ? /exclusions are not supported/
          : mode === "date"
            ? /date-only query/
            : /Apply or discard draft/,
      );
      action.click();
      assert.equal(bulkDialog().open, false);
      assert.equal(api.mutations().length, 0);
    } finally {
      await ui.destroy();
    }
  }
});

void test("cached admin, unknown/logged-out/denied permissions and missing bulk grants fail closed, verified single-ID and global grants work", async () => {
  for (const mode of ["unknown", "logout", "denied", "normal-only", "global"]) {
    await app.userStore.refresh(() => Promise.resolve(json(bulkAdmin)));
    const api = bulkTransport((request) =>
      request.pathname.endsWith("/users/me")
        ? mode === "unknown"
          ? json({}, 503)
          : mode === "logout"
            ? json(null)
            : json({
                ...bulkAdmin,
                is_admin: false,
                teams: [
                  {
                    permissions:
                      mode === "denied"
                        ? []
                        : mode === "normal-only"
                          ? ["view_issue", "change_issue_attachment"]
                          : [
                              "view_issue",
                              "change_issue_attachment",
                              "change_issue_attachment_bulk",
                            ],
                  },
                ],
              })
        : undefined,
    );
    const ui = mounted("artefacts=one");
    try {
      await flush();
      selectionHeader(ui.target).click();
      await flush();
      button(ui.target, "Bulk actions").click();
      await flush();
      assert.equal(
        button(ui.target, "Attach Issue…").disabled,
        mode !== "global",
      );
      if (mode === "unknown")
        assert.match(ui.target.textContent, /unknown, cancelled or superseded/);
      if (mode === "logout")
        assert.match(ui.target.textContent, /Log in again/);
      if (mode === "normal-only") {
        selectionRow(ui.target, 2).click();
        await flush();
        assert.equal(
          button(ui.target, "Attach Issue…").disabled,
          false,
          "one verified ID needs the normal grant only",
        );
      }
      assert.equal(api.mutations().length, 0);
    } finally {
      await ui.destroy();
    }
  }
});

void test("cross-page explicit attach uses frozen IDs only and refreshes current results/attachments while retaining query and grid view", async () => {
  let refreshed = false;
  const api = bulkTransport((request, options) => {
    if (options.method === "POST") {
      refreshed = true;
      return json(bulkIssue);
    }
    if (request.pathname.endsWith("/test-results"))
      return json({
        count: 120,
        test_results: (request.searchParams.get("offset") === "2"
          ? [3, 4]
          : [1, 2]
        ).map((id) => ({
          ...detailedResult(id),
          test_result: {
            ...detailedResult(id).test_result,
            issues: refreshed ? [{ issue: bulkIssue }] : [],
          },
        })),
      });
    return undefined;
  });
  const ui = mounted("artefacts=one&limit=2");
  try {
    await flush();
    selectionRow(ui.target, 1).click();
    await flush();
    button(ui.target, "Next page").click();
    await flush();
    selectionRow(ui.target, 3).click();
    await flush();
    await localSearch(ui.target, "case 3");
    const view = /** @type {import('happy-dom').HTMLInputElement} */ (
      ui.target.querySelector(".sv-grid-global-filter input")
    ).value;
    const dialog = await openBulk(ui.target);
    assert.match(dialog.textContent, /2 test results/);
    assert.match(dialog.textContent, /Result IDs: 1, 3/);
    await pickBulkIssue(
      dialog,
      "https://observer.example/custom/base/issues/123",
    );
    button(dialog, "Attach issue").click();
    await flush();
    await flush();
    assert.equal(api.mutations().length, 1);
    assert.equal(api.mutations()[0].url.pathname, "/v1/issues/123/attach");
    assert.deepEqual(JSON.parse(api.mutations()[0].options.body), {
      test_results: [1, 3],
    });
    assert.equal(ui.handle.currentUrl.searchParams.get("artefacts"), "one");
    assert.equal(ui.handle.currentUrl.searchParams.get("offset"), "2");
    assert.equal(ui.target.querySelector(".selection-summary"), null);
    assert.equal(
      ui.target.querySelector(".sv-grid-global-filter input").value,
      view,
    );
    assert.match(ui.target.textContent, /does not report a changed count/);
    detailsButton(ui.target, 3).click();
    await flush();
    assert.match(detailsDialog().textContent, /Known issue 🐧/);
    assert.equal(
      api.sessions().length,
      3,
      "menu, dialog and immediately before submit",
    );
    assert.equal(
      api.searches().length,
      3,
      "initial, page, current-page refresh only",
    );
  } finally {
    await ui.destroy();
  }
});

void test("all-query detach requires same-modal acknowledgment above 50 and sends typed filters without pagination/view/base64", async () => {
  const api = bulkTransport();
  const metadata = `${Buffer.from("category").toString("base64")}:${Buffer.from("value").toString("base64")}`;
  const ui = mounted(
    `artefacts=one&artefact_is_archived=false&execution_metadata=${encodeURIComponent(metadata)}&limit=2&view=invalid`,
  );
  try {
    await flush();
    selectionHeader(ui.target).click();
    await flush();
    allMatchesCheckbox(ui.target)?.click();
    await flush();
    const dialog = await openBulk(ui.target, "detach");
    await pickBulkIssue(dialog, "https://observer.example/#/issues/123");
    assert.equal(button(dialog, "Detach issue").disabled, true);
    const ack = /** @type {import('happy-dom').HTMLInputElement | null} */ (
      dialog.querySelector('input[type="checkbox"]')
    );
    assert.ok(ack);
    ack.click();
    await flush();
    assert.equal(browser.document.querySelectorAll("dialog[open]").length, 1);
    button(dialog, "Detach issue").click();
    await flush();
    await flush();
    assert.equal(api.mutations().length, 1);
    assert.equal(api.mutations()[0].url.pathname, "/v1/issues/123/detach");
    assert.deepEqual(JSON.parse(api.mutations()[0].options.body), {
      test_results_filters: {
        artefacts: ["one"],
        artefact_is_archived: false,
        execution_metadata: { category: ["value"] },
      },
    });
  } finally {
    await ui.destroy();
  }
});

void test("rich single-issue suggestions reuse lookup/cache and never mutate until submission", async () => {
  const api = bulkTransport();
  const ui = mounted("artefacts=one");
  try {
    await flush();
    selectionRow(ui.target, 1).click();
    await flush();
    const dialog = await openBulk(ui.target);
    const input = await enter(
      dialog,
      'input[name="bulk-issue"]',
      "Known issue",
    );
    await settleSuggestions();
    assert.match(
      dialog.textContent,
      /#123 github — qa\/project\/123 — Known issue 🐧/,
    );
    input.focus();
    input.dispatchEvent(
      new browser.KeyboardEvent("keydown", {
        key: "ArrowDown",
        bubbles: true,
        cancelable: true,
      }),
    );
    assert.ok(browser.document.activeElement === button(dialog, "#123 github"));
    button(dialog, "#123 github").click();
    await flush();
    assert.equal(dialog.querySelector('input[name="bulk-issue"]'), null);
    assert.equal(
      app.searchFilterLabelCache().peek("issues", 123),
      "#123 github — qa/project/123 — Known issue 🐧",
    );
    assert.equal(api.mutations().length, 0);
    assert.equal(
      api.calls.filter(({ url }) => url.pathname.endsWith("/issues/123"))
        .length,
      0,
      "rich suggestion does not refetch detail",
    );
    button(dialog, "Cancel").click();
    await flush();
  } finally {
    await ui.destroy();
  }
});

void test("detach external URLs resolve only an exact existing issue with bounded q lookup and never PUT, including not-found/ambiguous matches", async () => {
  for (const mode of ["exact", "fuzzy", "ambiguous", "incomplete"]) {
    const api = bulkTransport((request) => {
      if (request.pathname.endsWith("/issues")) {
        const exact = { ...bulkIssue };
        return json({
          issues:
            mode === "fuzzy"
              ? [{ ...exact, url: `${exact.url}4` }]
              : mode === "ambiguous"
                ? [exact, { ...exact, id: 9 }]
                : [exact],
          count: mode === "incomplete" ? 30 : mode === "ambiguous" ? 2 : 1,
        });
      }
      return undefined;
    });
    const ui = mounted("artefacts=one");
    try {
      await flush();
      selectionRow(ui.target, 1).click();
      await flush();
      const dialog = await openBulk(ui.target, "detach");
      await pickBulkIssue(dialog, bulkIssue.url);
      if (mode === "exact") {
        button(dialog, "Detach issue").click();
        await flush();
        await flush();
      } else {
        assert.equal(button(dialog, "Detach issue").disabled, true);
        assert.match(dialog.textContent, /exact|unique/);
      }
      assert.equal(api.mutations().length, mode === "exact" ? 1 : 0);
      assert.equal(
        api.mutations().some(({ options }) => options.method === "PUT"),
        false,
      );
      const lookup = api.calls.find(({ url }) =>
        url.pathname.endsWith("/issues"),
      );
      assert.equal(lookup?.url.searchParams.get("q"), bulkIssue.url);
      assert.equal(lookup.url.searchParams.get("limit"), "10");
    } finally {
      await ui.destroy();
    }
  }
});

void test("issue creation is attach-only and separately authorized; known attachment failure retains issue ID for explicit retry without recreation", async () => {
  let denied = true;
  let posts = 0;
  const api = bulkTransport((request, options) => {
    if (request.pathname.endsWith("/users/me") && denied)
      return json({
        ...bulkAdmin,
        is_admin: false,
        teams: [{ permissions: ["view_issue", "change_issue_attachment"] }],
      });
    if (options.method === "POST")
      return ++posts === 1
        ? json({ detail: "Attachment validation failed" }, 422)
        : json(bulkIssue);
    return undefined;
  });
  const ui = mounted("artefacts=one");
  try {
    await flush();
    selectionRow(ui.target, 1).click();
    await flush();
    const dialog = await openBulk(ui.target);
    await pickBulkIssue(dialog, bulkIssue.url);
    assert.equal(button(dialog, "Attach issue").disabled, true);
    assert.match(dialog.textContent, /change_issue/);
    assert.equal(api.mutations().length, 0);
    denied = false;
    button(dialog, "Refresh permissions").click();
    await flush();
    button(dialog, "Attach issue").click();
    await flush();
    assert.equal(dialog.open, true);
    assert.match(dialog.textContent, /Issue #123 was created or found/);
    assert.match(dialog.textContent, /not atomic/);
    assert.match(dialog.textContent, /Attachment validation failed/);
    assert.equal(
      api.mutations().filter(({ options }) => options.method === "PUT").length,
      1,
    );
    button(dialog, "Retry attachment with this issue").click();
    await flush();
    await flush();
    assert.equal(api.mutations().length, 3);
    assert.equal(
      api.mutations().filter(({ options }) => options.method === "PUT").length,
      1,
    );
    assert.deepEqual(JSON.parse(api.mutations()[0].options.body), {
      url: bulkIssue.url,
    });
  } finally {
    await ui.destroy();
  }
});

void test("permission revocation/unknown/session expiry at submit sends no mutation despite an enabled reviewed choice", async () => {
  for (const mode of ["denied", "unknown", "logout"]) {
    let revoke = false;
    const api = bulkTransport((request) =>
      revoke && request.pathname.endsWith("/users/me")
        ? mode === "unknown"
          ? json({}, 503)
          : mode === "logout"
            ? json(null)
            : json({ ...bulkAdmin, is_admin: false, teams: [] })
        : undefined,
    );
    const ui = mounted("artefacts=one");
    try {
      await flush();
      selectionRow(ui.target, 1).click();
      await flush();
      const dialog = await openBulk(ui.target);
      await pickBulkIssue(dialog);
      assert.equal(button(dialog, "Attach issue").disabled, false);
      revoke = true;
      button(dialog, "Attach issue").click();
      await flush();
      assert.equal(api.mutations().length, 0);
      assert.match(
        dialog.textContent,
        /Missing confirmed|unknown|session changed/,
      );
    } finally {
      await ui.destroy();
    }
  }
});

void test("duplicate triggers, Escape, close and search/page controls cannot interrupt or resend an in-flight mutation", async () => {
  const pending = deferred();
  const api = bulkTransport((_request, options) =>
    options.method === "POST" ? pending.promise : undefined,
  );
  const ui = mounted("artefacts=one&limit=2");
  try {
    await flush();
    selectionRow(ui.target, 1).click();
    await flush();
    const dialog = await openBulk(ui.target);
    await pickBulkIssue(dialog);
    const submit = button(dialog, "Attach issue");
    submit.click();
    submit.click();
    await flush();
    assert.equal(api.mutations().length, 1);
    assert.equal(button(dialog, "Cancel").disabled, true);
    assert.equal(button(ui.target, "Search").disabled, true);
    assert.equal(button(ui.target, "Next page").disabled, true);
    dialog.dispatchEvent(
      new browser.KeyboardEvent("keydown", {
        key: "Escape",
        bubbles: true,
        cancelable: true,
      }),
    );
    await flush();
    assert.equal(dialog.open, true);
    pending.resolve(json(bulkIssue));
    await flush();
    await flush();
    assert.equal(api.mutations().length, 1);
    assert.equal(ui.target.querySelector(".selection-summary"), null);
  } finally {
    pending.resolve(json(bulkIssue));
    await ui.destroy();
  }
});

void test("server 401/403 inline errors remain retryable after fresh review while network/5xx outcomes block resubmission and explain uncertainty", async () => {
  for (const failure of [401, 403, 503, "network"]) {
    const api = bulkTransport((_request, options) =>
      options.method === "POST"
        ? failure === "network"
          ? Promise.reject(new Error("Connection lost"))
          : json({ detail: "Server declined" }, failure)
        : undefined,
    );
    const ui = mounted("artefacts=one");
    try {
      await flush();
      selectionRow(ui.target, 1).click();
      await flush();
      const dialog = await openBulk(ui.target);
      await pickBulkIssue(dialog);
      button(dialog, "Attach issue").click();
      await flush();
      assert.equal(api.mutations().length, 1);
      if (failure === 401) assert.match(dialog.textContent, /session expired/);
      else if (failure === 403)
        assert.match(dialog.textContent, /server denied/);
      else {
        assert.match(dialog.textContent, /Outcome unknown/);
        assert.match(dialog.textContent, /No automatic retry/);
        assert.equal(button(dialog, "Attach issue").disabled, true);
        button(dialog, "Attach issue").click();
        await flush();
        assert.equal(api.mutations().length, 1);
      }
      assert.match(ui.target.textContent, /1 selected by result ID/);
      assert.equal(
        app.errorStore.message,
        null,
        "bulk errors are local rather than global toasts",
      );
    } finally {
      await ui.destroy();
    }
  }
});

void test("pending submit authorization cannot mutate after selection/query/reapply/logout changes or outgoing unmount", async () => {
  for (const mode of ["selection", "query", "reapply", "logout", "unmount"]) {
    const auth = deferred();
    let wait = false;
    const api = bulkTransport((request) =>
      wait && request.pathname.endsWith("/users/me") ? auth.promise : undefined,
    );
    const ui = mounted("artefacts=one");
    try {
      await flush();
      selectionRow(ui.target, 1).click();
      await flush();
      const dialog = await openBulk(ui.target);
      await pickBulkIssue(dialog);
      wait = true;
      button(dialog, "Attach issue").click();
      await flush();
      if (mode === "selection") selectionRow(ui.target, 2).click();
      if (mode === "query") ui.handle.restore(url("artefacts=two"));
      if (mode === "reapply") ui.handle.restore(url("artefacts=one&limit=2"));
      if (mode === "logout")
        await app.userStore.refresh(() => Promise.resolve(json(null)));
      if (mode === "unmount") await ui.destroy();
      auth.resolve(json(bulkAdmin));
      await flush();
      await flush();
      assert.equal(api.mutations().length, 0);
    } finally {
      auth.resolve(json(bulkAdmin));
      if (mode !== "unmount") await ui.destroy();
    }
  }
});

void test("bulk cancellation and successful refresh preserve a suspended unconfirmed condition editor, confirmed query and view-only focus", async () => {
  const api = bulkTransport();
  const ui = mounted("artefacts=one&template_ids=confirmed");
  try {
    await flush();
    selectionRow(ui.target, 1).click();
    await flush();
    chip(ui.target, "Template ID").click();
    await flush();
    const input = await enter(
      ui.target,
      'input[name="template_ids"]',
      "unconfirmed 🐧",
    );
    const trigger = button(ui.target, "Bulk actions");
    trigger.dispatchEvent(
      new browser.MouseEvent("pointerdown", { bubbles: true }),
    );
    let dialog = await openBulk(ui.target);
    const focus = browser.document.activeElement;
    ui.handle.restore(
      url(
        `artefacts=one&template_ids=confirmed&view=${app.encodeView({ sorting: [{ id: "testCase", desc: true }] })}`,
      ),
    );
    await flush();
    assert.equal(dialog.open, true);
    assert.equal(browser.document.activeElement, focus);
    button(dialog, "Cancel").click();
    await flush();
    assert.equal(browser.document.activeElement, trigger);
    chip(ui.target, "Template ID").click();
    await flush();
    assert.equal(ui.target.querySelector('input[name="template_ids"]'), input);
    assert.equal(input.value, "unconfirmed 🐧");
    trigger.dispatchEvent(
      new browser.MouseEvent("pointerdown", { bubbles: true }),
    );
    dialog = await openBulk(ui.target);
    await pickBulkIssue(dialog);
    button(dialog, "Attach issue").click();
    await flush();
    await flush();
    assert.equal(
      ui.handle.currentUrl.searchParams.get("template_ids"),
      "confirmed",
    );
    assert.equal(
      chip(ui.target, "Template ID").getAttribute("title"),
      "Template ID: confirmed",
    );
    chip(ui.target, "Template ID").click();
    await flush();
    assert.equal(ui.target.querySelector('input[name="template_ids"]'), input);
    assert.equal(input.value, "unconfirmed 🐧");
    assert.equal(api.searches().length, 2);
  } finally {
    await ui.destroy();
  }
});

void test("successful detach can empty an out-of-range current page without stranding navigation or changing the query", async () => {
  let finished = false;
  const api = bulkTransport((request, options) => {
    if (options.method === "POST") {
      finished = true;
      return json(bulkIssue);
    }
    return finished && request.pathname.endsWith("/test-results")
      ? response([], 0)
      : undefined;
  });
  const ui = mounted("artefacts=one&issues=123&offset=50");
  try {
    await flush();
    selectionRow(ui.target, 1).click();
    await flush();
    const dialog = await openBulk(ui.target, "detach");
    await pickBulkIssue(dialog);
    button(dialog, "Detach issue").click();
    await flush();
    await flush();
    assert.match(ui.target.textContent, /No test results match/);
    assert.equal(button(ui.target, "Previous page").disabled, false);
    assert.equal(button(ui.target, "Next page").disabled, true);
    assert.equal(ui.handle.currentUrl.searchParams.get("offset"), "50");
    assert.equal(api.mutations().length, 1);
  } finally {
    await ui.destroy();
  }
});

function detailedResult(id = 1) {
  const row = result(id);
  return {
    ...row,
    test_result: {
      ...row.test_result,
      category: `category ${id}`,
      template_id: `template ${id}`,
      io_log: "",
      issues: [],
    },
    test_execution: {
      ...row.test_execution,
      created_at: "2026-02-03T12:34:56+05:30",
      execution_metadata: { "ζ Unicode 🐧": ["二", "一"], Alpha: ["z", "a"] },
    },
  };
}

/** @param {import('happy-dom').HTMLElement} target @param {number} id */
function detailsButton(target, id) {
  const found = target.querySelector(
    `button[aria-label="View details for case ${id}"]`,
  );
  assert.ok(found);
  return /** @type {import('happy-dom').HTMLButtonElement} */ (found);
}

function detailsDialog() {
  const dialog = browser.document.querySelector("dialog.search-result-details");
  assert.ok(dialog);
  return dialog;
}

void test("Details is the third native grid column and resolves raw IDs after local sort/filter without requests or selection", async () => {
  let calls = 0;
  const rows = [detailedResult(20), detailedResult(3), detailedResult(11)];
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(json({ count: 3, test_results: rows }));
  };
  const ui = mounted("artefacts=one");
  try {
    await flush();
    const headers = [...ui.target.querySelectorAll("thead tr th")];
    assert.ok(headers[0].classList.contains("sv-grid-selection-column"));
    assert.deepEqual(
      headers
        .slice(1, 4)
        .map((header) => header.getAttribute("data-svgrid-header-col")),
      ["run", "details", "artefact"],
    );
    assert.equal(!!headers[2].querySelector(".sv-grid-filter-button"), false);
    assert.equal(
      browser.document.querySelectorAll("dialog.search-result-details").length,
      1,
    );
    const sort = /** @type {import('happy-dom').HTMLButtonElement | null} */ (
      ui.target.querySelector(
        '[data-svgrid-header-col="testCase"] button.sv-grid-header-sort',
      )
    );
    assert.ok(sort);
    sort.click();
    await flush();
    const renderedIds = [
      ...ui.target.querySelectorAll("tbody button[data-test-result-id]"),
    ].map((button) => button.getAttribute("data-test-result-id"));
    assert.equal(
      new Set(renderedIds).size,
      renderedIds.length,
      "no duplicate row artifacts after sorting",
    );
    await localSearch(ui.target, "case 11");
    assert.equal(
      ui.target.querySelectorAll("tbody button[data-test-result-id]").length,
      1,
    );
    const before = ui.handle.currentUrl.href;
    const writes = ui.handle.replacements.length;
    const trigger = detailsButton(ui.target, 11);
    assert.ok(trigger.classList.contains("details-button"));
    assert.ok(
      trigger.querySelector(".icon.left svg"),
      "Details has an always-visible icon in Pragma's icon slot",
    );
    assert.ok(
      trigger.querySelector('.details-icon[aria-hidden="true"]'),
      "the decorative eye has its own non-shrinking size container",
    );
    assert.equal(trigger.querySelector(".text")?.textContent.trim(), "Details");
    trigger.dispatchEvent(
      new browser.MouseEvent("pointerdown", { bubbles: true, shiftKey: true }),
    );
    trigger.dispatchEvent(
      new browser.KeyboardEvent("keydown", { key: "Enter", bubbles: true }),
    );
    await flush();
    const dialog = detailsDialog();
    assert.equal(dialog.open, true);
    assert.match(dialog.textContent, /category 11/);
    assert.match(dialog.textContent, /template 11/);
    assert.equal(
      dialog
        .querySelector('a[aria-label="View Run for case 11"]')
        ?.getAttribute("href"),
      "/custom/base/configured-route/42?testExecutionId=7&testResultId=11",
    );
    assert.equal(ui.handle.currentUrl.href, before);
    assert.equal(ui.handle.replacements.length, writes);
    assert.equal(ui.target.querySelector(".selection-summary"), null);
    assert.equal(ui.target.querySelector(".sv-grid-cell-selected"), null);
    button(dialog, "Close").click();
    await flush();
    assert.equal(browser.document.activeElement, trigger);
    assert.equal(calls, 1);
    await localSearch(ui.target, "category 11");
    assert.equal(
      ui.target.querySelectorAll("tbody button[aria-haspopup=dialog]").length,
      0,
      "raw details must not participate in global filtering",
    );
    await localSearch(ui.target, "[object Object]");
    assert.equal(
      ui.target.querySelectorAll("tbody button[aria-haspopup=dialog]").length,
      0,
    );
  } finally {
    await ui.destroy();
  }
});

void test("loaded details show every Flutter-functional section, sorted Unicode metadata, execution timestamp and all future internal issues; logs stay literal and complete", async () => {
  const row = detailedResult(1);
  const log = `<script>globalThis.pwned=true</script>\n<img src=x onerror=alert(1)> & Ω\n  indented\n${"x".repeat(100_000)}\nEND`;
  const populated = {
    ...row,
    test_result: {
      ...row.test_result,
      io_log: log,
      issues: [
        {
          issue: {
            id: 123,
            source: "github",
            project: "org/project",
            key: "#123",
            title: "First <b>literal</b>",
            status: "open",
            url: "https://tracker.invalid/not-used",
          },
        },
        {
          issue: {
            id: 456,
            source: "jira",
            project: "Team",
            key: "TEAM-456",
            title: "Second 🐧",
            status: "closed",
            url: "javascript:alert(1)",
          },
        },
      ],
    },
  };
  globalThis.fetch = () =>
    Promise.resolve(json({ count: 1, test_results: [populated] }));
  const ui = mounted("artefacts=one");
  try {
    await flush();
    detailsButton(ui.target, 1).click();
    await flush();
    const dialog = detailsDialog();
    assert.equal(
      dialog.querySelector("h2")?.textContent,
      "Test result details",
    );
    assert.deepEqual(
      [...dialog.querySelectorAll("h3")].map((heading) => heading.textContent),
      ["Test Case", "Artefact", "Test Execution", "Issues", "IO Log"],
    );
    for (const text of [
      "category 1",
      "template 1",
      "Configured-route",
      "example artefact",
      "1.2",
      "stable",
      "amd64",
      "smoke",
      "test lab",
      "org/project",
      "TEAM-456",
      "Second 🐧",
      "github",
      "jira",
      "open",
      "closed",
    ])
      assert.ok(dialog.textContent.includes(text), text);
    assert.deepEqual(
      [
        ...dialog.querySelectorAll(".execution-metadata tbody th[scope=row]"),
      ].map((node) => node.textContent),
      ["Alpha", "ζ Unicode 🐧"],
    );
    assert.deepEqual(
      [...dialog.querySelectorAll(".execution-metadata li")].map(
        (node) => node.textContent,
      ),
      ["a", "z", "一", "二"],
    );
    const table = dialog.querySelector("table.execution-metadata");
    assert.ok(table, "Metadata is a real table, not scalar description items");
    assert.equal(
      table.closest("dd"),
      null,
      "Metadata uses the section's full width",
    );
    assert.deepEqual(
      [...table.querySelectorAll("thead th[scope=col]")].map(
        (node) => node.textContent,
      ),
      ["Category", "Values"],
    );
    assert.deepEqual(
      [...dialog.querySelectorAll("section > .description-list-container")].map(
        (container) =>
          [...container.querySelectorAll("dt")].map((node) => node.textContent),
      ),
      [
        ["Name", "Category", "Template ID", "Status"],
        ["Family", "Name", "Version", "Track", "Architecture"],
        ["Execution ID", "Test Plan", "Environment", "Status", "Created"],
      ],
    );
    for (const list of dialog.querySelectorAll("dl")) {
      assert.ok(list.classList.contains("list"));
      for (const item of list.children) {
        assert.deepEqual(
          [...item.children].map((node) => node.tagName),
          ["DT", "DD"],
          "Each semantic scalar row pairs one label with one value",
        );
      }
    }
    const time = dialog.querySelector("time");
    assert.equal(time?.getAttribute("datetime"), "2026-02-03T07:04:56.000Z");
    assert.equal(time.getAttribute("title"), row.test_execution.created_at);
    assert.equal(
      time.textContent,
      new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "long",
      }).format(new Date(row.test_execution.created_at)),
    );
    const links = [...dialog.querySelectorAll(".issues a")];
    assert.deepEqual(
      links.map((link) => link.getAttribute("href")),
      ["/custom/base/issues/123", "/custom/base/issues/456"],
    );
    for (const link of links) {
      assert.equal(link.getAttribute("target"), "_blank");
      assert.equal(link.getAttribute("rel"), "noopener noreferrer");
      assert.match(link.getAttribute("aria-label") ?? "", /View issue/);
    }
    assert.equal(dialog.querySelector("pre")?.textContent, log);
    assert.equal(dialog.querySelector("pre")?.hasAttribute("tabindex"), false);
    assert.equal(dialog.querySelector("pre")?.hasAttribute("role"), false);
    assert.equal(dialog.querySelector("script, img, b"), null);
    assert.ok(dialog.querySelector("header, .dialog-content-header"));
    assert.ok(dialog.querySelector("footer, .dialog-content-footer"));
    assert.equal(dialog.querySelectorAll(".issues > li").length, 2);
  } finally {
    await ui.destroy();
  }
});

void test("empty optional details use em dashes and explicit metadata empty state; unconfigured family still opens without guessed Run", async () => {
  const row = detailedResult(1);
  const empty = {
    ...row,
    artefact: {
      ...row.artefact,
      family: "unconfigured",
      track: "",
      version: "",
    },
    test_execution: {
      ...row.test_execution,
      execution_metadata: {},
      created_at: "",
      test_plan: "",
    },
    test_result: { ...row.test_result, category: "", template_id: "" },
  };
  globalThis.fetch = () =>
    Promise.resolve(json({ count: 1, test_results: [empty] }));
  const ui = mounted("artefacts=one");
  try {
    await flush();
    detailsButton(ui.target, 1).click();
    await flush();
    const dialog = detailsDialog();
    assert.match(dialog.textContent, /No execution metadata available\./);
    assert.equal(dialog.querySelector("pre, time, .issues, a"), null);
    assert.match(dialog.textContent, /Run unavailable/);
    assert.equal(
      [...dialog.querySelectorAll("dd")].filter(
        (node) => node.textContent === "—",
      ).length,
      6,
    );
    assert.deepEqual(
      [...dialog.querySelectorAll("h3")].map((node) => node.textContent),
      ["Test Case", "Artefact", "Test Execution"],
    );
  } finally {
    await ui.destroy();
  }
});

void test("Details retains explicit/all-matches exclusions, confirmed/unconfirmed drafts, grid identity and view-only history focus with no traffic", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(
      json({ count: 19, test_results: [detailedResult(1), detailedResult(2)] }),
    );
  };
  const ui = mounted("artefacts=one");
  try {
    await flush();
    selectionRow(ui.target, 1).click();
    await flush();
    detailsButton(ui.target, 1).click();
    await flush();
    button(detailsDialog(), "Close").click();
    await flush();
    assert.match(ui.target.textContent, /1 selected by result ID/);
    selectionHeader(ui.target).click();
    await flush();
    allMatchesCheckbox(ui.target)?.click();
    await flush();
    selectionRow(ui.target, 2).click();
    await flush();
    await chooseFilter(ui.target, "Template ID");
    await enter(ui.target, 'input[name="template_ids"]', "confirmed draft");
    await confirmEditor(ui.target);
    chip(ui.target, "Template ID").click();
    await flush();
    const input = await enter(
      ui.target,
      'input[name="template_ids"]',
      "unconfirmed 🐧",
    );
    const grid = ui.target.querySelector(".sv-grid-root");
    const href = ui.handle.currentUrl.href;
    const writes = ui.handle.replacements.length;
    const trigger = detailsButton(ui.target, 1);
    trigger.dispatchEvent(
      new browser.MouseEvent("pointerdown", { bubbles: true }),
    );
    trigger.click();
    await flush();
    const dialog = detailsDialog();
    assert.equal(dialog.open, true);
    const focus = browser.document.activeElement;
    const view = app.encodeView({ sorting: [{ id: "testCase", desc: true }] });
    ui.handle.restore(url(`artefacts=one&view=${view}`));
    await flush();
    ui.handle.restore(url("artefacts=one"));
    await flush();
    assert.equal(detailsDialog(), dialog);
    assert.equal(dialog.open, true);
    assert.equal(browser.document.activeElement, focus);
    assert.equal(ui.target.querySelector(".sv-grid-root"), grid);
    assert.match(
      ui.target.textContent,
      /18 selected across the applied query \(1 excluded\)/,
    );
    assert.equal(
      selectionRow(ui.target, 2).getAttribute("aria-checked"),
      "false",
    );
    assert.equal(ui.handle.currentUrl.href, href);
    assert.equal(ui.handle.replacements.length, writes);
    const x = /** @type {import('happy-dom').HTMLButtonElement | null} */ (
      dialog.querySelector("button[aria-label='Close details']")
    );
    x?.click();
    await flush();
    assert.equal(browser.document.activeElement, trigger);
    assert.equal(
      chip(ui.target, "Template ID").getAttribute("title"),
      "Template ID: confirmed draft",
    );
    chip(ui.target, "Template ID").click();
    await flush();
    assert.equal(ui.target.querySelector('input[name="template_ids"]'), input);
    assert.equal(input.value, "unconfirmed 🐧");
    assert.equal(calls, 1);
  } finally {
    await ui.destroy();
  }
});

void test("saving a Details-suspended editor retains its unconfirmed field but cannot resurrect another removed confirmed filter", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(
      json({ count: 1, test_results: [detailedResult(1)] }),
    );
  };
  // A and B are both confirmed; only A has unconfirmed edits.
  const ui = mounted("template_ids=confirmed-A&artefacts=confirmed-B");
  try {
    await flush();
    chip(ui.target, "Template ID").click();
    await flush();
    const input = await enter(
      ui.target,
      'input[name="template_ids"]',
      "unconfirmed-A 🐧",
    );
    const trigger = detailsButton(ui.target, 1);
    trigger.dispatchEvent(
      new browser.MouseEvent("pointerdown", { bubbles: true }),
    );
    trigger.click();
    await flush();
    button(detailsDialog(), "Close").click();
    await flush();
    const removeB =
      /** @type {import('happy-dom').HTMLButtonElement | null} */ (
        ui.target.querySelector('button[aria-label="Remove Artefact filter"]')
      );
    assert.ok(removeB);
    removeB.click();
    await flush();
    assert.equal(
      ui.target.querySelectorAll('.chip-trigger[aria-label^="Edit Artefact:"]')
        .length,
      0,
    );
    chip(ui.target, "Template ID").click();
    await flush();
    assert.equal(ui.target.querySelector('input[name="template_ids"]'), input);
    assert.equal(input.value, "unconfirmed-A 🐧");
    await confirmEditor(ui.target);
    assert.equal(
      chip(ui.target, "Template ID").getAttribute("title"),
      "Template ID: unconfirmed-A 🐧",
    );
    assert.equal(
      ui.target.querySelectorAll('.chip-trigger[aria-label^="Edit Artefact:"]')
        .length,
      0,
      "saving A must not restore removed B from its suspended snapshot",
    );
    assert.equal(
      calls.length,
      1,
      "Details, removing B and saving A do not search",
    );
    assert.equal(
      ui.handle.currentUrl.searchParams.get("artefacts"),
      "confirmed-B",
      "applied URL stays unchanged until Search",
    );
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls.length, 2);
    assert.equal(calls[1].searchParams.get("template_ids"), "unconfirmed-A 🐧");
    assert.equal(calls[1].searchParams.has("artefacts"), false);
    assert.equal(ui.handle.currentUrl.searchParams.has("artefacts"), false);
  } finally {
    await ui.destroy();
  }
});

void test("a resumed Details-suspended date editor revalidates pending From text after the confirmed Until chip is removed", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(
      json({ count: 1, test_results: [detailedResult(1)] }),
    );
  };
  const ui = mounted(
    "from_date=2026-01-01T00:00:00Z&until_date=2026-01-10T00:00:00Z",
  );
  try {
    await flush();
    chip(ui.target, "From").click();
    await flush();
    const input = await enter(
      ui.target,
      'input[name="from_date"]',
      "2026-01-15T00:00:00Z",
    );
    assert.equal(button(panel(ui.target), "Save changes").disabled, true);
    assert.match(panel(ui.target).textContent, /From must not be after Until/);
    const trigger = detailsButton(ui.target, 1);
    trigger.dispatchEvent(
      new browser.MouseEvent("pointerdown", { bubbles: true }),
    );
    trigger.click();
    await flush();
    button(detailsDialog(), "Close").click();
    await flush();
    const removeUntil =
      /** @type {import('happy-dom').HTMLButtonElement | null} */ (
        ui.target.querySelector('button[aria-label="Remove Until filter"]')
      );
    assert.ok(removeUntil);
    removeUntil.click();
    await flush();
    chip(ui.target, "From").click();
    await flush();
    assert.equal(
      ui.target.querySelector('input[name="from_date"]'),
      input,
      "resume must retain the mounted child holding invalid pending text",
    );
    assert.equal(input.value, "2026-01-15T00:00:00Z");
    assert.equal(
      button(panel(ui.target), "Save changes").disabled,
      false,
      "removed Until must no longer constrain the pending From value",
    );
    assert.doesNotMatch(
      panel(ui.target).textContent,
      /From must not be after Until|Until: 2026-01-10/,
    );
    await confirmEditor(ui.target);
    assert.equal(
      chip(ui.target, "From").getAttribute("title"),
      "From: 2026-01-15T00:00:00Z",
    );
    assert.equal(
      ui.target.querySelectorAll('.chip-trigger[aria-label^="Edit Until:"]')
        .length,
      0,
    );
    assert.equal(calls, 1, "resume and saving the rebased draft do not search");
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls, 2);
    assert.equal(
      ui.handle.currentUrl.searchParams.get("from_date"),
      "2026-01-15T00:00:00Z",
    );
    assert.equal(ui.handle.currentUrl.searchParams.has("until_date"), false);
  } finally {
    await ui.destroy();
  }
});

void test("a resumed Details-suspended lookup rebases removed Family context, cancels stale bodies and retains mounted pending input and selections", async () => {
  const late = deferred();
  const old = json({});
  old.json = async () => {
    const response = await late.promise;
    // eslint-disable-next-line @typescript-eslint/no-unsafe-return -- Browser response parser.
    return response.json();
  };
  const fresh = deferred();
  /** @type {AbortSignal | null | undefined} */ let oldSignal;
  /** @type {URL[]} */ const lookups = [];
  let resultsCalls = 0;
  globalThis.fetch = (input, options) => {
    const request = new URL(input instanceof Request ? input.url : input);
    if (request.pathname.endsWith("/test-results")) {
      resultsCalls++;
      return Promise.resolve(
        json({ count: 1, test_results: [detailedResult(1)] }),
      );
    }
    lookups.push(request);
    if (request.searchParams.has("families")) {
      oldSignal = options?.signal;
      return Promise.resolve(old);
    }
    return fresh.promise;
  };
  const ui = mounted("families=snap&artefacts=confirmed");
  try {
    await flush();
    chip(ui.target, "Artefact").click();
    await flush();
    await enter(ui.target, 'input[name="artefacts"]', "unconfirmed selected");
    button(panel(ui.target), "Add exact value").click();
    await flush();
    const input = await enter(
      ui.target,
      'input[name="artefacts"]',
      "pending lookup 🐧",
    );
    await settleSuggestions();
    assert.equal(lookups.length, 1);
    assert.deepEqual(lookups[0].searchParams.getAll("families"), ["snap"]);
    const trigger = detailsButton(ui.target, 1);
    trigger.dispatchEvent(
      new browser.MouseEvent("pointerdown", { bubbles: true }),
    );
    trigger.click();
    await flush();
    assert.equal(
      detailsDialog().contains(browser.document.activeElement),
      true,
    );
    button(detailsDialog(), "Close").click();
    await flush();
    assert.equal(browser.document.activeElement, trigger);
    const removeFamily =
      /** @type {import('happy-dom').HTMLButtonElement | null} */ (
        ui.target.querySelector('button[aria-label="Remove Family filter"]')
      );
    assert.ok(removeFamily);
    removeFamily.click();
    await flush();
    chip(ui.target, "Artefact").click();
    await flush();
    assert.equal(ui.target.querySelector('input[name="artefacts"]'), input);
    assert.equal(input.value, "pending lookup 🐧");
    assert.equal(
      oldSignal?.aborted,
      true,
      "resuming with the live Family context cancels the old restricted lookup",
    );
    assert.equal(browser.document.activeElement, input);
    assert.match(panel(ui.target).textContent, /confirmed/);
    assert.match(panel(ui.target).textContent, /unconfirmed selected/);
    late.resolve(json({ artefacts: ["STALE FAMILY RESULT"] }));
    await settleSuggestions();
    assert.equal(lookups.length, 2);
    assert.equal(lookups[1].searchParams.has("families"), false);
    assert.equal(lookups[1].searchParams.get("q"), "pending lookup 🐧");
    assert.doesNotMatch(panel(ui.target).textContent, /STALE FAMILY RESULT/);
    assert.equal(browser.document.activeElement, input);
    fresh.resolve(json({ artefacts: ["unrestricted fresh result"] }));
    await flush();
    assert.match(panel(ui.target).textContent, /unrestricted fresh result/);
    assert.doesNotMatch(panel(ui.target).textContent, /STALE FAMILY RESULT/);
    assert.equal(
      browser.document.activeElement,
      input,
      "neither stale nor current replies may steal editor focus",
    );
    assert.equal(input.value, "pending lookup 🐧");
    assert.equal(
      button(panel(ui.target), "Save changes").disabled,
      true,
      "pending query text stays unconfirmed",
    );
    button(panel(ui.target), "Clear input").click();
    await flush();
    await confirmEditor(ui.target);
    assert.equal(
      chip(ui.target, "Artefact").getAttribute("title"),
      "Artefact: confirmed, unconfirmed selected",
    );
    assert.equal(
      ui.target.querySelectorAll('.chip-trigger[aria-label^="Edit Family:"]')
        .length,
      0,
    );
    assert.equal(resultsCalls, 1);
    assert.equal(
      lookups.length,
      2,
      "only the original and context-refreshed suggestion requests are sent",
    );
    assert.equal(
      ui.handle.currentUrl.searchParams.get("families"),
      "snap",
      "draft changes still await explicit Search",
    );
  } finally {
    await ui.destroy();
  }
});

void test("native close, filtered-away trigger fallback and dataset/unmount invalidation reject stale Details callbacks", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(
      json({ count: 19, test_results: [detailedResult(1), detailedResult(2)] }),
    );
  };
  const ui = mounted("artefacts=one&limit=2");
  try {
    await flush();
    const oldTrigger = detailsButton(ui.target, 1);
    oldTrigger.click();
    await flush();
    const dialog = detailsDialog();
    dialog
      .querySelector("button")
      ?.dispatchEvent(
        new browser.KeyboardEvent("keydown", { key: "Escape", bubbles: true }),
      );
    await flush();
    assert.equal(dialog.open, false);
    assert.equal(browser.document.activeElement, oldTrigger);
    oldTrigger.click();
    await flush();
    const encoded = app.encodeView({ globalFilter: "case 2" });
    ui.handle.restore(url(`artefacts=one&limit=2&view=${encoded}`));
    await flush();
    assert.equal(dialog.open, true);
    assert.notEqual(
      oldTrigger.getAttribute("data-test-result-id"),
      "1",
      "SvGrid may recycle a still-connected cell for another result",
    );
    button(dialog, "Close").click();
    await flush();
    assert.equal(
      browser.document.activeElement,
      ui.target.querySelector(".results-grid"),
    );
    detailsButton(ui.target, 2).click();
    await flush();
    ui.handle.restore(url("artefacts=two&limit=2"));
    await flush();
    assert.equal(dialog.open, false);
    oldTrigger.click();
    await flush();
    assert.equal(dialog.open, false);
    detailsButton(ui.target, 1).click();
    await flush();
    button(ui.target, "Next page").click();
    await flush();
    assert.equal(dialog.open, false);
    detailsButton(ui.target, 1).click();
    await flush();
    button(ui.target, "Search").click();
    await flush();
    assert.equal(dialog.open, false);
    assert.equal(
      calls,
      4,
      "only initial/query/pagination/reapply request results",
    );
    detailsButton(ui.target, 1).click();
    await flush();
    assert.equal(dialog.open, true);
  } finally {
    await ui.destroy();
  }
  assert.equal(
    browser.document.querySelector("dialog.search-result-details"),
    null,
  );
});

void test("pending suggestions/labels and view polling complete behind Details without moving modal focus or erasing suspended editor input", async () => {
  const pending = deferred();
  const pendingLabel = deferred();
  let suggestions = 0;
  let calls = 0;
  globalThis.fetch = (input) => {
    calls++;
    const request = new URL(input instanceof Request ? input.url : input);
    if (request.pathname.endsWith("/issues/990019"))
      return pendingLabel.promise;
    if (request.pathname.endsWith("/artefacts/search")) {
      suggestions++;
      return pending.promise;
    }
    return Promise.resolve(
      json({ count: 1, test_results: [detailedResult(1)] }),
    );
  };
  const ui = mounted("artefacts=one&issues=990019");
  try {
    await flush();
    chip(ui.target, "Artefact").click();
    await flush();
    const input = await enter(
      ui.target,
      'input[name="artefacts"]',
      "pending text",
    );
    await new Promise((resolve) => setTimeout(resolve, 280));
    assert.equal(suggestions, 1);
    const trigger = detailsButton(ui.target, 1);
    trigger.dispatchEvent(
      new browser.MouseEvent("pointerdown", { bubbles: true }),
    );
    trigger.click();
    await flush();
    const focused = browser.document.activeElement;
    pending.resolve(json([{ name: "pending text suggestion" }]));
    pendingLabel.resolve(
      json({
        id: 990019,
        source: "github",
        project: "org",
        key: "990019",
        title: "Hydrated behind modal",
      }),
    );
    await new Promise((resolve) => setTimeout(resolve, 280));
    assert.equal(detailsDialog().open, true);
    assert.equal(browser.document.activeElement, focused);
    assert.match(
      chip(ui.target, "Issues").getAttribute("title") ?? "",
      /Hydrated behind modal/,
    );
    button(detailsDialog(), "Close").click();
    await flush();
    chip(ui.target, "Artefact").click();
    await flush();
    assert.equal(ui.target.querySelector('input[name="artefacts"]'), input);
    assert.equal(input.value, "pending text");
    assert.equal(suggestions, 1);
    assert.equal(
      calls,
      3,
      "only initial results, pending label and pending suggestion; Details/polling never fetch",
    );
  } finally {
    await ui.destroy();
  }
});

/** @param {string} query */
function selectionFor(query) {
  const selection = new app.TestResultsSelection();
  selection.setQuery(
    app.selectionQuery(app.parseSearch(url(query).searchParams, families)),
  );
  return selection;
}

/** Actual SvGrid accessible checkboxes, not custom stand-ins.
 * @param {import('happy-dom').HTMLElement} target */
function selectionHeader(target) {
  const header = target.querySelector(
    'button[role="checkbox"][aria-label="Select all rows"]',
  );
  assert.ok(header);
  return /** @type {import('happy-dom').HTMLButtonElement} */ (header);
}

/** @param {import('happy-dom').HTMLElement} target @param {number} id */
function selectionRow(target, id) {
  const row = Array.from(target.querySelectorAll("tbody tr")).find(
    (row) =>
      row.querySelector('[data-col-id="testCase"]')?.textContent.trim() ===
      `case ${id}`,
  );
  const checkbox = row?.querySelector(
    'button[role="checkbox"][aria-label="Select row"]',
  );
  assert.ok(checkbox, `Missing real grid checkbox for result ${id}`);
  return /** @type {import('happy-dom').HTMLButtonElement} */ (checkbox);
}

/** @param {import('happy-dom').HTMLElement} target */
function allMatchesCheckbox(target) {
  return /** @type {import('happy-dom').HTMLInputElement | null} */ (
    target.querySelector('.selection-summary input[type="checkbox"]')
  );
}

/** @param {import('happy-dom').HTMLElement} target @param {string} value */
async function localSearch(target, value) {
  return enter(target, ".sv-grid-global-filter input", value);
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
            entry: "tests/test-results-search-entry.svelte.js",
            formats: ["es"],
          },
          rolldownOptions: { output: { codeSplitting: false } },
        },
      })
    )
  );
  const bundle = built[0].output.find((item) => item.type === "chunk");
  assert.ok(bundle);
  browser = new Window({ url: url().href });
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
    "HTMLSelectElement",
    "HTMLTextAreaElement",
    "Event",
    "KeyboardEvent",
    "MouseEvent",
    "CSS",
    "ResizeObserver",
    "MutationObserver",
    "customElements",
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
  // Happy DOM does not implement the native Popover API used by Pragma. Model
  // its beforetoggle/toggle, declarative triggers and auto light-dismiss here.
  // Rendering can settle between beforetoggle and the native open transition;
  // focus on a still-closed popover must be ignored, just like the browser.
  // Real top-layer positioning and keyboard traversal still need browser QA.
  /** @type {Set<import('happy-dom').HTMLElement>} */
  const openPopovers = new Set();
  /** @param {string} name @param {string} oldState @param {string} newState */
  const toggleEvent = (name, oldState, newState) =>
    Object.assign(new browser.Event(name), { oldState, newState });
  /** @param {import('happy-dom').HTMLElement} element */
  function hidePopover(element) {
    if (!openPopovers.has(element)) return;
    element.dispatchEvent(toggleEvent("beforetoggle", "open", "closed"));
    openPopovers.delete(element);
    element.removeAttribute("data-test-open");
    element.dispatchEvent(toggleEvent("toggle", "open", "closed"));
  }
  /** @param {import('happy-dom').HTMLElement} element */
  function showPopover(element) {
    if (openPopovers.has(element)) return;
    element.dispatchEvent(toggleEvent("beforetoggle", "closed", "open"));
    for (const other of openPopovers) hidePopover(other);
    setTimeout(() => {
      if (!element.isConnected) return;
      openPopovers.add(element);
      element.setAttribute("data-test-open", "");
      element.dispatchEvent(toggleEvent("toggle", "closed", "open"));
    });
  }
  // Preserve the native methods' dynamic receivers; invoke only with .call().
  // eslint-disable-next-line @typescript-eslint/unbound-method
  const originalFocus = browser.HTMLElement.prototype.focus;
  // eslint-disable-next-line @typescript-eslint/unbound-method
  const originalMatches = browser.Element.prototype.matches;
  browser.Element.prototype.matches = function (selector) {
    if (selector === ":modal") return this.hasAttribute("data-test-modal");
    if (selector === ":popover-open")
      return this.hasAttribute("data-test-open");
    return originalMatches.call(this, selector);
  };
  browser.HTMLElement.prototype.focus = function () {
    const containingPopover = this.closest("[popover]");
    if (containingPopover && !containingPopover.hasAttribute("data-test-open"))
      return;
    originalFocus.call(this);
  };
  Object.defineProperties(browser.HTMLElement.prototype, {
    showPopover: {
      /** @this {import('happy-dom').HTMLElement} */
      value() {
        showPopover(this);
      },
    },
    hidePopover: {
      /** @this {import('happy-dom').HTMLElement} */
      value() {
        hidePopover(this);
      },
    },
  });
  // Happy DOM has no native dialog/Invoker Commands implementation. Model only
  // open/close/toggle/focus restoration; actual top-layer, Tab containment,
  // backdrop and layout are covered by the opt-in Chromium regression.
  /** @type {WeakMap<import('happy-dom').HTMLDialogElement, import('happy-dom').HTMLElement | null>} */
  const invokers = new WeakMap();
  browser.HTMLDialogElement.prototype.showModal = function () {
    if (this.open) return;
    invokers.set(
      this,
      /** @type {import('happy-dom').HTMLElement | null} */ (
        browser.document.activeElement
      ),
    );
    for (const popover of openPopovers) hidePopover(popover);
    this.open = true;
    this.setAttribute("data-test-modal", "");
    this.querySelector("button")?.focus();
    this.dispatchEvent(toggleEvent("toggle", "closed", "open"));
  };
  browser.HTMLDialogElement.prototype.close = function () {
    if (!this.open) return;
    this.open = false;
    this.removeAttribute("data-test-modal");
    const invoker = invokers.get(this);
    if (invoker?.isConnected) invoker.focus();
    this.dispatchEvent(toggleEvent("toggle", "open", "closed"));
    setTimeout(() => this.dispatchEvent(new browser.Event("close")));
  };
  browser.document.addEventListener("click", (event) => {
    const target = /** @type {import('happy-dom').Element} */ (event.target);
    const command = target.closest('button[command="close"]');
    if (command) {
      const dialog = browser.document.getElementById(
        command.getAttribute("commandfor") ?? "",
      );
      if (dialog instanceof browser.HTMLDialogElement) dialog.close();
    }
  });
  browser.document.addEventListener("click", (event) => {
    const target = /** @type {import('happy-dom').Element} */ (event.target);
    const trigger =
      /** @type {import('happy-dom').HTMLButtonElement | null} */ (
        target.closest("button[popovertarget]")
      );
    const popover = trigger
      ? browser.document.getElementById(
          trigger.getAttribute("popovertarget") ?? "",
        )
      : null;
    if (popover) {
      trigger?.focus();
      if (openPopovers.has(popover)) hidePopover(popover);
      else showPopover(popover);
    } else {
      for (const open of openPopovers)
        if (!open.contains(target)) hidePopover(open);
    }
  });
  // Model the browser's default Enter activation for native buttons.
  browser.document.addEventListener(
    "keydown",
    (event) => {
      const target = /** @type {import('happy-dom').HTMLButtonElement} */ (
        event.target
      );
      queueMicrotask(() => {
        if (
          event.key === "Enter" &&
          !event.defaultPrevented &&
          target.matches("button")
        )
          target.click();
        if (event.key === "Escape" && !event.defaultPrevented) {
          const dialog =
            /** @type {import('happy-dom').HTMLDialogElement | null} */ (
              browser.document.querySelector("dialog[open]")
            );
          dialog?.close();
        }
      });
    },
    true,
  );
  // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
  app = /** @type {typeof import('./test-results-search-entry.svelte.js')} */ (
    /** @type {unknown} */ (
      await import(
        `data:text/javascript;base64,${Buffer.from(bundle.code).toString("base64")}`
      )
    )
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

void test("family display names capitalize only the first route-name character, independently of API names", () => {
  for (const [name, expected] of [
    ["configured-route", "Configured-route"],
    ["customWidgets", "CustomWidgets"],
    ["aPI-bundles", "API-bundles"],
    ["Already-Mixed", "Already-Mixed"],
    [" spaced", " spaced"],
    ["", ""],
  ]) {
    const family = { ...families[0], name, api_name: "unrelated-api-family" };
    assert.equal(app.familyDisplayName(family), expected);
    assert.equal(family.name, name);
    assert.equal(family.api_name, "unrelated-api-family");
  }
});

void test("all eight list filters match OpenAPI names, repeated parameters, and backend exact-match contracts", async () => {
  // JSON.parse's untyped return is narrowed to the schema fragment under test.
  // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
  const schema =
    /** @type {{ paths: Record<string, {get: {parameters: {name: string; schema: {anyOf?: {type?: string}[]} }[]}}> }} */ (
      JSON.parse(
        await readFile(
          new URL("../../../backend/schemata/openapi.json", import.meta.url),
          "utf8",
        ),
      )
    );
  const parameters = schema.paths["/v1/test-results"].get.parameters;
  const matching = await readFile(
    new URL(
      "../../../backend/test_observer/controllers/test_results/filter_test_results.py",
      import.meta.url,
    ),
    "utf8",
  );
  for (const key of ORIGINAL_LIST_FILTERS) {
    assert.ok(
      parameters
        .find((parameter) => parameter.name === key)
        ?.schema.anyOf?.some((type) => type.type === "array"),
      key,
    );
    assert.match(matching, new RegExp(`\\.in_\\(filters\\.${key}\\)`));
  }
  const params = new URLSearchParams(
    "families=snap&test_result_statuses=FAILED,PASSED&test_result_statuses=SKIPPED&artefacts=alpha, beta&artefacts=alpha&artefact_versions=1%2B2&artefact_tracks=stable&environments=lab&test_plans=smoke&test_cases=case",
  );
  const query = app.parseSearch(params, families);
  assert.deepEqual(query.problems, []);
  assert.deepEqual(query.filters.test_result_statuses, [
    "FAILED",
    "PASSED",
    "SKIPPED",
  ]);
  assert.deepEqual(query.filters.artefacts, ["alpha", "beta"]);
  assert.equal(query.hasFilters, true);
  const apiParams = app.searchParams(query.filters, 2, 4);
  assert.deepEqual(apiParams.getAll("artefacts"), ["alpha", "beta"]);
  assert.deepEqual(apiParams.getAll("test_result_statuses"), [
    "FAILED",
    "PASSED",
    "SKIPPED",
  ]);
  assert.equal(apiParams.get("artefact_versions"), "1+2");
  assert.equal(apiParams.get("offset"), "4");
  assert.deepEqual(app.parseSearch(apiParams, families).filters, query.filters);
  assert.equal(
    app.viewRunPath(
      /** @type {import('../src/lib/testResultsSearch').SearchResult} */ (
        /** @type {unknown} */ (result())
      ),
      families,
      "/other/base",
    ),
    "/other/base/configured-route/42?testExecutionId=7&testResultId=1",
  );
  assert.equal(
    app.viewRunPath(
      /** @type {import('../src/lib/testResultsSearch').SearchResult} */ (
        /** @type {unknown} */ (result())
      ),
      [],
      "",
    ),
    null,
  );
});

void test("unsupported and invalid URL filters block instead of silently broadening the search", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(response());
  };
  const store = new app.TestResultsSearchStore();
  for (const query of [
    "artefacts=ok&test_execution_statuses=FAILED",
    "families=unknown",
    "test_result_statuses=UNKNOWN",
    "artefacts=ok&offset=-1",
    "artefacts=ok&limit=0",
    "artefacts=ok&limit=1&limit=2",
    "artefacts=ok&offset=9007199254740992",
  ]) {
    const applied = app.parseSearch(url(query).searchParams, families);
    assert.ok(applied.problems.length, query);
    await store.search(applied);
    assert.equal(store.response, null);
    assert.equal(store.loading, false);
  }
  for (const query of [
    "",
    "limit=2&offset=3",
    "artefacts= , ",
    "view=invalid",
    "view=invalid&limit=2&offset=3",
  ]) {
    await store.search(app.parseSearch(url(query).searchParams, families));
  }
  assert.equal(calls, 0);
});

void test("search uses configured API defaults and replaces pages, safely ending on short or empty responses", async () => {
  /** @type {{url: URL; options: RequestInit}[]} */
  const calls = [];
  const replies = [
    response([1, 2], 9, 2),
    response([3], 9, 2, 2),
    response([], 9, 2, 4),
  ];
  globalThis.fetch = (input, options = {}) => {
    calls.push({
      url: new URL(input instanceof Request ? input.url : input),
      options,
    });
    return Promise.resolve(replies.shift() ?? response());
  };
  const store = new app.TestResultsSearchStore();
  for (const offset of [0, 2, 4]) {
    await store.search(
      app.parseSearch(
        url(`artefacts=one,two&test_cases=case&limit=2&offset=${offset}`)
          .searchParams,
        families,
      ),
    );
    assert.equal(store.response?.offset, offset);
    assert.deepEqual(
      store.response.test_results.map((r) => r.test_result.id),
      offset === 0 ? [1, 2] : offset === 2 ? [3] : [],
    );
  }
  assert.equal(calls.length, 3);
  for (const call of calls) {
    assert.equal(call.url.pathname, "/v1/test-results");
    assert.deepEqual(call.url.searchParams.getAll("artefacts"), ["one", "two"]);
    assert.equal(call.options.credentials, "include");
    assert.equal(new Headers(call.options.headers).get("X-CSRF-Token"), "1");
    assert.equal(call.options.method ?? "GET", "GET");
  }
});

void test("typed date-only, false-only and none-stage searches fetch, while every malformed condition blocks the store", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(response());
  };
  const store = new app.TestResultsSearchStore();
  for (const input of [
    "from_date=2026-01-01T00:00:00Z",
    "until_date=2026-01-01T00:00:00Z",
    "artefact_is_archived=false",
    "rerun_is_requested=false",
    "execution_is_latest=false",
    "artefact_stages=",
    "issues=none",
    "assignee_ids=1,2",
  ]) {
    await store.search(app.parseSearch(url(input).searchParams, families));
    assert.ok(store.response, input);
  }
  assert.equal(calls.length, 8);
  assert.deepEqual(calls.at(-1)?.searchParams.getAll("reviewer_ids"), [
    "1",
    "2",
  ]);
  assert.equal(calls.at(-1)?.searchParams.has("assignee_ids"), false);
  for (const input of [
    "issues=1,any",
    "reviewer_ids=9007199254740992",
    "execution_metadata=broken",
    "artefact_is_archived=maybe",
    "rerun_is_requested=",
    "execution_is_latest=null",
    "from_date=2026-02-30T00:00:00Z",
    "until_date=2026-01-01",
    "from_date=2026-02-01T00:00:00Z&until_date=2026-01-01T00:00:00Z",
  ]) {
    await store.search(
      app.parseSearch(url(`artefacts=valid&${input}`).searchParams, families),
    );
    assert.equal(store.response, null, input);
    assert.equal(store.loading, false, input);
  }
  assert.equal(
    calls.length,
    8,
    "partial valid filters never make an invalid search eligible",
  );
});

void test("old results, errors and session checks cannot replace a newer query or a cleared search", async () => {
  for (const oldStatus of [200, 401, 403, 500]) {
    const old = deferred();
    let sessionCalls = 0;
    globalThis.fetch = (input) => {
      const request = new URL(input instanceof Request ? input.url : input);
      if (request.pathname.endsWith("/users/me")) {
        sessionCalls++;
        return Promise.resolve(json(null));
      }
      return request.searchParams.get("artefacts") === "old"
        ? old.promise
        : Promise.resolve(response([2]));
    };
    const store = new app.TestResultsSearchStore();
    const older = store.search(
      app.parseSearch(url("artefacts=old").searchParams, families),
    );
    await store.search(
      app.parseSearch(url("artefacts=new").searchParams, families),
    );
    old.resolve(oldStatus === 200 ? response([1]) : json({}, oldStatus));
    await older;
    assert.equal(store.response?.test_results[0]?.test_result.id, 2);
    assert.equal(store.error, null);
    assert.equal(store.accessError, null);
    assert.equal(sessionCalls, 0);
  }
  const session = deferred();
  let checking = false;
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    if (request.pathname.endsWith("/users/me")) {
      checking = true;
      return session.promise;
    }
    return Promise.resolve(json({}, 403));
  };
  const store = new app.TestResultsSearchStore();
  const older = store.search(
    app.parseSearch(url("artefacts=old").searchParams, families),
  );
  await flush();
  assert.equal(checking, true);
  await store.search(app.parseSearch(url().searchParams, families));
  session.resolve(json({ id: 5, teams: [], is_admin: false }));
  await older;
  assert.equal(store.response, null);
  assert.equal(store.accessError, null);
  assert.equal(store.loading, false);
});

void test("auth revalidation accurately distinguishes logged out, permission denied, and inconclusive sessions", async () => {
  for (const [pageStatus, sessionBody, sessionStatus, expected] of [
    [401, null, 200, "requiresLogin"],
    [403, {}, 401, "requiresLogin"],
    [403, { id: 5, teams: [], is_admin: false }, 200, "forbidden"],
    [401, { id: 5, teams: [], is_admin: false }, 200, "requiresLogin"],
    [403, {}, 503, "sessionCheckFailed"],
  ]) {
    globalThis.fetch = (input) =>
      Promise.resolve(
        new URL(input instanceof Request ? input.url : input).pathname.endsWith(
          "/users/me",
        )
          ? json(sessionBody, /** @type {number} */ (sessionStatus))
          : json({}, /** @type {number} */ (pageStatus)),
      );
    const store = new app.TestResultsSearchStore();
    await store.search(
      app.parseSearch(url("artefacts=one").searchParams, families),
    );
    assert.equal(store.accessError, expected);
    assert.equal(store.loading, false);
    assert.equal(store.response, null);
  }
});

void test("cancelled session body parsing cannot overwrite the shared user cache", async () => {
  const user = {
    id: 99,
    teams: [],
    is_admin: false,
    name: "Current user",
    email: "user@example.test",
    launchpad_handle: null,
  };
  await app.userStore.refresh(() => Promise.resolve(json(user)));
  const session = deferred();
  let readingBody = false;
  const oldResponse = json(null);
  oldResponse.json = async () => {
    readingBody = true;
    const response = await session.promise;
    // eslint-disable-next-line @typescript-eslint/no-unsafe-return
    return response.json();
  };
  globalThis.fetch = (input) =>
    Promise.resolve(
      new URL(input instanceof Request ? input.url : input).pathname.endsWith(
        "/users/me",
      )
        ? oldResponse
        : json({}, 403),
    );
  const store = new app.TestResultsSearchStore();
  const older = store.search(
    app.parseSearch(url("artefacts=old").searchParams, families),
  );
  await flush();
  assert.equal(readingBody, true);
  await store.search(app.parseSearch(url().searchParams, families));
  session.resolve(json(null));
  await older;
  assert.equal(app.userStore.current?.id, user.id);
  assert.equal(store.accessError, null);
});

/** @param {string} [query] */
function mounted(query = "") {
  const target = browser.document.createElement("div");
  browser.document.body.append(target);
  const handle = app.mountSearch(
    /** @type {HTMLElement} */ (/** @type {unknown} */ (target)),
    url(query),
    families,
  );
  return {
    target,
    handle,
    destroy: async () => {
      await handle.destroy();
      target.remove();
    },
  };
}

/** @param {import('happy-dom').HTMLElement} target @param {string} text */
function button(target, text) {
  const found = Array.from(target.querySelectorAll("button")).find((b) =>
    b.textContent.includes(text),
  );
  assert.ok(found, `Missing button ${text}`);
  return found;
}

/** @param {import('happy-dom').HTMLElement} target */
function panel(target) {
  const found = target.querySelector(".condition-popover .panel");
  assert.ok(found, "An anchored picker/editor must be open");
  return /** @type {import('happy-dom').HTMLElement} */ (found);
}

/** @param {import('happy-dom').HTMLElement} target @param {string} selector @param {string} value */
async function enter(target, selector, value) {
  const input = /** @type {import('happy-dom').HTMLInputElement | null} */ (
    target.querySelector(selector)
  );
  assert.ok(input);
  input.value = value;
  input.dispatchEvent(new browser.Event("input", { bubbles: true }));
  await flush();
  return input;
}

/** Use the explicit manual path when these tests are about confirmed exact
 * conditions, rather than unconfirmed suggestion query text. Existing comma
 * links still restore; new lookup values are added one at a time deliberately.
 * @param {import('happy-dom').HTMLElement} target
 * @param {string} selector @param {string} value
 */
async function replaceExact(target, selector, value) {
  const editor =
    target.closest(".panel") ?? target.querySelector(".panel") ?? target;
  const exact = Array.from(editor.querySelectorAll("button")).find((b) =>
    b.textContent.includes("Add exact"),
  );
  if (!exact) return enter(target, selector, value);
  for (const remove of editor.querySelectorAll("button"))
    if (remove.getAttribute("aria-label")?.startsWith("Remove selected "))
      remove.click();
  await flush();
  let input;
  for (const part of value
    .split(",")
    .map((v) => v.trim())
    .filter(Boolean)) {
    input = await enter(target, selector, part);
    exact.click();
    await flush();
  }
  assert.ok(input);
  return input;
}

/** @param {import('happy-dom').HTMLElement} target @param {string} label */
async function chooseFilter(target, label) {
  button(target, "+ Add filter").click();
  await flush();
  button(panel(target), label).click();
  await flush();
}

/** @param {import('happy-dom').HTMLElement} target */
async function confirmEditor(target) {
  const form = panel(target).querySelector("form");
  assert.ok(form);
  form.dispatchEvent(
    new browser.Event("submit", { bubbles: true, cancelable: true }),
  );
  await flush();
  if (!target.querySelector(".panel"))
    assert.ok(
      browser.document.activeElement.matches(".chip-trigger"),
      "confirming an editor returns focus to its chip",
    );
}

/** @param {import('happy-dom').HTMLElement} target @param {string} label */
function chip(target, label) {
  const found = Array.from(target.querySelectorAll("button.chip-trigger")).find(
    (element) =>
      element.getAttribute("aria-label")?.startsWith(`Edit ${label}:`),
  );
  assert.ok(found, `Missing ${label} chip`);
  return /** @type {import('happy-dom').HTMLButtonElement} */ (found);
}

void test("mounted restored typed conditions become chips and survive edits, view changes, pagination, history and clear", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    if (request.pathname.includes("/users/"))
      return Promise.resolve(
        json({
          id: Number(request.pathname.split("/").at(-1)),
          name: "Reviewer",
        }),
      );
    calls.push(request);
    const limit = Number(request.searchParams.get("limit") ?? 50);
    return Promise.resolve(
      response(
        Array.from({ length: limit }, (_, i) => i + 1),
        200,
        limit,
      ),
    );
  };
  const params = new URLSearchParams({
    artefacts: "old",
    artefact_stages: "",
    artefact_is_archived: "false",
    rerun_is_requested: "false",
    execution_is_latest: "true",
    issues: "any",
    assignee_ids: "2,3",
    template_ids: "template-1,template-2",
    execution_metadata: `${Buffer.from("c:at,🐧").toString("base64")}:${Buffer.from("one,two:三").toString("base64")}`,
    from_date: "2024-02-29T00:00:00.123456Z",
    until_date: "2026-10-20T00:00:00+01:00",
    limit: "2",
  });
  const ui = mounted(params.toString());
  try {
    await flush();
    assert.equal(calls.length, 1);
    assert.doesNotMatch(
      ui.target.textContent,
      /Additional URL filters|not available yet/,
    );
    assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 11);
    assert.equal(
      chip(ui.target, "Artefact Stage").title,
      "Artefact Stage: (none)",
    );
    assert.equal(
      chip(ui.target, "Archived").title,
      "Archived: Non archived only",
    );
    assert.match(chip(ui.target, "Metadata").title, /c:at,🐧.*one,two:三/);
    chip(ui.target, "Artefact").click();
    await flush();
    await replaceExact(ui.target, 'input[name="artefacts"]', "new");
    await confirmEditor(ui.target);
    const viewOnly = new URL(ui.handle.currentUrl);
    viewOnly.searchParams.set("view", "invalid-view");
    ui.handle.restore(viewOnly);
    await flush();
    assert.equal(
      calls.length,
      1,
      "view-only replacement cannot refetch or discard drafts",
    );
    assert.equal(chip(ui.target, "Artefact").title, "Artefact: new");
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls.length, 2);
    assert.equal(calls[1].searchParams.get("artefacts"), "new");
    assert.equal(calls[1].searchParams.has("view"), false);
    assert.deepEqual(calls[1].searchParams.getAll("reviewer_ids"), ["2", "3"]);
    assert.equal(calls[1].searchParams.has("assignee_ids"), false);
    for (const key of [
      "artefact_stages",
      "artefact_is_archived",
      "rerun_is_requested",
      "execution_is_latest",
      "issues",
      "execution_metadata",
      "from_date",
      "until_date",
    ])
      assert.deepEqual(
        calls[1].searchParams.getAll(key),
        params.getAll(key),
        key,
      );
    assert.deepEqual(calls[1].searchParams.getAll("template_ids"), [
      "template-1",
      "template-2",
    ]);
    button(ui.target, "Next page").click();
    await flush();
    assert.equal(calls.length, 3);
    assert.equal(calls[2].searchParams.get("offset"), "50");
    assert.deepEqual(calls[2].searchParams.getAll("reviewer_ids"), ["2", "3"]);
    assert.deepEqual(
      calls[2].searchParams.getAll("execution_metadata"),
      calls[1].searchParams.getAll("execution_metadata"),
    );
    ui.handle.restore(url(params.toString()));
    await flush();
    assert.equal(calls.length, 4);
    assert.equal(chip(ui.target, "Artefact").title, "Artefact: old");
    // A date alone is a meaningful Flutter search, not an unfiltered request.
    ui.handle.restore(url("until_date=2026-01-01T00:00:00Z"));
    await flush();
    assert.equal(calls.length, 5);
    assert.equal(chip(ui.target, "Until").title, "Until: 2026-01-01T00:00:00Z");
    assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 1);
    button(ui.target, "Clear all").click();
    await flush();
    assert.equal(ui.handle.currentUrl.search, "");
    assert.equal(calls.length, 5);
    assert.doesNotMatch(ui.target.textContent, /Additional URL filters/);
  } finally {
    await ui.destroy();
  }
});

void test("mounted invalid URL-only constraints visibly block and cannot be silently removed by unrelated Search edits", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(response());
  };
  for (const invalid of [
    "issues=any,1",
    "reviewer_ids=bad",
    "execution_metadata=broken",
    "from_date=2026-02-30T00:00:00Z",
    "from_date=2026-01-01T00:00:00.0000001Z",
    "artefact_is_archived=bad",
    "test_result_statuses=BAD",
    "families=unknown",
    "limit=0",
    "offset=-1",
    "unknown=blocked",
  ]) {
    const ui = mounted(`artefacts=old&${invalid}`);
    try {
      await flush();
      assert.match(
        ui.target.querySelector('[role="alert"]')?.textContent ?? "",
        /Search not applied/,
      );
      chip(ui.target, "Artefact").click();
      await flush();
      await replaceExact(ui.target, 'input[name="artefacts"]', "new");
      await confirmEditor(ui.target);
      button(ui.target, "Search").click();
      await flush();
      assert.match(
        ui.target.querySelector('[role="alert"]')?.textContent ?? "",
        /No request was sent/,
      );
      const original = new URLSearchParams(invalid);
      for (const [key, value] of original)
        assert.equal(ui.handle.currentUrl.searchParams.get(key), value);
      assert.equal(calls, 0, invalid);
      button(ui.target, "Clear all").click();
      await flush();
      assert.equal(ui.target.querySelector('[role="alert"]'), null);
      assert.equal(calls, 0);
    } finally {
      await ui.destroy();
    }
  }
});

void test("mounted sub-microsecond lower bounds visibly block without fetching, and representable bounds retain exact microsecond ordering", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(response());
  };
  const unrepresentable = "2026-01-01T00:00:00.0000001Z";
  const ui = mounted(`from_date=${unrepresentable}`);
  try {
    await flush();
    const alert = ui.target.querySelector('[role="alert"]');
    assert.match(alert?.textContent ?? "", /Invalid from_date:.*microsecond/);
    assert.match(alert?.textContent ?? "", /No request was sent/);
    assert.equal(calls.length, 0);
    button(ui.target, "Search").click();
    await flush();
    assert.equal(
      ui.handle.currentUrl.searchParams.get("from_date"),
      unrepresentable,
    );
    assert.equal(
      calls.length,
      0,
      "Search cannot replace an invalid lower bound with a truncated or unfiltered request",
    );

    ui.handle.restore(
      url(
        "from_date=2026-01-01T00:00:00.000001Z&until_date=2026-01-01T00:00:00.000000Z",
      ),
    );
    await flush();
    assert.match(
      ui.target.querySelector('[role="alert"]')?.textContent ?? "",
      /Invalid date range/,
    );
    assert.equal(
      calls.length,
      0,
      "six-digit inverted bounds must not collapse to the same millisecond",
    );

    ui.handle.restore(
      url(
        "from_date=2026-01-01T00:00:00.000001Z&until_date=2026-01-01T00:00:00.000002000Z",
      ),
    );
    await flush();
    assert.equal(ui.target.querySelector('[role="alert"]'), null);
    assert.equal(calls.length, 1);
    assert.equal(
      calls[0].searchParams.get("from_date"),
      "2026-01-01T00:00:00.000001Z",
    );
    assert.equal(
      calls[0].searchParams.get("until_date"),
      "2026-01-01T00:00:00.000002000Z",
    );
  } finally {
    await ui.destroy();
  }
});

void test("search actions use dense Pragma buttons with separate icon and text slots", async () => {
  const ui = mounted("view=invalid");
  try {
    await flush();
    const search = button(ui.target, "Search");
    assert.ok(search.querySelector(".button-content > .icon.left svg"));
    assert.equal(search.querySelector(".button-content > .text svg"), null);
    assert.equal(
      search.querySelector(".button-content > .text")?.textContent.trim(),
      "Search",
    );
    for (const label of [
      "+ Add filter",
      "Search",
      "Clear all",
      "Reset table view",
    ])
      assert.ok(button(ui.target, label).classList.contains("dense"), label);
  } finally {
    await ui.destroy();
  }
});

void test("mounted controls apply exact drafts, render SvGrid context and accessible base-aware links, restore history and clear", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(response([1]));
  };
  const ui = mounted();
  try {
    await flush();
    assert.match(ui.target.textContent, /Choose at least one filter/);
    assert.equal(calls.length, 0);
    assert.equal(ui.target.querySelector("input"), null);
    assert.equal(ui.target.querySelector("fieldset"), null);
    await chooseFilter(ui.target, "Artefact");
    const input = await replaceExact(
      ui.target,
      'input[name="artefacts"]',
      "one, two",
    );
    assert.ok(ui.target.querySelector(`label[for="${input.id}"]`));
    await confirmEditor(ui.target);
    await chooseFilter(ui.target, "Family");
    const family = /** @type {import('happy-dom').HTMLInputElement | null} */ (
      ui.target.querySelector('input[value="snap"]')
    );
    assert.ok(family);
    assert.equal(
      family.closest("label")?.textContent.trim(),
      "Configured-route",
    );
    family.click();
    await flush();
    await confirmEditor(ui.target);
    assert.equal(calls.length, 0, "draft edits do not fetch before applying");
    assert.match(ui.target.textContent, /Changes not applied/);
    assert.match(chip(ui.target, "Family").textContent, /Configured-route/);
    button(ui.target, "Search").click();
    await flush();
    assert.deepEqual(calls[0]?.searchParams.getAll("artefacts"), [
      "one",
      "two",
    ]);
    assert.equal(calls[0]?.searchParams.get("families"), "snap");
    assert.equal(ui.handle.history.length, 2);
    assert.ok(
      ui.target.querySelector(".sv-grid-root"),
      "actual SvGrid must mount",
    );
    assert.match(
      ui.target.textContent,
      /1 matching test results on the server/,
    );
    assert.match(ui.target.textContent, /only this loaded page/);
    assert.equal(
      ui.target
        .querySelector('tbody td[data-col-id="family"]')
        ?.textContent.trim(),
      "Configured-route",
    );
    for (const text of [
      "example artefact",
      "case 1",
      "FAILED",
      "1.2",
      "stable",
      "test lab",
      "smoke",
    ])
      assert.ok(ui.target.textContent.includes(text), text);
    const link = /** @type {import('happy-dom').HTMLAnchorElement | null} */ (
      ui.target.querySelector('a[aria-label="View Run for case 1"]')
    );
    assert.ok(link, ui.target.innerHTML);
    assert.equal(
      link.getAttribute("href"),
      "/custom/base/configured-route/42?testExecutionId=7&testResultId=1",
    );
    link.focus();
    assert.equal(browser.document.activeElement, link);
    const applied = ui.handle.history[1];
    ui.handle.restore(url("test_cases=restored"));
    await flush();
    assert.equal(calls.at(-1)?.searchParams.get("test_cases"), "restored");
    ui.handle.restore(applied);
    await flush();
    assert.equal(chip(ui.target, "Artefact").title, "Artefact: one, two");
    assert.deepEqual(calls.at(-1)?.searchParams.getAll("artefacts"), [
      "one",
      "two",
    ]);
    button(ui.target, "Clear all").click();
    await flush();
    assert.equal(ui.target.querySelector(".sv-grid-root"), null);
    assert.match(ui.target.textContent, /Choose at least one filter/);
    assert.equal(calls.length, 3, "clear must not fetch unfiltered results");
  } finally {
    await ui.destroy();
  }
});

void test("native post-opening focus works for pointer and Enter on picker, text and checkbox chips", async () => {
  globalThis.fetch = () => Promise.resolve(response());
  for (const [query, label] of [
    ["", ""],
    ["artefacts=known-value", "Artefact"],
    ["test_result_statuses=FAILED", "Status"],
    ["families=snap", "Family"],
  ]) {
    for (const mode of ["pointer", "Enter"]) {
      const ui = mounted(query);
      try {
        await flush();
        const trigger = label
          ? chip(ui.target, label)
          : button(ui.target, "+ Add filter");
        trigger.focus();
        if (mode === "pointer") trigger.click();
        else
          trigger.dispatchEvent(
            new browser.KeyboardEvent("keydown", {
              key: "Enter",
              bubbles: true,
              cancelable: true,
            }),
          );
        await flush();
        const input = panel(ui.target).querySelector("input");
        assert.ok(input);
        assert.ok(
          browser.document.activeElement === input,
          `${mode} must focus ${label || "picker"} after native opening`,
        );
        if (!label) {
          input.value = "environ";
          input.dispatchEvent(new browser.Event("input", { bubbles: true }));
          await flush();
          assert.equal(
            panel(ui.target).querySelectorAll("li button").length,
            1,
          );
        }
        input.dispatchEvent(
          new browser.KeyboardEvent("keydown", {
            key: "Escape",
            bubbles: true,
            cancelable: true,
          }),
        );
        await flush();
        assert.equal(ui.target.querySelector(".panel"), null);
        assert.ok(
          browser.document.activeElement === trigger,
          "Escape must return focus to the opener",
        );
      } finally {
        await ui.destroy();
      }
    }
  }
});

void test("open overlays use visible viewport bounds rather than tall documents and follow resize/scroll", async () => {
  globalThis.fetch = () => Promise.resolve(response());
  const ui = mounted("test_result_statuses=FAILED");
  const originalWidth = browser.innerWidth;
  const originalHeight = browser.innerHeight;
  const documentHeight = Object.getOwnPropertyDescriptor(
    browser.document.documentElement,
    "scrollHeight",
  );
  Object.defineProperty(browser.document.documentElement, "scrollHeight", {
    configurable: true,
    value: 1004,
  });
  try {
    await flush();
    const trigger = button(ui.target, "+ Add filter");
    trigger.click();
    await flush();
    const content = panel(ui.target);
    const overlay = /** @type {import('happy-dom').HTMLElement | null} */ (
      content.parentElement
    );
    assert.ok(overlay);
    // Happy DOM has no layout; supply the real QA geometry and verify the
    // resulting viewport constraints, leaving scrollbar reachability to browser QA.
    content.getBoundingClientRect = () => new browser.DOMRect(0, 0, 368, 375);
    overlay.getBoundingClientRect = () => new browser.DOMRect(0, 0, 368, 375);
    let anchorY = 132;
    trigger.getBoundingClientRect = () =>
      new browser.DOMRect(browser.innerWidth - 150, anchorY, 108, 26);
    for (const [width, height] of [
      [800, 480],
      [1440, 500],
      [800, 360],
    ]) {
      browser.happyDOM.setViewport({ width, height });
      browser.dispatchEvent(new browser.Event("resize"));
      await flush();
      const top = Number.parseFloat(overlay.style.top);
      const left = Number.parseFloat(overlay.style.left);
      const maxHeight = Number.parseFloat(overlay.style.maxHeight);
      assert.ok(
        top >= 16 && top + Math.min(375, maxHeight) <= height - 16,
        `${width}x${height} overlay must fit vertically`,
      );
      assert.ok(
        left >= 16 && left + 368 <= width - 16,
        `${width}x${height} overlay must fit horizontally`,
      );
      assert.ok(
        maxHeight < height - 32,
        "height must account for its anchor, not just the full viewport",
      );
    }
    const previousTop = Number.parseFloat(overlay.style.top);
    anchorY = 20;
    browser.document.dispatchEvent(new browser.Event("scroll"));
    await flush();
    assert.ok(
      Number.parseFloat(overlay.style.top) < previousTop,
      "scrolling must retain the trigger anchor",
    );
    assert.ok(
      browser.document.activeElement === content.querySelector("input"),
      "repositioning must not disturb input focus",
    );
  } finally {
    await ui.destroy();
    browser.happyDOM.setViewport({
      width: originalWidth,
      height: originalHeight,
    });
    if (documentHeight)
      Object.defineProperty(
        browser.document.documentElement,
        "scrollHeight",
        documentHeight,
      );
    else
      Reflect.deleteProperty(browser.document.documentElement, "scrollHeight");
  }
});

void test("searchable picker offers all eighteen unused fields and never creates an empty chip", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(response());
  };
  const ui = mounted();
  try {
    await flush();
    button(ui.target, "+ Add filter").click();
    await flush();
    const picker = panel(ui.target);
    assert.equal(
      picker.closest('[role="dialog"]')?.getAttribute("aria-label"),
      "Add filter",
    );
    assert.ok(
      browser.document.activeElement === picker.querySelector("input"),
      "opening must focus the picker input after the native transition",
    );
    assert.deepEqual(
      Array.from(picker.querySelectorAll("li button")).map((item) =>
        item.textContent.trim(),
      ),
      [
        "Family",
        "Status",
        "Issues",
        "Reviewers",
        "Artefact",
        "Artefact Version",
        "Artefact Stage",
        "Artefact Track",
        "Archived",
        "Rerun Requested",
        "Execution Version",
        "Environment",
        "Test Case",
        "Test Plan",
        "Template ID",
        "Metadata",
        "From",
        "Until",
      ],
    );
    await enter(picker, 'input[type="search"]', "  TEST  ");
    assert.equal(picker.querySelectorAll("li button").length, 2);
    await enter(picker, 'input[type="search"]', "not-a-filter");
    assert.match(picker.textContent, /No matching filters/);
    await enter(picker, 'input[type="search"]', "artefact");
    button(picker, "Artefact").click();
    await flush();
    assert.equal(button(panel(ui.target), "Add filter").disabled, true);
    await enter(ui.target, 'input[name="artefacts"]', " , , ");
    await confirmEditor(ui.target);
    assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 0);
    assert.equal(calls, 0);
    await replaceExact(
      ui.target,
      'input[name="artefacts"]',
      "alpha, beta,alpha",
    );
    await confirmEditor(ui.target);
    const condition = chip(ui.target, "Artefact");
    assert.equal(browser.document.activeElement, condition);
    assert.equal(
      condition.querySelector("button"),
      null,
      "chip edit and remove cannot be nested buttons",
    );
    assert.match(condition.textContent, /alpha \+1/);
    assert.equal(condition.title, "Artefact: alpha, beta");
    button(ui.target, "+ Add filter").click();
    await flush();
    await enter(panel(ui.target), 'input[type="search"]', "artefact");
    assert.equal(
      panel(ui.target).querySelectorAll("li button").length,
      3,
      "an existing field cannot be added twice",
    );
    button(panel(ui.target), "Cancel").click();
    await flush();
    const remove = /** @type {import('happy-dom').HTMLButtonElement | null} */ (
      ui.target.querySelector('button[aria-label="Remove Artefact filter"]')
    );
    assert.ok(remove);
    assert.ok(remove.querySelector(".button-content > .icon.left svg"));
    remove.click();
    await flush();
    assert.equal(
      browser.document.activeElement,
      button(ui.target, "+ Add filter"),
    );
    await chooseFilter(ui.target, "Artefact");
    assert.equal(ui.target.querySelector('input[name="artefacts"]')?.value, "");
    assert.equal(calls, 0);
  } finally {
    await ui.destroy();
  }
});

void test("all eight chip editors preserve configured families, checkbox statuses and exact comma values until Search", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(response());
  };
  const ui = mounted();
  try {
    await flush();
    await chooseFilter(ui.target, "Family");
    for (const family of families) {
      const checkbox =
        /** @type {import('happy-dom').HTMLInputElement | null} */ (
          panel(ui.target).querySelector(`input[value="${family.api_name}"]`)
        );
      assert.ok(checkbox);
      checkbox.click();
    }
    await flush();
    await confirmEditor(ui.target);
    assert.match(
      chip(ui.target, "Family").title,
      /Configured-route, Another-route/,
    );
    await chooseFilter(ui.target, "Status");
    assert.equal(
      panel(ui.target).querySelectorAll('input[type="checkbox"]').length,
      3,
    );
    for (const status of ["PASSED", "FAILED", "SKIPPED"]) {
      const checkbox =
        /** @type {import('happy-dom').HTMLInputElement | null} */ (
          panel(ui.target).querySelector(`input[value="${status}"]`)
        );
      assert.ok(checkbox);
      checkbox.click();
    }
    await flush();
    await confirmEditor(ui.target);
    for (const [key, label] of [
      ["artefacts", "Artefact"],
      ["artefact_versions", "Artefact Version"],
      ["artefact_tracks", "Artefact Track"],
      ["environments", "Environment"],
      ["test_plans", "Test Plan"],
      ["test_cases", "Test Case"],
    ]) {
      await chooseFilter(ui.target, label);
      await replaceExact(
        ui.target,
        `input[name="${key}"]`,
        ` first ${key}, second+${key}, first ${key}, `,
      );
      await confirmEditor(ui.target);
      assert.equal(
        chip(ui.target, label).title,
        `${label}: first ${key}, second+${key}`,
      );
    }
    assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 8);
    button(ui.target, "+ Add filter").click();
    await flush();
    assert.equal(panel(ui.target).querySelectorAll("li").length, 10);
    button(panel(ui.target), "Cancel").click();
    await flush();
    assert.equal(calls.length, 0);
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls.length, 1);
    assert.deepEqual(
      calls[0].searchParams.getAll("families"),
      families.map((family) => family.api_name),
    );
    assert.deepEqual(calls[0].searchParams.getAll("test_result_statuses"), [
      "PASSED",
      "FAILED",
      "SKIPPED",
    ]);
    for (const key of ORIGINAL_LIST_FILTERS.slice(2))
      assert.deepEqual(calls[0].searchParams.getAll(key), [
        `first ${key}`,
        `second+${key}`,
      ]);
    assert.doesNotMatch(ui.target.textContent, /Changes not applied/);
    assert.match(ui.target.textContent, /Results for applied query/);
  } finally {
    await ui.destroy();
  }
});

void test("confirmed add/edit/remove drafts never fetch or replace applied results; Search applies the complete draft and resets pagination", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(response([1, 2], 20, 2, 2));
  };
  const ui = mounted("artefacts=old&test_cases=applied&limit=2&offset=2");
  try {
    await flush();
    chip(ui.target, "Artefact").click();
    await flush();
    assert.match(
      panel(ui.target).querySelector('[aria-label="Selected details"]')
        ?.textContent ?? "",
      /old/,
    );
    assert.equal(ui.target.querySelector('input[name="artefacts"]')?.value, "");
    await replaceExact(ui.target, 'input[name="artefacts"]', "new, second");
    await confirmEditor(ui.target);
    const remove = /** @type {import('happy-dom').HTMLButtonElement | null} */ (
      ui.target.querySelector('button[aria-label="Remove Test Case filter"]')
    );
    assert.ok(remove);
    remove.click();
    await flush();
    await chooseFilter(ui.target, "Environment");
    await replaceExact(ui.target, 'input[name="environments"]', "lab");
    await confirmEditor(ui.target);
    assert.equal(calls.length, 1);
    assert.equal(ui.handle.history.length, 1);
    assert.match(ui.target.textContent, /Changes not applied/);
    assert.match(ui.target.textContent, /Results for previous query/);
    assert.match(ui.target.textContent, /case 1/);
    assert.equal(button(ui.target, "Next page").disabled, true);
    assert.equal(button(ui.target, "Previous page").disabled, true);
    button(ui.target, "Next page").click();
    assert.equal(calls.length, 1);
    chip(ui.target, "Artefact").click();
    await flush();
    await enter(ui.target, 'input[name="artefacts"]', "unconfirmed");
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls.length, 2);
    assert.deepEqual(calls[1].searchParams.getAll("artefacts"), [
      "new",
      "second",
    ]);
    assert.equal(calls[1].searchParams.get("environments"), "lab");
    assert.equal(calls[1].searchParams.has("test_cases"), false);
    assert.equal(calls[1].searchParams.has("offset"), false);
    assert.equal(ui.target.querySelector(".panel"), null);
    assert.doesNotMatch(ui.target.textContent, /Changes not applied/);
    ui.handle.restore(url("artefacts=old&test_cases=applied&limit=2&offset=2"));
    await flush();
    chip(ui.target, "Artefact").click();
    await flush();
    await replaceExact(ui.target, 'input[name="artefacts"]', "old");
    await confirmEditor(ui.target);
    assert.doesNotMatch(ui.target.textContent, /Changes not applied/);
    assert.equal(button(ui.target, "Next page").disabled, false);
  } finally {
    await ui.destroy();
  }
});

void test("cancel, Escape, outside dismissal and switching popovers discard edits, with meaningful focus and intentional removal", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(response());
  };
  const ui = mounted("artefacts=original&test_result_statuses=FAILED");
  const outside = browser.document.createElement("button");
  outside.textContent = "Outside control";
  browser.document.body.append(outside);
  try {
    await flush();
    for (const dismissal of ["Cancel", "Escape", "outside"]) {
      const trigger = chip(ui.target, "Artefact");
      trigger.click();
      await flush();
      const input = await enter(
        ui.target,
        'input[name="artefacts"]',
        "discard me",
      );
      assert.ok(
        browser.document.activeElement === input,
        "opening must focus the editor input after the native transition",
      );
      const tab = new browser.KeyboardEvent("keydown", {
        key: "Tab",
        bubbles: true,
        cancelable: true,
      });
      input.dispatchEvent(tab);
      assert.equal(
        tab.defaultPrevented,
        false,
        "Tab must retain normal browser navigation",
      );
      if (dismissal === "Cancel") button(panel(ui.target), "Cancel").click();
      else if (dismissal === "Escape")
        input.dispatchEvent(
          new browser.KeyboardEvent("keydown", {
            key: "Escape",
            bubbles: true,
            cancelable: true,
          }),
        );
      else {
        outside.focus();
        outside.click();
      }
      await flush();
      assert.equal(ui.target.querySelector(".panel"), null);
      assert.equal(
        browser.document.activeElement,
        dismissal === "outside" ? outside : trigger,
      );
      assert.equal(chip(ui.target, "Artefact").title, "Artefact: original");
      assert.doesNotMatch(ui.target.textContent, /Changes not applied/);
    }
    chip(ui.target, "Status").click();
    await flush();
    const failed = /** @type {import('happy-dom').HTMLInputElement | null} */ (
      panel(ui.target).querySelector('input[value="FAILED"]')
    );
    assert.ok(failed?.checked);
    failed.click();
    await flush();
    assert.equal(button(panel(ui.target), "Save changes").disabled, true);
    assert.match(panel(ui.target).textContent, /or remove this filter/);
    button(ui.target, "+ Add filter").click();
    await flush();
    assert.equal(ui.target.querySelectorAll(".panel").length, 1);
    assert.match(panel(ui.target).textContent, /Find a filter/);
    button(panel(ui.target), "Cancel").click();
    await flush();
    chip(ui.target, "Status").click();
    await flush();
    assert.equal(
      panel(ui.target).querySelector('input[value="FAILED"]')?.checked,
      true,
      "switching does not save cleared checkboxes",
    );
    button(panel(ui.target), "Remove filter").click();
    await flush();
    assert.equal(
      browser.document.activeElement,
      button(ui.target, "+ Add filter"),
    );
    assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 1);
    assert.equal(calls, 1);
  } finally {
    outside.remove();
    await ui.destroy();
  }
});

void test("URL restoration resets open editors and restores full long/repeated/comma values; removing the final chip and clearing never fetch unfiltered data", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(response());
  };
  const long = "long-exact-artefact-name-".repeat(8);
  const applied = url(
    `artefacts=${long},second&artefacts=third&families=another-api-family`,
  );
  const ui = mounted(applied.search.slice(1));
  try {
    await flush();
    const trigger = chip(ui.target, "Artefact");
    assert.match(trigger.textContent, /\+2/);
    assert.equal(trigger.title, `Artefact: ${long}, second, third`);
    assert.equal(
      trigger.getAttribute("aria-label"),
      `Edit Artefact: ${long}, second, third`,
    );
    assert.equal(chip(ui.target, "Family").title, "Family: Another-route");
    trigger.click();
    await flush();
    assert.equal(ui.target.querySelector('input[name="artefacts"]')?.value, "");
    assert.deepEqual(
      Array.from(panel(ui.target).querySelectorAll(".selected li > span")).map(
        (item) => item.textContent,
      ),
      [long, "second", "third"],
    );
    await enter(ui.target, 'input[name="artefacts"]', "transient");
    ui.handle.restore(url("test_cases=restored"));
    await flush();
    assert.equal(ui.target.querySelector(".panel"), null);
    assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 1);
    assert.equal(chip(ui.target, "Test Case").title, "Test Case: restored");
    ui.handle.restore(applied);
    await flush();
    assert.equal(
      chip(ui.target, "Artefact").title,
      `Artefact: ${long}, second, third`,
    );
    assert.equal(calls.length, 3);
    button(ui.target, "Clear all").click();
    await flush();
    assert.equal(ui.handle.history.at(-1)?.search, "");
    assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 0);
    assert.equal(calls.length, 3);
    await chooseFilter(ui.target, "Test Case");
    await replaceExact(ui.target, 'input[name="test_cases"]', "one");
    await confirmEditor(ui.target);
    button(ui.target, "Search").click();
    await flush();
    const remove = /** @type {import('happy-dom').HTMLButtonElement | null} */ (
      ui.target.querySelector('button[aria-label="Remove Test Case filter"]')
    );
    assert.ok(remove);
    remove.click();
    await flush();
    assert.match(ui.target.textContent, /clear the previous query/);
    assert.match(ui.target.textContent, /Results for previous query/);
    assert.equal(calls.length, 4);
    button(ui.target, "Search").click();
    await flush();
    assert.equal(ui.handle.history.at(-1)?.search, "");
    assert.equal(ui.target.querySelector(".sv-grid-root"), null);
    assert.equal(calls.length, 4);
    assert.ok(
      calls.every((call) =>
        app.SEARCH_FILTERS.some((key) => call.searchParams.has(key)),
      ),
    );
    await chooseFilter(ui.target, "Test Case");
    await replaceExact(ui.target, 'input[name="test_cases"]', "draft only");
    await confirmEditor(ui.target);
    button(ui.target, "Clear all").click();
    await flush();
    assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 0);
    assert.equal(
      calls.length,
      4,
      "clearing drafts on an already-empty URL is safe too",
    );
  } finally {
    await ui.destroy();
  }
});

void test("mounted pagination disables repeated clicks while loading, maintains applied filters and stops on short data", async () => {
  const next = deferred();
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    calls.push(request);
    return request.searchParams.get("offset") === "2"
      ? next.promise
      : Promise.resolve(response([1, 2], 8, 2));
  };
  const ui = mounted("artefacts=one&limit=2");
  try {
    await flush();
    button(ui.target, "Next page").click();
    button(ui.target, "Next page").click();
    await flush();
    assert.match(ui.target.textContent, /Loading test results/);
    assert.equal(calls.length, 2);
    assert.equal(calls[1].searchParams.get("offset"), "2");
    assert.equal(calls[1].searchParams.get("artefacts"), "one");
    next.resolve(response([3], 8, 2, 2));
    await flush();
    assert.equal(button(ui.target, "Next page").disabled, true);
    assert.equal(button(ui.target, "Previous page").disabled, false);
    assert.match(ui.target.textContent, /case 3/);
    assert.doesNotMatch(ui.target.textContent, /case 1/);
    button(ui.target, "Previous page").click();
    await flush();
    assert.equal(calls.length, 3);
    assert.equal(calls[2].searchParams.get("offset"), null);
  } finally {
    await ui.destroy();
  }
});

void test("mounted grid filtering and sorting stay local without changing the backend total", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(response([2, 1], 12));
  };
  const ui = mounted("test_result_statuses=FAILED");
  try {
    await flush();
    const cells = () =>
      Array.from(
        ui.target.querySelectorAll('tbody td[data-col-id="testCase"]'),
      ).map((cell) => cell.textContent.trim());
    assert.deepEqual(cells(), ["case 2", "case 1"]);
    const sort =
      /** @type {import('happy-dom').HTMLButtonElement | undefined} */ (
        Array.from(
          ui.target.querySelectorAll("button.sv-grid-header-sort"),
        ).find((element) => element.textContent.includes("Test case"))
      );
    assert.ok(sort);
    sort.click();
    await flush();
    assert.deepEqual(cells(), ["case 1", "case 2"]);
    assert.deepEqual(
      app.decodeView(ui.handle.history.at(-1)?.searchParams.get("view") ?? null)
        ?.sorting,
      [{ id: "testCase", desc: false }],
    );
    const local = /** @type {import('happy-dom').HTMLInputElement | null} */ (
      ui.target.querySelector(".sv-grid-global-filter input")
    );
    assert.ok(local);
    local.focus();
    local.value = "no such case";
    local.dispatchEvent(new browser.Event("input", { bubbles: true }));
    await flush();
    assert.deepEqual(cells(), []);
    assert.match(
      ui.target.textContent,
      /No loaded results match the local grid filters/,
    );
    assert.match(
      ui.target.textContent,
      /12 matching test results on the server/,
    );
    assert.equal(calls, 1);
    assert.equal(
      ui.handle.history.length,
      1,
      "grid changes replace, not push history",
    );
    assert.equal(
      app.decodeView(ui.handle.history[0].searchParams.get("view"))
        ?.globalFilter,
      "no such case",
    );
    assert.equal(
      browser.document.activeElement,
      local,
      "automatic view writes preserve input focus",
    );
    // Return every customization to default using the grid itself (not Reset).
    sort.click();
    await flush();
    sort.click();
    await flush();
    local.value = "";
    local.dispatchEvent(new browser.Event("input", { bubbles: true }));
    await flush();
    assert.equal(ui.handle.history[0].searchParams.has("view"), false);
    assert.equal(calls, 1);
  } finally {
    await ui.destroy();
  }
});

void test("view is presentation-only in query identity and never appears in API parameters", () => {
  const params = url(
    "artefacts=one&artefacts=two&limit=2&offset=2&view=invalid",
  ).searchParams;
  const applied = app.parseSearch(params, families);
  assert.deepEqual(applied.problems, []);
  assert.equal(
    app
      .searchParams(applied.filters, applied.limit, applied.offset)
      .has("view"),
    false,
  );
  assert.equal(
    app.searchQueryString(params),
    "artefacts=one&artefacts=two&limit=2&offset=2",
  );
  params.set("view", "different");
  assert.equal(
    app.searchQueryString(params),
    "artefacts=one&artefacts=two&limit=2&offset=2",
  );
  params.append("unsupported", "still blocks");
  assert.match(
    app.parseSearch(params, families).problems[0],
    /Unsupported URL filter/,
  );
});

void test("explicit Search retries when URL encoding changes but backend query identity does not", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(response());
  };
  const ui = mounted("artefacts=one%20two&limit=50");
  try {
    await flush();
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls, 2);
    assert.equal(
      ui.handle.history.at(-1)?.searchParams.get("artefacts"),
      "one two",
    );
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls, 3);
  } finally {
    await ui.destroy();
  }
});

void test("presentation history adapter preserves repeated queries, base, fragment and skips stale/outgoing writes", async () => {
  let current = new URL(
    `${url("artefacts=one&artefacts=two&limit=2&offset=4").href}#anchor`,
  );
  const initial = current.href;
  let writes = 0;
  const adapter = {
    currentUrl: () => current,
    /** @param {URL} next */
    replace: (next) => {
      current = next;
      writes++;
      return Promise.resolve();
    },
  };
  await app.replaceSearchView("encoded-view", initial, adapter);
  assert.equal(writes, 1);
  assert.deepEqual(current.searchParams.getAll("artefacts"), ["one", "two"]);
  assert.equal(current.pathname, "/custom/base/test-results");
  assert.equal(current.hash, "#anchor");
  assert.equal(current.searchParams.get("offset"), "4");
  await app.replaceSearchView("old-grid", initial, adapter);
  assert.equal(writes, 1);
  await app.replaceSearchView("old-grid", current.href, {
    ...adapter,
    currentUrl: () => null,
  });
  assert.equal(writes, 1);
  await app.replaceSearchView(null, current.href, adapter);
  assert.equal(current.href, initial);
});

/** @param {import('happy-dom').HTMLElement} target */
function gridCases(target) {
  return Array.from(
    target.querySelectorAll('tbody td[data-col-id="testCase"]'),
  ).map((cell) => cell.textContent.trim());
}

void test("shared URL restores sorting, global, column, facet and visibility state; removing it restores defaults without remount/fetch", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(response([3, 2, 1], 12));
  };
  const view = app.encodeView({
    sorting: [
      { id: "testCase", desc: false },
      { id: "missing", desc: true },
      { id: "run", desc: true },
    ],
    globalFilter: "case",
    columnFilters: {
      testCase: { operator: "contains", value: "2" },
      missing: { operator: "contains", value: "never" },
      run: { operator: "contains", value: "never" },
    },
    facetFilters: { status: ["FAILED"], missing: ["never"], run: ["never"] },
    hiddenColumns: ["version", "missing"],
    shownColumns: ["missing", "version"],
  });
  const ui = mounted(`artefacts=one&view=${view}`);
  try {
    await flush();
    const grid = ui.target.querySelector(".sv-grid-root");
    assert.ok(grid);
    assert.deepEqual(gridCases(ui.target), ["case 2"]);
    assert.equal(
      ui.target.querySelector('th[data-svgrid-header-col="version"]'),
      null,
    );
    assert.equal(
      ui.target.querySelector(".sv-grid-global-filter input")?.value,
      "case",
    );
    assert.equal(
      ui.handle.replacements.length,
      0,
      "restoring a URL must not echo a rewrite",
    );
    ui.handle.restore(url("artefacts=one"));
    await flush();
    assert.equal(ui.target.querySelector(".sv-grid-root"), grid);
    assert.deepEqual(gridCases(ui.target), ["case 3", "case 2", "case 1"]);
    assert.ok(ui.target.querySelector('th[data-svgrid-header-col="version"]'));
    assert.equal(
      ui.target.querySelector(".sv-grid-global-filter input")?.value,
      "",
    );
    assert.equal(calls, 1);
    assert.equal(ui.handle.replacements.length, 0);
  } finally {
    await ui.destroy();
  }
});

void test("view history changes preserve confirmed drafts, active editor, grid identity and focus", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(response([2, 1]));
  };
  const ui = mounted("artefacts=one&artefacts=two");
  try {
    await flush();
    await chooseFilter(ui.target, "Test Case");
    await replaceExact(ui.target, 'input[name="test_cases"]', "confirmed");
    await confirmEditor(ui.target);
    chip(ui.target, "Artefact").click();
    await flush();
    const editor = await enter(
      ui.target,
      'input[name="artefacts"]',
      "unconfirmed",
    );
    const grid = ui.target.querySelector(".sv-grid-root");
    const view = app.encodeView({
      sorting: [{ id: "testCase", desc: false }],
      globalFilter: "case 1",
    });
    ui.handle.restore(url(`artefacts=one&artefacts=two&view=${view}`));
    await flush();
    assert.equal(ui.target.querySelector('input[name="artefacts"]'), editor);
    assert.equal(editor.value, "unconfirmed");
    assert.equal(browser.document.activeElement, editor);
    assert.equal(chip(ui.target, "Test Case").title, "Test Case: confirmed");
    assert.match(ui.target.textContent, /Changes not applied/);
    assert.equal(ui.target.querySelector(".sv-grid-root"), grid);
    assert.deepEqual(gridCases(ui.target), ["case 1"]);
    ui.handle.restore(url("artefacts=one&artefacts=two"));
    await flush();
    assert.equal(browser.document.activeElement, editor);
    assert.deepEqual(gridCases(ui.target), ["case 2", "case 1"]);
    assert.equal(calls, 1);
  } finally {
    await ui.destroy();
  }
});

void test("view-only updates do not cancel/refetch pending results or auth checks", async () => {
  for (const auth of [false, true]) {
    const pending = deferred();
    /** @type {AbortSignal[]} */
    const signals = [];
    let calls = 0;
    globalThis.fetch = (input, options) => {
      calls++;
      if (options?.signal) signals.push(options.signal);
      const request = new URL(input instanceof Request ? input.url : input);
      if (auth && !request.pathname.endsWith("/users/me"))
        return Promise.resolve(json({}, 403));
      return pending.promise;
    };
    const ui = mounted("artefacts=one");
    try {
      await flush();
      const before = calls;
      const view = app.encodeView({ globalFilter: "case 1" });
      ui.handle.restore(url(`artefacts=one&view=${view}`));
      await flush();
      assert.equal(calls, before);
      assert.ok(signals.length);
      assert.ok(signals.every((signal) => !signal.aborted));
      pending.resolve(auth ? json(null) : response([2, 1]));
      await flush();
      if (auth) assert.match(ui.target.textContent, /need to be logged in/);
      else assert.deepEqual(gridCases(ui.target), ["case 1"]);
    } finally {
      await ui.destroy();
    }
  }
});

void test("outgoing grid callbacks cannot write over a newer query or recreate view after clear", async () => {
  const pending = deferred();
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return calls === 1 ? Promise.resolve(response([2, 1])) : pending.promise;
  };
  const ui = mounted("artefacts=old");
  try {
    await flush();
    const sort = /** @type {import('happy-dom').HTMLButtonElement | null} */ (
      ui.target.querySelector(
        '[data-svgrid-header-col="testCase"] button.sv-grid-header-sort',
      )
    );
    assert.ok(sort);
    sort.click();
    // The grid's sort callback is effect-driven; navigate before it flushes.
    ui.handle.restore(url("artefacts=new"));
    await flush();
    assert.equal(calls, 2);
    assert.equal(ui.handle.currentUrl.search, "?artefacts=new");
    assert.equal(ui.handle.replacements.length, 0);
    pending.resolve(response([3]));
    await flush();
    const incomingSort =
      /** @type {import('happy-dom').HTMLButtonElement | null} */ (
        ui.target.querySelector(
          '[data-svgrid-header-col="testCase"] button.sv-grid-header-sort',
        )
      );
    assert.ok(incomingSort);
    incomingSort.click();
    button(ui.target, "Clear all").click();
    await flush();
    assert.equal(ui.handle.currentUrl.search, "");
    assert.equal(ui.target.querySelector(".sv-grid-root"), null);
    assert.equal(calls, 2);
  } finally {
    await ui.destroy();
  }
});

void test("table view survives pagination, changed Search and identical Search retry; reset only view and Clear all resets everything", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(response([2, 1], 12, 2));
  };
  const view = app.encodeView({
    sorting: [{ id: "testCase", desc: false }],
    hiddenColumns: ["version"],
  });
  const ui = mounted(`artefacts=one&limit=2&view=${view}`);
  try {
    await flush();
    assert.deepEqual(gridCases(ui.target), ["case 1", "case 2"]);
    button(ui.target, "Next page").click();
    await flush();
    assert.equal(ui.handle.history.at(-1)?.searchParams.get("view"), view);
    assert.equal(calls.length, 2);
    assert.equal(calls[1].searchParams.get("offset"), "2");
    assert.deepEqual(gridCases(ui.target), ["case 1", "case 2"]);
    assert.equal(
      ui.target.querySelector('th[data-svgrid-header-col="version"]'),
      null,
    );
    chip(ui.target, "Artefact").click();
    await flush();
    await replaceExact(ui.target, 'input[name="artefacts"]', "changed");
    await confirmEditor(ui.target);
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls.length, 3);
    assert.equal(calls[2].searchParams.get("artefacts"), "changed");
    assert.equal(ui.handle.history.at(-1)?.searchParams.get("view"), view);
    assert.deepEqual(gridCases(ui.target), ["case 1", "case 2"]);
    // Identical explicit Search still retries, and discards unconfirmed edits.
    chip(ui.target, "Artefact").click();
    await flush();
    await enter(ui.target, 'input[name="artefacts"]', "unconfirmed");
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls.length, 4);
    assert.equal(calls[3].searchParams.get("artefacts"), "changed");
    assert.equal(ui.target.querySelector(".panel"), null);
    assert.equal(ui.handle.history.at(-1)?.searchParams.get("view"), view);
    const grid = ui.target.querySelector(".sv-grid-root");
    button(ui.target, "Reset table view").click();
    await flush();
    assert.equal(calls.length, 4);
    assert.equal(ui.target.querySelector(".sv-grid-root"), grid);
    assert.equal(ui.handle.history.at(-1)?.searchParams.has("view"), false);
    assert.deepEqual(gridCases(ui.target), ["case 2", "case 1"]);
    assert.ok(ui.target.querySelector('th[data-svgrid-header-col="version"]'));
    ui.handle.restore(url(`artefacts=changed&view=${view}`));
    await flush();
    const beforeClear = calls.length;
    button(ui.target, "Clear all").click();
    await flush();
    assert.equal(calls.length, beforeClear);
    assert.equal(ui.handle.history.at(-1)?.search, "");
    assert.equal(ui.target.querySelector(".sv-grid-root"), null);
    assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 0);
    assert.ok(calls.every((request) => !request.searchParams.has("view")));
  } finally {
    await ui.destroy();
  }
});

void test("malformed/oversized views and inapplicable column refs remain usable, and view-only URLs never fetch", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(response([2, 1]));
  };
  for (const view of [
    "malformed",
    "a".repeat(8193),
    app.encodeView({
      sorting: [{ id: "run", desc: true }],
      facetFilters: { missing: ["never"] },
    }),
  ]) {
    const ui = mounted(`artefacts=one&view=${view}`);
    try {
      await flush();
      assert.deepEqual(gridCases(ui.target), ["case 2", "case 1"]);
      const before = calls;
      ui.handle.restore(url(`view=${view}&limit=2&offset=2`));
      await flush();
      assert.equal(calls, before);
      assert.match(ui.target.textContent, /Choose at least one filter/);
      await chooseFilter(ui.target, "Artefact");
      await replaceExact(ui.target, 'input[name="artefacts"]', "draft");
      await confirmEditor(ui.target);
      chip(ui.target, "Artefact").click();
      await flush();
      button(ui.target, "Clear all").click();
      await flush();
      assert.equal(ui.target.querySelector(".panel"), null);
      assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 0);
    } finally {
      await ui.destroy();
    }
  }
});

void test("actual grid column/facet filters and visibility controls update a shareable URL without fetching or closing menus", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(response([2, 1]));
  };
  const ui = mounted("artefacts=one&artefacts=two");
  try {
    await flush();
    const filter = /** @type {import('happy-dom').HTMLButtonElement | null} */ (
      ui.target.querySelector('button[aria-label="Filter Test case"]')
    );
    assert.ok(filter);
    filter.click();
    await flush();
    await enter(ui.target, ".sv-grid-menu-condition-value", "case");
    let shared = app.decodeView(
      ui.handle.history.at(-1)?.searchParams.get("view") ?? null,
    );
    assert.deepEqual(shared?.columnFilters, {
      testCase: { operator: "contains", value: "case" },
    });
    const caseTwo = Array.from(
      ui.target.querySelectorAll('.sv-grid-menu [role="option"]'),
    ).find((option) => option.textContent.includes("case 2"));
    assert.ok(
      caseTwo,
      ui.target.querySelector(".sv-grid-filter-menu")?.outerHTML,
    );
    caseTwo.dispatchEvent(new browser.MouseEvent("click", { bubbles: true }));
    await flush();
    shared = app.decodeView(
      ui.handle.history.at(-1)?.searchParams.get("view") ?? null,
    );
    assert.deepEqual(shared?.facetFilters, { testCase: ["case 1"] });
    assert.deepEqual(gridCases(ui.target), ["case 1"]);
    assert.ok(
      ui.target.querySelector(".sv-grid-filter-menu"),
      "URL echo must not close the active menu",
    );
    // Dismiss via the grid's own backdrop, then use its built-in chooser.
    const backdrop = /** @type {import('happy-dom').HTMLElement | null} */ (
      ui.target.querySelector(".sv-grid-menu-backdrop")
    );
    assert.ok(backdrop);
    backdrop.click();
    await flush();
    const menu = /** @type {import('happy-dom').HTMLButtonElement | null} */ (
      ui.target.querySelector('button[aria-label="Artefact column menu"]')
    );
    assert.ok(menu);
    menu.click();
    await flush();
    button(ui.target, "Choose columns").click();
    await flush();
    const version = Array.from(
      ui.target.querySelectorAll(
        '.sv-grid-choose-columns-menu [role="option"]',
      ),
    ).find((option) => option.textContent.trim() === "Version");
    assert.ok(version);
    version.dispatchEvent(new browser.MouseEvent("click", { bubbles: true }));
    await new Promise((resolve) => setTimeout(resolve, 300));
    shared = app.decodeView(
      ui.handle.history.at(-1)?.searchParams.get("view") ?? null,
    );
    assert.deepEqual(shared?.hiddenColumns, ["version"]);
    assert.equal(
      ui.target.querySelector('th[data-svgrid-header-col="version"]'),
      null,
    );
    assert.equal(calls, 1);
    assert.equal(ui.handle.history.length, 1);
    assert.deepEqual(ui.handle.history[0].searchParams.getAll("artefacts"), [
      "one",
      "two",
    ]);
    const track = Array.from(
      ui.target.querySelectorAll(
        '.sv-grid-choose-columns-menu [role="option"]',
      ),
    ).find((option) => option.textContent.trim() === "Track");
    assert.ok(track);
    track.dispatchEvent(new browser.MouseEvent("click", { bubbles: true }));
    // Do not wait for the 250ms visibility tick before submitting Search.
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls, 2);
    assert.deepEqual(
      app
        .decodeView(ui.handle.history.at(-1)?.searchParams.get("view") ?? null)
        ?.hiddenColumns?.toSorted(),
      ["track", "version"],
    );
  } finally {
    await ui.destroy();
  }
});

void test("mounted initial/pagination-only/invalid, no-match, retry and access states render accurately", async () => {
  /** @type {{query: string; status?: number; session?: Response; text: RegExp; noFetch?: boolean}[]} */
  const cases = [
    {
      query: "limit=2&offset=2",
      text: /Choose at least one filter/,
      noFetch: true,
    },
    {
      query: "artefacts=one&issues=any,1",
      text: /Search not applied/,
      noFetch: true,
    },
    { query: "artefacts=one", text: /No test results match/ },
    {
      query: "artefacts=one",
      status: 500,
      text: /Could not load test results/,
    },
    {
      query: "artefacts=one",
      status: 401,
      session: json(null),
      text: /need to be logged in/,
    },
    {
      query: "artefacts=one",
      status: 403,
      session: json({ id: 5, teams: [], is_admin: false }),
      text: /don't have permission/,
    },
    {
      query: "artefacts=one",
      status: 403,
      session: json({}, 503),
      text: /couldn't verify your session/,
    },
  ];
  for (const scenario of cases) {
    let calls = 0;
    globalThis.fetch = (input) => {
      calls++;
      if (
        new URL(input instanceof Request ? input.url : input).pathname.endsWith(
          "/users/me",
        )
      )
        return Promise.resolve(scenario.session ?? json(null));
      return Promise.resolve(
        scenario.status ? json({}, scenario.status) : response([]),
      );
    };
    const ui = mounted(scenario.query);
    try {
      await flush();
      assert.match(ui.target.textContent, scenario.text);
      if (scenario.noFetch) assert.equal(calls, 0);
      if (scenario.status === 500) {
        globalThis.fetch = () => Promise.resolve(response([4]));
        button(ui.target, "Retry").click();
        await flush();
        assert.match(ui.target.textContent, /case 4/);
        assert.doesNotMatch(ui.target.textContent, /Could not load/);
      }
      if (scenario.status === 401) {
        const link = ui.target.querySelector('a[href*="/auth/saml/login"]');
        assert.ok(link);
        const href = link.getAttribute("href");
        assert.ok(href);
        const login = new URL(href);
        assert.equal(
          login.searchParams.get("return_to"),
          url(scenario.query).href,
        );
      }
    } finally {
      await ui.destroy();
    }
  }
});

/** @param {import('happy-dom').HTMLElement} target @param {string} selector */
async function clickInput(target, selector) {
  const input = /** @type {import('happy-dom').HTMLInputElement | null} */ (
    target.querySelector(selector)
  );
  assert.ok(input, selector);
  input.click();
  await flush();
  return input;
}

void test("all eighteen compact editors confirm typed values, meaningful labels and complete repeated API conditions only on Search", async () => {
  app.searchFilterLabelCache().clear();
  /** @type {URL[]} */
  const calls = [];
  /** @type {string[]} */
  const details = [];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    if (request.pathname.includes("/issues/")) {
      details.push(request.pathname);
      return Promise.resolve(
        json({
          id: 41,
          project: "project",
          key: "BUG-7",
          title: "Unicode 🐧 failure",
        }),
      );
    }
    if (request.pathname.includes("/users/")) {
      details.push(request.pathname);
      return Promise.resolve(
        json({ id: 42, name: "A Reviewer", launchpad_handle: "reviewer" }),
      );
    }
    if (request.pathname.endsWith("/execution-metadata"))
      return Promise.resolve(json({ execution_metadata: {} }));
    calls.push(request);
    return Promise.resolve(response());
  };
  const ui = mounted();
  try {
    await flush();
    await chooseFilter(ui.target, "Family");
    await clickInput(panel(ui.target), 'input[value="snap"]');
    await confirmEditor(ui.target);
    await chooseFilter(ui.target, "Status");
    const status = await clickInput(panel(ui.target), 'input[value="FAILED"]');
    assert.equal(status.closest("label")?.textContent.trim(), "Failed");
    await confirmEditor(ui.target);
    assert.equal(chip(ui.target, "Status").title, "Status: Failed");
    for (const [field, label] of [
      ["issues", "Issues"],
      ["reviewer_ids", "Reviewers"],
    ]) {
      await chooseFilter(ui.target, label);
      await replaceExact(
        panel(ui.target),
        `input[name="${field}"]`,
        field === "issues" ? "41,41" : "42",
      );
      await confirmEditor(ui.target);
    }
    assert.match(
      chip(ui.target, "Issues").title,
      /#41 project\/BUG-7 — Unicode 🐧 failure/,
    );
    assert.match(
      chip(ui.target, "Reviewers").title,
      /#42 A Reviewer @reviewer/,
    );
    for (const [field, label] of [
      ["artefacts", "Artefact"],
      ["artefact_versions", "Artefact Version"],
      ["artefact_tracks", "Artefact Track"],
      ["environments", "Environment"],
      ["test_cases", "Test Case"],
      ["test_plans", "Test Plan"],
      ["template_ids", "Template ID"],
    ]) {
      await chooseFilter(ui.target, label);
      await replaceExact(
        panel(ui.target),
        `input[name="${field}"]`,
        " first,second, first, ",
      );
      await confirmEditor(ui.target);
      assert.equal(chip(ui.target, label).title, `${label}: first, second`);
    }
    await chooseFilter(ui.target, "Artefact Stage");
    assert.deepEqual(
      Array.from(panel(ui.target).querySelectorAll("input")).map(
        (input) => input.value,
      ),
      ["", "alpha", "shared", "beta"],
    );
    await clickInput(panel(ui.target), 'input[value=""]');
    await clickInput(panel(ui.target), 'input[value="beta"]');
    await confirmEditor(ui.target);
    assert.equal(
      chip(ui.target, "Artefact Stage").title,
      "Artefact Stage: (none), beta",
    );
    for (const label of ["Archived", "Rerun Requested", "Execution Version"]) {
      await chooseFilter(ui.target, label);
      assert.equal(button(panel(ui.target), "Add filter").disabled, true);
      await clickInput(panel(ui.target), 'input[value="false"]');
      await confirmEditor(ui.target);
    }
    assert.equal(
      chip(ui.target, "Archived").title,
      "Archived: Non archived only",
    );
    assert.equal(
      chip(ui.target, "Rerun Requested").title,
      "Rerun Requested: No rerun requested",
    );
    assert.equal(
      chip(ui.target, "Execution Version").title,
      "Execution Version: Older executions only",
    );
    await chooseFilter(ui.target, "Metadata");
    assert.match(
      panel(ui.target).textContent,
      /all categories \(AND\).*any value \(OR\)/,
    );
    for (const [category, value] of [
      ["c:at,🐧", "one,two:三"],
      ["c:at,🐧", "alternative"],
      ["second", " exact whitespace "],
    ]) {
      await enter(
        panel(ui.target),
        'input[name="metadata-category"]',
        category,
      );
      await enter(panel(ui.target), 'input[name="metadata-value"]', value);
      assert.equal(button(panel(ui.target), "Add filter").disabled, true);
      button(panel(ui.target), "Add pair").click();
      await flush();
    }
    await confirmEditor(ui.target);
    assert.equal(
      chip(ui.target, "Metadata").title,
      'Metadata: "c:at,🐧" = "one,two:三", "c:at,🐧" = "alternative", "second" = " exact whitespace "',
    );
    await chooseFilter(ui.target, "From");
    assert.match(panel(ui.target).textContent, /Date and time \(UTC\)/);
    await enter(
      panel(ui.target),
      'input[type="datetime-local"]',
      "2026-01-01T12:30:00",
    );
    await confirmEditor(ui.target);
    assert.equal(chip(ui.target, "From").title, "From: 2026-01-01T12:30:00Z");
    await chooseFilter(ui.target, "Until");
    await enter(
      panel(ui.target),
      'input[name="until_date"]',
      "2026-02-01T12:30:00.123456+01:30",
    );
    await confirmEditor(ui.target);
    assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 18);
    assert.equal(calls.length, 0);
    button(ui.target, "+ Add filter").click();
    await flush();
    assert.match(panel(ui.target).textContent, /All filters are in use/);
    assert.equal(panel(ui.target).querySelectorAll("li").length, 0);
    button(panel(ui.target), "Cancel").click();
    await flush();
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls.length, 1);
    const params = calls[0].searchParams;
    for (const key of app.EDITABLE_SEARCH_FILTERS)
      assert.ok(params.has(key), key);
    assert.deepEqual(params.getAll("artefact_stages"), ["", "beta"]);
    for (const key of [
      "artefact_is_archived",
      "rerun_is_requested",
      "execution_is_latest",
    ])
      assert.equal(params.get(key), "false");
    assert.equal(params.get("issues"), "41");
    assert.equal(params.get("reviewer_ids"), "42");
    assert.deepEqual(
      app.parseSearch(params, families).filters.execution_metadata,
      [
        { category: "c:at,🐧", values: ["one,two:三", "alternative"] },
        { category: "second", values: [" exact whitespace "] },
      ],
    );
    assert.equal(params.get("until_date"), "2026-02-01T12:30:00.123456+01:30");
    assert.equal(new Set(details).size, 2);
    assert.doesNotMatch(ui.target.textContent, /Changes not applied/);
  } finally {
    await ui.destroy();
  }
});

void test("single-choice booleans and ID modes cannot contradict one another; removing unknown stages is explicit", async () => {
  globalThis.fetch = (input) =>
    Promise.resolve(
      new URL(input instanceof Request ? input.url : input).pathname.includes(
        "/test-results",
      )
        ? response()
        : json({}, 403),
    );
  const ui = mounted(
    "artefact_is_archived=false&rerun_is_requested=false&execution_is_latest=false&issues=none&reviewer_ids=any&artefact_stages=unknown,alpha&families=snap",
  );
  try {
    await flush();
    for (const label of ["Archived", "Rerun Requested", "Execution Version"]) {
      chip(ui.target, label).click();
      await flush();
      assert.equal(
        panel(ui.target).querySelector('input[value="false"]')?.checked,
        true,
      );
      await clickInput(panel(ui.target), 'input[value="true"]');
      assert.equal(
        panel(ui.target).querySelectorAll("input:checked").length,
        1,
      );
      await confirmEditor(ui.target);
    }
    for (const [label, field, any, none] of [
      ["Issues", "issues", "Has any issue", "Has no issues"],
      ["Reviewers", "reviewer_ids", "Has any reviewer", "Has no reviewer"],
    ]) {
      chip(ui.target, label).click();
      await flush();
      await clickInput(panel(ui.target), 'input[value="ids"]');
      await enter(panel(ui.target), `input[name="${field}"]`, "any,1");
      assert.equal(button(panel(ui.target), "Save changes").disabled, true);
      await replaceExact(
        panel(ui.target),
        `input[name="${field}"]`,
        "51, 52,51",
      );
      await confirmEditor(ui.target);
      assert.match(
        chip(ui.target, label).title,
        /#51 details unavailable, #52 details unavailable/,
      );
      chip(ui.target, label).click();
      await flush();
      await clickInput(panel(ui.target), 'input[value="any"]');
      assert.equal(
        panel(ui.target).querySelectorAll("input:checked").length,
        1,
      );
      assert.equal(
        panel(ui.target).querySelector(`input[name="${field}"]`),
        null,
      );
      await confirmEditor(ui.target);
      assert.equal(chip(ui.target, label).title, `${label}: ${any}`);
      chip(ui.target, label).click();
      await flush();
      await clickInput(panel(ui.target), 'input[value="none"]');
      await confirmEditor(ui.target);
      assert.equal(chip(ui.target, label).title, `${label}: ${none}`);
    }
    chip(ui.target, "Family").click();
    await flush();
    await clickInput(panel(ui.target), 'input[value="snap"]');
    await clickInput(panel(ui.target), 'input[value="another-api-family"]');
    await confirmEditor(ui.target);
    assert.equal(
      chip(ui.target, "Artefact Stage").title,
      "Artefact Stage: unknown, alpha",
    );
    chip(ui.target, "Artefact Stage").click();
    await flush();
    assert.match(panel(ui.target).textContent, /unknown \(not configured\)/);
    await clickInput(panel(ui.target), 'input[value="unknown"]');
    await confirmEditor(ui.target);
    button(ui.target, "Search").click();
    await flush();
    assert.deepEqual(
      ui.handle.currentUrl.searchParams.getAll("artefact_stages"),
      ["alpha"],
    );
    assert.equal(ui.handle.currentUrl.searchParams.get("issues"), "none");
    assert.equal(ui.handle.currentUrl.searchParams.get("reviewer_ids"), "none");
    assert.equal(
      ui.handle.currentUrl.searchParams.get("execution_is_latest"),
      "true",
    );
  } finally {
    await ui.destroy();
  }
});

void test("metadata validates Unicode character limits and pending pairs, groups categories, and removes pairs without delimiter loss", async () => {
  globalThis.fetch = () => Promise.resolve(response());
  const ui = mounted();
  try {
    await flush();
    await chooseFilter(ui.target, "Metadata");
    for (const [category, value] of [
      ["", "value"],
      ["category", ""],
      ["🐧".repeat(201), "value"],
      ["category", "x".repeat(201)],
    ]) {
      await enter(
        panel(ui.target),
        'input[name="metadata-category"]',
        category,
      );
      await enter(panel(ui.target), 'input[name="metadata-value"]', value);
      button(panel(ui.target), "Add pair").click();
      await flush();
      assert.match(
        panel(ui.target).querySelector('[role="alert"]')?.textContent ?? "",
        /1–200 characters/,
      );
      assert.equal(button(panel(ui.target), "Add filter").disabled, true);
    }
    for (const [category, value] of [
      ["🐧".repeat(200), "🐧".repeat(200)],
      ["category:1,2", "value:1,2"],
      ["category:1,2", "value:1,2"],
      ["category:1,2", "other"],
    ]) {
      await enter(
        panel(ui.target),
        'input[name="metadata-category"]',
        category,
      );
      await enter(panel(ui.target), 'input[name="metadata-value"]', value);
      button(panel(ui.target), "Add pair").click();
      await flush();
    }
    assert.equal(
      panel(ui.target).querySelectorAll('button[aria-label^="Remove metadata"]')
        .length,
      3,
    );
    button(panel(ui.target), "Remove pair").click();
    await flush();
    await confirmEditor(ui.target);
    assert.equal(
      chip(ui.target, "Metadata").title,
      'Metadata: "category:1,2" = "value:1,2", "category:1,2" = "other"',
    );
    chip(ui.target, "Metadata").click();
    await flush();
    button(panel(ui.target), "Remove pair").click();
    await flush();
    button(panel(ui.target), "Remove pair").click();
    await flush();
    assert.equal(button(panel(ui.target), "Save changes").disabled, true);
    button(panel(ui.target), "Remove filter").click();
    await flush();
    assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 0);
  } finally {
    await ui.destroy();
  }
});

void test("date editors retain offset/microseconds on unchanged save, reject invalid or inverted bounds, and intentionally apply new UTC picker precision", async () => {
  /** @type {URL[]} */ const calls = [];
  globalThis.fetch = (input) => {
    calls.push(new URL(input instanceof Request ? input.url : input));
    return Promise.resolve(response());
  };
  const from = "2026-01-01T01:30:00.123456000+01:30";
  const until = "2026-01-01T00:00:00.123457Z";
  const ui = mounted(
    new URLSearchParams({ from_date: from, until_date: until }).toString(),
  );
  try {
    await flush();
    chip(ui.target, "From").click();
    await flush();
    assert.equal(
      panel(ui.target).querySelector('input[name="from_date"]')?.value,
      from,
    );
    assert.match(
      /** @type {import('happy-dom').HTMLInputElement | null} */ (
        panel(ui.target).querySelector('input[type="datetime-local"]')
      )?.value ?? "",
      /^2026-01-01T00:00(?::00)?$/,
    );
    await confirmEditor(ui.target);
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls.at(-1)?.searchParams.get("from_date"), from);
    chip(ui.target, "Until").click();
    await flush();
    for (const invalid of [
      "2026-02-30T00:00:00Z",
      "2026-01-01T00:00:00",
      "2026-01-01T00:00:00.0000001Z",
      "2026-01-01T00:00:00.123455Z",
    ]) {
      await enter(panel(ui.target), 'input[name="until_date"]', invalid);
      assert.ok(panel(ui.target).querySelector('[role="alert"]'));
      assert.equal(button(panel(ui.target), "Save changes").disabled, true);
      await confirmEditor(ui.target);
      assert.equal(calls.length, 2, "invalid editor cannot confirm or fetch");
      assert.equal(chip(ui.target, "Until").title, `Until: ${until}`);
    }
    await enter(
      panel(ui.target),
      'input[type="datetime-local"]',
      "2026-02-01T10:20:30",
    );
    await confirmEditor(ui.target);
    assert.equal(chip(ui.target, "Until").title, "Until: 2026-02-01T10:20:30Z");
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls.at(-1)?.searchParams.get("from_date"), from);
    assert.equal(
      calls.at(-1)?.searchParams.get("until_date"),
      "2026-02-01T10:20:30Z",
    );
    chip(ui.target, "From").click();
    await flush();
    button(panel(ui.target), "Remove filter").click();
    await flush();
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls.at(-1)?.searchParams.has("from_date"), false);
    assert.equal(
      calls.at(-1)?.searchParams.get("until_date"),
      "2026-02-01T10:20:30Z",
    );
  } finally {
    await ui.destroy();
  }
});

void test("invalid raw fields can be explicitly replaced or cleared while unknown constraints survive and block unrelated edits", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(response());
  };
  const ui = mounted(
    "artefacts=kept&artefact_is_archived=bad&issues=any,1&from_date=bad&unknown=kept&offset=-1",
  );
  try {
    await flush();
    for (const label of ["Archived", "Issues", "From"])
      assert.match(chip(ui.target, label).title, /Invalid URL value/);
    chip(ui.target, "Archived").click();
    await flush();
    assert.match(panel(ui.target).textContent, /original URL value is invalid/);
    await clickInput(panel(ui.target), 'input[value="false"]');
    await confirmEditor(ui.target);
    chip(ui.target, "Issues").click();
    await flush();
    button(panel(ui.target), "Remove filter").click();
    await flush();
    chip(ui.target, "From").click();
    await flush();
    await enter(
      panel(ui.target),
      'input[name="from_date"]',
      "2026-01-01T00:00:00Z",
    );
    await confirmEditor(ui.target);
    assert.match(ui.target.textContent, /Changes not applied/);
    button(ui.target, "Search").click();
    await flush();
    const params = ui.handle.currentUrl.searchParams;
    assert.equal(params.get("artefact_is_archived"), "false");
    assert.equal(params.has("issues"), false);
    assert.equal(params.get("from_date"), "2026-01-01T00:00:00Z");
    assert.equal(params.get("unknown"), "kept");
    assert.equal(params.get("offset"), "-1");
    assert.equal(calls, 0);
    assert.match(ui.target.textContent, /Unsupported URL filter: unknown/);
  } finally {
    await ui.destroy();
  }
});

void test("hydration caches permission/unavailable outcomes without toasts, preserves IDs, and isolates session changes", async () => {
  app.searchFilterLabelCache().clear();
  app.errorStore.clear();
  /** @type {string[]} */ const details = [];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    if (request.pathname.includes("/test-results"))
      return Promise.resolve(response());
    details.push(request.pathname);
    const id = Number(request.pathname.split("/").at(-1));
    if (id === 71) return Promise.resolve(json({}, 403));
    if (id === 72) return Promise.resolve(json({}, 404));
    if (id === 73) return Promise.reject(new Error("offline"));
    if (id === 74)
      return Promise.resolve(json({ id: 999, name: "Wrong identity" }));
    return Promise.resolve(
      json({ id, name: "Session reviewer", launchpad_handle: "handle" }),
    );
  };
  const ui = mounted("issues=71,72,73&reviewer_ids=74,75");
  try {
    await flush();
    await flush();
    assert.equal(details.length, 5);
    assert.equal(
      chip(ui.target, "Issues").title,
      "Issues: #71 details unavailable, #72 details unavailable, #73 details unavailable",
    );
    assert.match(
      chip(ui.target, "Reviewers").title,
      /#74 details unavailable, #75 Session reviewer @handle/,
    );
    chip(ui.target, "Issues").click();
    await flush();
    assert.match(panel(ui.target).textContent, /#71 details unavailable/);
    button(panel(ui.target), "Cancel").click();
    await flush();
    button(ui.target, "Search").click();
    await flush();
    assert.equal(
      details.length,
      5,
      "remount/save/retry must use session cache including failures",
    );
    assert.deepEqual(ui.handle.currentUrl.searchParams.getAll("issues"), [
      "71,72,73",
    ]);
    assert.equal(app.errorStore.message, null);
    await app.userStore.refresh(() =>
      Promise.resolve(
        json({ id: 1234, name: "New session", teams: [], is_admin: false }),
      ),
    );
    await flush();
    assert.equal(
      details.length,
      10,
      "changed session invalidates private label cache once",
    );
    assert.equal(app.errorStore.message, null);
  } finally {
    await ui.destroy();
  }
});

void test("hydration cancels obsolete typed/restored selections and ignores late response bodies without poisoning session cache", async () => {
  app.searchFilterLabelCache().clear();
  const late = deferred();
  const old = json({});
  let reading = false;
  old.json = async () => {
    reading = true;
    const response = await late.promise;
    // eslint-disable-next-line @typescript-eslint/no-unsafe-return -- Response.json is the browser's untyped body parser.
    return response.json();
  };
  /** @type {AbortSignal[]} */ const oldSignals = [];
  let oldCalls = 0;
  globalThis.fetch = (input, options) => {
    const request = new URL(input instanceof Request ? input.url : input);
    if (request.pathname.endsWith("/issues/81")) {
      oldCalls++;
      if (options?.signal) oldSignals.push(options.signal);
      return Promise.resolve(old);
    }
    if (request.pathname.endsWith("/issues/82"))
      return Promise.resolve(
        json({ id: 82, project: "new", key: "82", title: "Latest issue" }),
      );
    return Promise.resolve(response());
  };
  const ui = mounted("issues=81");
  try {
    await flush();
    assert.equal(reading, true);
    const initialCalls = oldCalls;
    assert.equal(
      initialCalls,
      1,
      "initial draft synchronization must not duplicate hydration",
    );
    assert.equal(chip(ui.target, "Issues").title, "Issues: #81 loading…");
    ui.handle.restore(url("issues=82"));
    await flush();
    assert.ok(oldSignals.every((signal) => signal.aborted));
    assert.equal(
      oldCalls,
      initialCalls,
      "newly mounted editors must not hydrate outgoing URL IDs",
    );
    assert.match(chip(ui.target, "Issues").title, /Latest issue/);
    late.resolve(
      json({ id: 81, project: "stale", key: "81", title: "Stale issue" }),
    );
    await flush();
    assert.doesNotMatch(ui.target.textContent, /Stale issue/);
    assert.equal(app.searchFilterLabelCache().peek("issues", 81), undefined);
    chip(ui.target, "Issues").click();
    await flush();
    await replaceExact(panel(ui.target), 'input[name="issues"]', "81");
    button(panel(ui.target), "Cancel").click();
    await flush();
    assert.match(chip(ui.target, "Issues").title, /Latest issue/);
    assert.equal(
      oldCalls,
      initialCalls + 1,
      "a cancelled lookup is not a cached failure",
    );
  } finally {
    await ui.destroy();
  }
});

void test("label cache deduplicates pending requests and only aborts when its last consumer leaves", async () => {
  const cache = new app.SearchFilterLabelCache();
  const pending = deferred();
  let calls = 0;
  /** @type {AbortSignal | null | undefined} */ let requestSignal;
  globalThis.fetch = (_input, options) => {
    calls++;
    requestSignal = options?.signal;
    return pending.promise;
  };
  const first = new AbortController();
  const second = new AbortController();
  const a = cache.load("reviewer_ids", 91, first.signal);
  const b = cache.load("reviewer_ids", 91, second.signal);
  assert.equal(calls, 1);
  first.abort();
  assert.equal(requestSignal?.aborted, false);
  pending.resolve(
    json({ id: 91, name: "Shared reviewer", launchpad_handle: null }),
  );
  assert.equal(await a, undefined);
  assert.equal(await b, "#91 Shared reviewer");
  assert.equal(cache.peek("reviewer_ids", 91), "#91 Shared reviewer");
  assert.equal(
    await cache.load("reviewer_ids", 91, new AbortController().signal),
    "#91 Shared reviewer",
  );
  assert.equal(calls, 1);
});

void test("new typed editor kinds retain cancellation/Escape/outside semantics and never save temporary edits", async () => {
  let calls = 0;
  globalThis.fetch = (input) => {
    if (
      new URL(input instanceof Request ? input.url : input).pathname.endsWith(
        "/execution-metadata",
      )
    )
      return Promise.resolve(json({ execution_metadata: {} }));
    calls++;
    return Promise.resolve(response());
  };
  const metadata = `${Buffer.from("category").toString("base64")}:${Buffer.from("value").toString("base64")}`;
  const ui = mounted(
    `artefact_is_archived=false&issues=none&execution_metadata=${metadata}&from_date=2026-01-01T00:00:00.123456Z`,
  );
  const outside = browser.document.createElement("button");
  outside.textContent = "Outside";
  browser.document.body.append(outside);
  try {
    await flush();
    for (const label of ["Archived", "Issues", "Metadata", "From"]) {
      for (const dismissal of ["Cancel", "Escape", "outside"]) {
        const trigger = chip(ui.target, label);
        const original = trigger.title;
        trigger.click();
        await flush();
        assert.ok(
          panel(ui.target).contains(browser.document.activeElement),
          "typed editor receives focus after opening",
        );
        if (label === "Archived")
          await clickInput(panel(ui.target), 'input[value="true"]');
        else if (label === "Issues")
          await clickInput(panel(ui.target), 'input[value="any"]');
        else if (label === "Metadata")
          await enter(
            panel(ui.target),
            'input[name="metadata-category"]',
            "discard me",
          );
        else
          await enter(
            panel(ui.target),
            'input[name="from_date"]',
            "2027-01-01T00:00:00Z",
          );
        if (dismissal === "Cancel") button(panel(ui.target), "Cancel").click();
        else if (dismissal === "Escape")
          panel(ui.target).dispatchEvent(
            new browser.KeyboardEvent("keydown", {
              key: "Escape",
              bubbles: true,
              cancelable: true,
            }),
          );
        else {
          outside.focus();
          outside.click();
        }
        await flush();
        assert.equal(ui.target.querySelector(".panel"), null);
        assert.equal(chip(ui.target, label).title, original);
        assert.equal(
          browser.document.activeElement,
          dismissal === "outside" ? outside : trigger,
        );
        assert.doesNotMatch(ui.target.textContent, /Changes not applied/);
      }
    }
    assert.equal(calls, 1);
  } finally {
    outside.remove();
    await ui.destroy();
  }
});

const settleSuggestions = () =>
  new Promise((resolve) => setTimeout(resolve, 290));

/** @param {import('happy-dom').HTMLElement} target @param {string} key */
async function press(target, key) {
  const event = new browser.KeyboardEvent("keydown", {
    key,
    bubbles: true,
    cancelable: true,
  });
  target.dispatchEvent(event);
  await flush();
  return event;
}

/** @param {import('happy-dom').HTMLElement} target */
function suggestionButtons(target) {
  return Array.from(target.querySelectorAll("button")).filter((button) =>
    button.closest(".suggestions"),
  );
}

void test("lookup contracts use the actual six endpoints, trimmed q, bounded replies and draft family parameters only for name lookups", async () => {
  /** @type {{url: URL; options: RequestInit}[]} */ const calls = [];
  globalThis.fetch = (input, options = {}) => {
    const request = new URL(input instanceof Request ? input.url : input);
    calls.push({ url: request, options });
    const path = request.pathname;
    return Promise.resolve(
      json(
        path.endsWith("/test-cases")
          ? {
              test_cases: [
                { test_case: "a case", template_id: "template1" },
                { test_case: "a case", template_id: "template2" },
                { test_case: "comma,case", template_id: "template3" },
              ],
            }
          : path.endsWith("/issues")
            ? {
                issues: [
                  {
                    id: 204,
                    source: "jira",
                    project: "generic",
                    key: "BUG-4",
                    title: "A failure",
                  },
                  { id: -1 },
                ],
              }
            : path.endsWith("/users")
              ? {
                  users: [
                    {
                      id: 205,
                      name: "A Reviewer",
                      launchpad_handle: "review",
                      email: "review@example.test",
                    },
                  ],
                }
              : path.endsWith("/environments")
                ? { environments: ["a lab", "a lab"] }
                : path.endsWith("/test-plans")
                  ? { test_plans: ["a plan"] }
                  : {
                      artefacts: Array.from(
                        { length: 70 },
                        (_, i) => `artefact${i}`,
                      ),
                    },
      ),
    );
  };
  const fields = /** @type {const} */ ([
    "artefacts",
    "environments",
    "test_plans",
    "test_cases",
    "issues",
    "reviewer_ids",
  ]);
  const paths = [
    "artefacts/search",
    "environments",
    "test-plans",
    "test-cases",
    "issues",
    "users",
  ];
  for (const [index, field] of fields.entries()) {
    assert.deepEqual(
      await app.lookupValues(
        field,
        " a ",
        ["custom-family"],
        new AbortController().signal,
      ),
      [],
    );
    assert.equal(calls.length, index);
    const values = await app.lookupValues(
      field,
      "  a query 🐧  ",
      ["z-family", "a-family", "z-family"],
      new AbortController().signal,
    );
    const call = calls[index];
    assert.equal(call.url.pathname, `/v1/${paths[index]}`);
    assert.equal(call.url.searchParams.get("q"), "a query 🐧");
    assert.equal(call.url.searchParams.get("limit"), index < 4 ? "50" : "10");
    assert.deepEqual(
      call.url.searchParams.getAll("families"),
      index < 4 ? ["a-family", "z-family"] : [],
    );
    assert.equal(call.options.credentials, "include");
    assert.equal(new Headers(call.options.headers).get("X-CSRF-Token"), "1");
    if (field === "artefacts") assert.equal(values.length, 50);
    if (field === "environments") assert.equal(values.length, 1);
    if (field === "test_cases") {
      assert.equal(
        values.length,
        2,
        "duplicate case names with different template IDs are one choice",
      );
      assert.equal(values[0].value, "a case");
      assert.match(values[1].unavailable ?? "", /commas/);
    }
    if (field === "issues")
      assert.match(values[0].label, /#204 jira — generic\/BUG-4 — A failure/);
    if (field === "reviewer_ids")
      assert.match(values[0].label, /A Reviewer @review — review@example.test/);
  }
  assert.match(app.suggestionScope(), /^http:\/\/localhost:30000:/);
});

void test("mounted name suggestions debounce, separate selected values from query, support keyboard/multi-select/exact/removal and apply only on Search", async () => {
  /** @type {URL[]} */ const calls = [];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    calls.push(request);
    return Promise.resolve(
      request.pathname.endsWith("/test-results")
        ? response()
        : json({ artefacts: ["alpha", "alpine", "alpha"] }),
    );
  };
  const ui = mounted();
  try {
    await flush();
    await chooseFilter(ui.target, "Artefact");
    assert.equal(calls.length, 0);
    assert.match(panel(ui.target).textContent, /at least 2 characters/);
    const input = await enter(ui.target, 'input[name="artefacts"]', " a ");
    await settleSuggestions();
    assert.equal(calls.length, 0);
    await enter(ui.target, 'input[name="artefacts"]', "al");
    await enter(ui.target, 'input[name="artefacts"]', "alp");
    assert.equal(calls.length, 0, "no request on each keystroke");
    assert.match(panel(ui.target).textContent, /Loading suggestions/);
    await settleSuggestions();
    assert.equal(calls.length, 1);
    assert.equal(calls[0].searchParams.get("q"), "alp");
    assert.equal(button(panel(ui.target), "Add filter").disabled, true);
    assert.equal(ui.handle.currentUrl.search, "");
    assert.equal((await press(input, "Enter")).defaultPrevented, true);
    assert.equal(ui.target.querySelectorAll(".chip-trigger").length, 0);
    assert.equal(panel(ui.target).querySelector('[role="combobox"]'), null);
    await press(input, "ArrowDown");
    assert.equal(
      browser.document.activeElement,
      suggestionButtons(panel(ui.target))[0],
    );
    await press(suggestionButtons(panel(ui.target))[0], "ArrowDown");
    assert.equal(
      browser.document.activeElement,
      suggestionButtons(panel(ui.target))[1],
    );
    await press(suggestionButtons(panel(ui.target))[1], "ArrowUp");
    await press(suggestionButtons(panel(ui.target))[0], "Enter");
    assert.equal(input.value, "");
    assert.equal(browser.document.activeElement, input);
    assert.match(
      panel(ui.target).querySelector(".selected")?.textContent ?? "",
      /alpha/,
    );
    await enter(ui.target, 'input[name="artefacts"]', "al");
    await settleSuggestions();
    assert.deepEqual(
      suggestionButtons(panel(ui.target)).map((b) => b.textContent.trim()),
      ["alpine"],
    );
    suggestionButtons(panel(ui.target))[0].click();
    await flush();
    await enter(ui.target, 'input[name="artefacts"]', "al");
    await settleSuggestions();
    assert.match(panel(ui.target).textContent, /No unselected matches/);
    assert.equal(button(panel(ui.target), "Add filter").disabled, true);
    button(panel(ui.target), "Clear input").click();
    await flush();
    await enter(ui.target, 'input[name="artefacts"]', "alpha");
    button(panel(ui.target), "Add exact value").click();
    await flush();
    assert.equal(
      panel(ui.target).querySelectorAll(".selected li").length,
      2,
      "exact duplicates cannot duplicate a selection",
    );
    await enter(ui.target, 'input[name="artefacts"]', "new exact");
    assert.equal(
      button(panel(ui.target), "Add filter").disabled,
      true,
      "pending text cannot be lost on Save",
    );
    button(panel(ui.target), "Add exact value").click();
    await flush();
    button(panel(ui.target), "Remove").click();
    await flush();
    assert.deepEqual(
      Array.from(panel(ui.target).querySelectorAll(".selected li > span")).map(
        (n) => n.textContent,
      ),
      ["alpine", "new exact"],
    );
    await confirmEditor(ui.target);
    assert.equal(
      chip(ui.target, "Artefact").title,
      "Artefact: alpine, new exact",
    );
    assert.equal(ui.handle.currentUrl.search, "");
    assert.equal(
      calls.filter((c) => c.pathname.endsWith("/test-results")).length,
      0,
    );
    button(ui.target, "Search").click();
    await flush();
    assert.deepEqual(calls.at(-1)?.searchParams.getAll("artefacts"), [
      "alpine",
      "new exact",
    ]);
  } finally {
    await ui.destroy();
  }
});

void test("confirmed draft family chips scope suggestions without searching results or dropping values unavailable in the new context", async () => {
  /** @type {URL[]} */ const calls = [];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    calls.push(request);
    return Promise.resolve(
      request.pathname.endsWith("/test-results")
        ? response()
        : json({ environments: ["current lab"] }),
    );
  };
  const ui = mounted("families=snap&environments=retained");
  try {
    await flush();
    chip(ui.target, "Family").click();
    await flush();
    await clickInput(panel(ui.target), 'input[value="snap"]');
    await clickInput(panel(ui.target), 'input[value="another-api-family"]');
    await confirmEditor(ui.target);
    chip(ui.target, "Environment").click();
    await flush();
    await enter(ui.target, 'input[name="environments"]', "la");
    await settleSuggestions();
    assert.deepEqual(calls.at(-1)?.searchParams.getAll("families"), [
      "another-api-family",
    ]);
    assert.equal(
      ui.handle.currentUrl.searchParams.get("families"),
      "snap",
      "applied URL is not the draft lookup context",
    );
    assert.equal(
      calls.filter((c) => c.pathname.endsWith("/test-results")).length,
      1,
    );
    assert.match(
      panel(ui.target).querySelector(".selected")?.textContent ?? "",
      /retained/,
    );
    suggestionButtons(panel(ui.target))[0].click();
    await flush();
    await confirmEditor(ui.target);
    assert.equal(
      chip(ui.target, "Environment").title,
      "Environment: retained, current lab",
    );
  } finally {
    await ui.destroy();
  }
});

void test("rich issue/reviewer suggestions prime selected labels, keep exclusive modes and exact-ID fallback without extra detail requests", async () => {
  app.searchFilterLabelCache().clear();
  /** @type {URL[]} */ const calls = [];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    calls.push(request);
    return Promise.resolve(
      json(
        request.pathname.endsWith("/issues")
          ? {
              issues: [
                {
                  id: 330,
                  project: "Generic",
                  key: "BUG-1",
                  title: "Issue title",
                  source: "github",
                },
              ],
            }
          : request.pathname.endsWith("/users")
            ? {
                users: [
                  {
                    id: 331,
                    name: "Person",
                    launchpad_handle: "person",
                    email: "person@example.test",
                  },
                ],
              }
            : {},
      ),
    );
  };
  const ui = mounted();
  try {
    await flush();
    for (const [label, field, rich] of [
      ["Issues", "issues", "Issue title"],
      ["Reviewers", "reviewer_ids", "person@example.test"],
    ]) {
      await chooseFilter(ui.target, label);
      await enter(ui.target, `input[name="${field}"]`, "pe");
      await settleSuggestions();
      assert.match(
        suggestionButtons(panel(ui.target))[0].textContent,
        new RegExp(rich),
      );
      suggestionButtons(panel(ui.target))[0].click();
      await flush();
      assert.match(
        panel(ui.target).querySelector(".selected")?.textContent ?? "",
        new RegExp(rich),
      );
      await confirmEditor(ui.target);
      assert.match(chip(ui.target, label).title, new RegExp(rich));
    }
    assert.equal(
      calls.length,
      2,
      "lookup records are sufficient labels; no redundant /id GET",
    );
    assert.ok(calls.every((c) => !c.searchParams.has("families")));
    chip(ui.target, "Issues").click();
    await flush();
    await enter(ui.target, 'input[name="issues"]', "any,1");
    button(panel(ui.target), "Add exact IDs").click();
    await flush();
    assert.equal(button(panel(ui.target), "Save changes").disabled, true);
    assert.ok(panel(ui.target).querySelector('[role="alert"]'));
    await enter(ui.target, 'input[name="issues"]', "330,330");
    button(panel(ui.target), "Add exact IDs").click();
    await flush();
    assert.equal(panel(ui.target).querySelectorAll(".selected li").length, 1);
    await clickInput(panel(ui.target), 'input[value="none"]');
    await confirmEditor(ui.target);
    assert.equal(chip(ui.target, "Issues").title, "Issues: Has no issues");
  } finally {
    await ui.destroy();
  }
});

void test("an in-flight draft family-context change aborts old parsed suggestions and refreshes without wiping selections", async () => {
  const late = deferred();
  const old = json({});
  old.json = async () => {
    const response = await late.promise;
    // eslint-disable-next-line @typescript-eslint/no-unsafe-return -- Browser response parser.
    return response.json();
  };
  /** @type {AbortSignal | null | undefined} */ let oldSignal;
  /** @type {URL[]} */ const calls = [];
  globalThis.fetch = (input, options) => {
    const request = new URL(input instanceof Request ? input.url : input);
    calls.push(request);
    if (request.searchParams.get("families") === "old-family") {
      oldSignal = options?.signal;
      return Promise.resolve(old);
    }
    return Promise.resolve(json({ artefacts: ["new-family result"] }));
  };
  const target = browser.document.createElement("div");
  browser.document.body.append(target);
  const handle = app.mountSuggestions(
    /** @type {HTMLElement} */ (/** @type {unknown} */ (target)),
  );
  try {
    await enter(target, 'input[name="artefacts"]', "same query");
    await settleSuggestions();
    handle.setFamilies(["new-family"]);
    await flush();
    assert.equal(oldSignal?.aborted, true);
    assert.deepEqual(handle.selected, ["retained"]);
    assert.equal(suggestionButtons(target).length, 0);
    late.resolve(json({ artefacts: ["STALE FAMILY"] }));
    await settleSuggestions();
    assert.equal(calls.length, 2);
    assert.deepEqual(calls[1].searchParams.getAll("families"), ["new-family"]);
    assert.doesNotMatch(target.textContent, /STALE FAMILY/);
    assert.match(target.textContent, /new-family result/);
    assert.deepEqual(handle.selected, ["retained"]);
  } finally {
    await handle.destroy();
    target.remove();
  }
});

void test("unsupported comma/whitespace names are honestly disabled and manual exact commas are not silently split", async () => {
  globalThis.fetch = () =>
    Promise.resolve(
      json({
        test_cases: [
          { test_case: "case,one", template_id: "template" },
          { test_case: " surrounded ", template_id: "other" },
        ],
      }),
    );
  const ui = mounted();
  try {
    await flush();
    await chooseFilter(ui.target, "Test Case");
    await enter(ui.target, 'input[name="test_cases"]', "ca");
    await settleSuggestions();
    assert.ok(suggestionButtons(panel(ui.target)).every((b) => b.disabled));
    assert.match(
      panel(ui.target).textContent,
      /commas.*comma-separated|surrounding whitespace/,
    );
    await enter(ui.target, 'input[name="test_cases"]', "case,one");
    button(panel(ui.target), "Add exact value").click();
    await flush();
    assert.match(
      panel(ui.target).querySelector('[role="alert"]')?.textContent ?? "",
      /commas/,
    );
    assert.equal(panel(ui.target).querySelectorAll(".selected li").length, 0);
    button(panel(ui.target), "Clear input").click();
    await flush();
    assert.equal(button(panel(ui.target), "Add filter").disabled, true);
    assert.match(panel(ui.target).textContent, /No selected values/);
  } finally {
    await ui.destroy();
  }
});

void test("lookup failures remain local, retain selected values, offer retry/exact and distinguish auth/permission errors", async () => {
  app.errorStore.clear();
  for (const [status, message] of [
    [401, /Sign in/],
    [403, /permission/],
    [500, /could not be loaded/],
  ]) {
    let fail = true;
    let calls = 0;
    globalThis.fetch = (input) => {
      const request = new URL(input instanceof Request ? input.url : input);
      if (request.pathname.endsWith("/test-results"))
        return Promise.resolve(response());
      calls++;
      return Promise.resolve(
        fail
          ? json({}, /** @type {number} */ (status))
          : json({ test_plans: ["plan"] }),
      );
    };
    const ui = mounted("test_plans=retained");
    try {
      await flush();
      chip(ui.target, "Test Plan").click();
      await flush();
      await enter(ui.target, 'input[name="test_plans"]', "pl");
      await settleSuggestions();
      assert.match(
        panel(ui.target).textContent,
        /** @type {RegExp} */ (message),
      );
      assert.match(
        panel(ui.target).querySelector(".selected")?.textContent ?? "",
        /retained/,
      );
      assert.equal(app.errorStore.message, null);
      fail = false;
      button(panel(ui.target), "Retry suggestions").click();
      await settleSuggestions();
      assert.equal(calls, 2);
      suggestionButtons(panel(ui.target))[0].click();
      await flush();
      await confirmEditor(ui.target);
      assert.equal(
        chip(ui.target, "Test Plan").title,
        "Test Plan: retained, plan",
      );
    } finally {
      await ui.destroy();
    }
  }
});

void test("latest query wins over delayed response bodies and stale 500 errors, with abort on below-threshold/close/field switch", async () => {
  for (const oldStatus of [200, 500]) {
    const late = deferred();
    /** @type {AbortSignal | null | undefined} */ let oldSignal;
    let reading = false;
    const oldResponse = json({}, oldStatus);
    if (oldStatus === 200)
      oldResponse.json = async () => {
        reading = true;
        const response = await late.promise;
        // eslint-disable-next-line @typescript-eslint/no-unsafe-return -- Browser response parser.
        return response.json();
      };
    globalThis.fetch = (input, options) => {
      const request = new URL(input instanceof Request ? input.url : input);
      if (request.searchParams.get("q") === "old") {
        oldSignal = options?.signal;
        return oldStatus === 200 ? Promise.resolve(oldResponse) : late.promise;
      }
      return Promise.resolve(json({ artefacts: ["new result"] }));
    };
    const ui = mounted();
    try {
      await flush();
      await chooseFilter(ui.target, "Artefact");
      await enter(ui.target, 'input[name="artefacts"]', "old");
      await settleSuggestions();
      assert.ok(oldSignal);
      if (oldStatus === 200) assert.equal(reading, true);
      await enter(ui.target, 'input[name="artefacts"]', "new");
      await settleSuggestions();
      assert.equal(oldSignal.aborted, true);
      late.resolve(
        oldStatus === 200 ? json({ artefacts: ["STALE"] }) : oldResponse,
      );
      await flush();
      assert.deepEqual(
        suggestionButtons(panel(ui.target)).map((b) => b.textContent.trim()),
        ["new result"],
      );
      assert.doesNotMatch(
        panel(ui.target).textContent,
        /STALE|could not be loaded/,
      );
    } finally {
      await ui.destroy();
    }
  }
  /** @type {AbortSignal[]} */ const signals = [];
  const late = deferred();
  globalThis.fetch = (_input, options) => {
    if (options?.signal) signals.push(options.signal);
    return late.promise;
  };
  const ui = mounted();
  try {
    await flush();
    await chooseFilter(ui.target, "Artefact");
    await enter(ui.target, 'input[name="artefacts"]', "first");
    await settleSuggestions();
    await enter(ui.target, 'input[name="artefacts"]', "a");
    assert.equal(signals[0].aborted, true);
    await enter(ui.target, 'input[name="artefacts"]', "second");
    await settleSuggestions();
    button(panel(ui.target), "Cancel").click();
    await flush();
    assert.equal(signals[1].aborted, true);
    await chooseFilter(ui.target, "Environment");
    await enter(ui.target, 'input[name="environments"]', "third");
    await settleSuggestions();
    button(ui.target, "+ Add filter").click();
    await flush();
    assert.equal(signals[2].aborted, true);
    late.resolve(json({ artefacts: ["STALE"], environments: ["STALE"] }));
    await flush();
    assert.doesNotMatch(ui.target.textContent, /STALE/);
  } finally {
    await ui.destroy();
  }
});

void test("auth changes abort lookup bodies and clear prior suggestions before loading the new context", async () => {
  await app.userStore.refresh(() =>
    Promise.resolve(
      json({ id: 410, name: "First", teams: [], is_admin: false }),
    ),
  );
  const late = deferred();
  /** @type {AbortSignal | null | undefined} */ let oldSignal;
  let first = true;
  const old = json({});
  old.json = async () => {
    const response = await late.promise;
    // eslint-disable-next-line @typescript-eslint/no-unsafe-return -- Browser response parser.
    return response.json();
  };
  globalThis.fetch = (_input, options) => {
    if (first) {
      first = false;
      oldSignal = options?.signal;
      return Promise.resolve(old);
    }
    return Promise.resolve(json({ artefacts: ["Anonymous result"] }));
  };
  const ui = mounted();
  try {
    await flush();
    await chooseFilter(ui.target, "Artefact");
    await enter(ui.target, 'input[name="artefacts"]', "query");
    await settleSuggestions();
    await app.userStore.refresh(() => Promise.resolve(json(null)));
    await flush();
    assert.equal(oldSignal?.aborted, true);
    assert.equal(suggestionButtons(panel(ui.target)).length, 0);
    late.resolve(json({ artefacts: ["PRIVATE OLD RESULT"] }));
    await settleSuggestions();
    assert.doesNotMatch(ui.target.textContent, /PRIVATE OLD RESULT/);
    assert.match(panel(ui.target).textContent, /Anonymous result/);
  } finally {
    await ui.destroy();
  }
});

void test("metadata suggestions load lazily once per session context, filter locally, preserve raw manual punctuation and group pairs", async () => {
  await app.userStore.refresh(() =>
    Promise.resolve(json({ id: 420, teams: [], is_admin: false })),
  );
  /** @type {URL[]} */ const calls = [];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    calls.push(request);
    return Promise.resolve(
      json({
        execution_metadata: {
          "c:at,🐧": ["one,two:三", "other"],
          another: ["elsewhere"],
          ["__proto__"]: ["literal"],
        },
      }),
    );
  };
  const ui = mounted();
  try {
    await flush();
    assert.equal(calls.length, 0);
    await chooseFilter(ui.target, "Metadata");
    assert.equal(calls.length, 1);
    assert.equal(calls[0].pathname, "/v1/execution-metadata");
    assert.equal(calls[0].search, "");
    const categoryInput = await enter(
      ui.target,
      'input[name="metadata-category"]',
      "c:",
    );
    const categories = ui.target.querySelector(
      `#${categoryInput.getAttribute("list")}`,
    );
    assert.deepEqual(
      Array.from(categories?.querySelectorAll("option") ?? []).map(
        (item) => item.value,
      ),
      ["c:at,🐧"],
    );
    await enter(ui.target, 'input[name="metadata-category"]', "c:at,🐧");
    const valueInput = await enter(
      ui.target,
      'input[name="metadata-value"]',
      "one,",
    );
    const values = ui.target.querySelector(
      `#${valueInput.getAttribute("list")}`,
    );
    assert.deepEqual(
      Array.from(values?.querySelectorAll("option") ?? []).map(
        (item) => item.value,
      ),
      ["one,two:三"],
    );
    await enter(ui.target, 'input[name="metadata-value"]', "one,two:三");
    assert.equal(
      (await press(valueInput, "Enter")).defaultPrevented,
      false,
      "native datalist selection must not be cancelled",
    );
    await confirmEditor(ui.target);
    assert.equal(
      ui.target.querySelectorAll(".chip-trigger").length,
      0,
      "pending pair blocks implicit form confirmation",
    );
    button(panel(ui.target), "Add pair").click();
    await flush();
    await enter(ui.target, 'input[name="metadata-category"]', "c:at,🐧");
    await enter(ui.target, 'input[name="metadata-value"]', "manual:comma,🐧");
    button(panel(ui.target), "Add pair").click();
    await flush();
    await confirmEditor(ui.target);
    assert.equal(
      chip(ui.target, "Metadata").title,
      'Metadata: "c:at,🐧" = "one,two:三", "c:at,🐧" = "manual:comma,🐧"',
    );
    chip(ui.target, "Metadata").click();
    await flush();
    await enter(ui.target, 'input[name="metadata-category"]', "unknown");
    assert.match(
      panel(ui.target).textContent,
      /No\s+matching known categories/,
    );
    await enter(ui.target, 'input[name="metadata-category"]', "__proto__");
    assert.deepEqual(
      Array.from(panel(ui.target).querySelectorAll("option")).map(
        (item) => item.value,
      ),
      ["__proto__", "literal"],
      "category keys are literal data, not object prototype members",
    );
    assert.equal(
      calls.length,
      1,
      "neither typing nor reopening refetches the full map",
    );
    assert.equal(ui.handle.currentUrl.search, "");
    button(panel(ui.target), "Cancel").click();
    await flush();
    await app.userStore.refresh(() => Promise.resolve(json(null)));
    await flush();
    await app.userStore.refresh(() =>
      Promise.resolve(json({ id: 420, teams: [], is_admin: false })),
    );
    await flush();
    chip(ui.target, "Metadata").click();
    await flush();
    assert.equal(
      calls.length,
      2,
      "logout while closed invalidates even a subsequent identical profile",
    );
  } finally {
    await ui.destroy();
    await app.userStore.refresh(() => Promise.resolve(json(null)));
  }
});

void test("metadata ignores cancelled parsed bodies, keeps failures local and permits exact pairs plus explicit retry", async () => {
  await app.userStore.refresh(() =>
    Promise.resolve(json({ id: 430, teams: [], is_admin: false })),
  );
  app.errorStore.clear();
  const late = deferred();
  const old = json({});
  old.json = async () => {
    const response = await late.promise;
    // eslint-disable-next-line @typescript-eslint/no-unsafe-return -- Browser response parser.
    return response.json();
  };
  let count = 0;
  /** @type {AbortSignal | null | undefined} */ let oldSignal;
  globalThis.fetch = (_input, options) => {
    count++;
    if (count === 1) {
      oldSignal = options?.signal;
      return Promise.resolve(old);
    }
    return Promise.resolve(
      count === 2
        ? json({}, 403)
        : json({ execution_metadata: { latest: ["value"] } }),
    );
  };
  const ui = mounted();
  try {
    await flush();
    await chooseFilter(ui.target, "Metadata");
    button(panel(ui.target), "Cancel").click();
    await flush();
    assert.equal(oldSignal?.aborted, true);
    late.resolve(json({ execution_metadata: { PRIVATE: ["OLD"] } }));
    await flush();
    await chooseFilter(ui.target, "Metadata");
    assert.match(panel(ui.target).textContent, /permission/);
    assert.equal(app.errorStore.message, null);
    await enter(ui.target, 'input[name="metadata-category"]', "manual:🐧");
    await enter(ui.target, 'input[name="metadata-value"]', "value,exact");
    button(panel(ui.target), "Add pair").click();
    await flush();
    button(panel(ui.target), "Retry suggestions").click();
    await flush();
    assert.equal(count, 3);
    const options = Array.from(panel(ui.target).querySelectorAll("option")).map(
      (item) => item.value,
    );
    assert.deepEqual(options, ["latest"]);
    await confirmEditor(ui.target);
    assert.equal(
      chip(ui.target, "Metadata").title,
      'Metadata: "manual:🐧" = "value,exact"',
    );
  } finally {
    await ui.destroy();
    await app.userStore.refresh(() => Promise.resolve(json(null)));
  }
});

void test("known metadata cache has a bounded lifetime rather than persisting stale options indefinitely", async () => {
  await app.userStore.refresh(() =>
    Promise.resolve(json({ id: 440, teams: [], is_admin: false })),
  );
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(
      json({ execution_metadata: { category: [`generation${calls}`] } }),
    );
  };
  const now = Date.now;
  try {
    const scope = app.suggestionScope();
    const first = await app.metadataSuggestions.load(
      scope,
      new AbortController().signal,
    );
    const cached = await app.metadataSuggestions.load(
      scope,
      new AbortController().signal,
    );
    assert.deepEqual(first, { category: ["generation1"] });
    assert.deepEqual(cached, first);
    assert.equal(calls, 1);
    Date.now = () => now() + 6 * 60_000;
    const refreshed = await app.metadataSuggestions.load(
      scope,
      new AbortController().signal,
    );
    assert.deepEqual(refreshed, { category: ["generation2"] });
    assert.equal(calls, 2);
  } finally {
    Date.now = now;
    await app.userStore.refresh(() => Promise.resolve(json(null)));
  }
});

void test("selection snapshot normalizes all typed predicates, never paging/view, and keeps validation and microseconds", () => {
  const params = new URLSearchParams({
    families: "snap",
    test_result_statuses: "FAILED,PASSED",
    artefacts: "two,one,one",
    artefact_versions: "1,2",
    artefact_tracks: "stable",
    environments: "lab",
    test_plans: "smoke",
    test_cases: "case",
    artefact_stages: "",
    artefact_is_archived: "false",
    rerun_is_requested: "false",
    execution_is_latest: "false",
    issues: "none",
    reviewer_ids: "any",
    template_ids: "b,a",
    from_date: "2026-01-01T01:00:00.123456+01:00",
    until_date: "2026-02-01T00:00:00Z",
    limit: "2",
    offset: "4",
    view: "local-only",
  });
  const pair = (/** @type {string} */ category, /** @type {string} */ value) =>
    `${app.encodeMetadataPart(category)}:${app.encodeMetadataPart(value)}`;
  params.append("execution_metadata", pair("punctuation:,", "value:,"));
  params.append("execution_metadata", pair("punctuation:,", "other"));
  const query = app.parseSearch(params, families);
  assert.deepEqual(query.problems, []);
  const snapshot = app.selectionQuery(query);
  assert.ok(snapshot);
  const equivalent = new URLSearchParams(params);
  equivalent.set("artefacts", "one,two");
  equivalent.set("test_result_statuses", "PASSED,FAILED");
  equivalent.set("template_ids", "a,b");
  equivalent.set("from_date", "2026-01-01T00:00:00.1234560Z");
  equivalent.set("until_date", "2026-02-01T00:00:00.000000Z");
  equivalent.set(
    "execution_metadata",
    [
      pair("punctuation:,", "other"),
      pair("punctuation:,", "value:,"),
      pair("punctuation:,", "other"),
    ].join(","),
  );
  equivalent.set("limit", "1000");
  equivalent.delete("offset");
  equivalent.delete("view");
  assert.equal(
    app.selectionQuery(app.parseSearch(equivalent, families))?.key,
    snapshot.key,
  );
  for (const [key, replacement] of [
    ["artefact_stages", "alpha"],
    ["artefact_is_archived", "true"],
    ["rerun_is_requested", "true"],
    ["execution_is_latest", "true"],
    ["issues", "any"],
    ["reviewer_ids", "none"],
    ["from_date", "2026-01-01T00:00:00.123457Z"],
  ]) {
    const changed = new URLSearchParams(equivalent);
    changed.set(key, replacement);
    assert.notEqual(
      app.selectionQuery(app.parseSearch(changed, families))?.key,
      snapshot.key,
      key,
    );
  }
  for (const suffix of [
    "issues=0",
    "unknown=x",
    "limit=0",
    "from_date=not-a-date",
    "families=unavailable",
  ]) {
    const invalid = app.parseSearch(
      url(`artefacts=one&${suffix}`).searchParams,
      families,
    );
    assert.ok(invalid.problems.length);
    assert.equal(app.selectionQuery(invalid), null);
  }
  assert.equal(
    app.selectionQuery(
      app.parseSearch(url("view=x&offset=2").searchParams, families),
    ),
    null,
  );
  query.filters.artefacts.push("draft-mutation");
  query.filters.execution_metadata[0].values.push("draft-mutation");
  assert.deepEqual(snapshot.filters.artefacts, ["two", "one"]);
  assert.deepEqual(snapshot.filters.execution_metadata[0].values, [
    "value:,",
    "other",
  ]);
  assert.equal(snapshot.filters.artefact_is_archived, false);
  assert.deepEqual(snapshot.filters.artefact_stages, [""]);
});

void test("selection rule counts unique explicit IDs across pages, all exclusions and million matches without enumerating", () => {
  const selection = selectionFor("artefacts=one");
  selection.updateCount(1_000_000);
  const first = selection.page([1, 2, 2], () => true);
  assert.equal(first.headerState([1, 2]), "none");
  first.toggle([1, 1, 999, -1, 1.5], true);
  assert.equal(selection.selectedCount, 1);
  assert.equal(first.headerState([1, 2, 2]), "some");
  first.toggleAllMatches();
  assert.equal(selection.allMatches, false, "partial page is not eligible");
  first.toggle([2], true);
  assert.equal(first.allLoadedSelected(), true);
  const second = selection.page([2, 3, 4], () => true);
  second.toggle([3], true);
  assert.deepEqual([...selection.explicitIds], [1, 2, 3]);
  first.toggleAllMatches();
  assert.equal(selection.selectedCount, 1_000_000);
  assert.equal(selection.explicitIds.size, 0);
  second.toggle([3, 3, 4, 999], false);
  assert.equal(selection.selectedCount, 999_998);
  assert.deepEqual([...selection.exclusions], [3, 4]);
  assert.equal(first.headerState([1, 2]), "all");
  assert.equal(second.headerState([2, 3, 4]), "some");
  second.toggle([3], true);
  assert.equal(selection.selectedCount, 999_999);
  selection.updateCount(19);
  assert.equal(
    selection.selectedCount,
    18,
    "last count, not an invented snapshot total",
  );
  selection.updateCount(0);
  assert.equal(
    selection.selectedCount,
    0,
    "never negative after server deletions",
  );
  assert.equal(
    selection.allMatches,
    true,
    "active rule survives zero count/exclusions",
  );
});

void test("all-mode off keeps selected loaded backend-page rows (even locally hidden), header off is not global Clear", () => {
  const selection = selectionFor("test_result_statuses=FAILED");
  selection.updateCount(19);
  const first = selection.page([1, 2], () => true);
  first.toggle([1, 2], true);
  first.toggleAllMatches();
  const second = selection.page([3, 4, 5, 5], () => true);
  second.toggle([4], false);
  // A local filter displays only row 3; header off excludes only row 3.
  second.toggle([3], false);
  assert.equal(selection.allMatches, true);
  assert.equal(selection.selectedCount, 17);
  assert.equal(first.headerState([1, 2]), "all");
  assert.equal(second.headerState([3]), "none");
  assert.equal(second.headerState([]), "none");
  second.toggleAllMatches();
  assert.equal(selection.allMatches, false);
  assert.deepEqual([...selection.explicitIds], [5]);
  assert.equal(selection.exclusions.size, 0);
  assert.equal(first.isSelected(1), false);
  second.clear();
  assert.equal(selection.selectedCount, 0);
  assert.equal(selection.explicitIds.size, 0);
});

void test("page selection capabilities reject stale/loading callbacks, invalid queries, unknown IDs and empty-page opt-in", () => {
  const selection = selectionFor("artefacts=one");
  selection.updateCount(19);
  let current = true;
  const first = selection.page([1, 2], () => current);
  first.toggle([1, 2], true);
  current = false;
  first.toggleAllMatches();
  first.clear();
  first.toggle([1], false);
  assert.equal(selection.selectedCount, 2);
  assert.equal(first.headerState([1, 2]), "none");
  assert.equal(first.allLoadedSelected(), false);
  current = true;
  const equivalent = app.selectionQuery(
    app.parseSearch(
      url("offset=4&artefacts=one&limit=2&view=x").searchParams,
      families,
    ),
  );
  selection.setQuery(equivalent);
  assert.equal(selection.selectedCount, 2);
  selection.setQuery(
    app.selectionQuery(
      app.parseSearch(url("artefacts=two").searchParams, families),
    ),
  );
  first.toggle([1, 2], true);
  first.toggleAllMatches();
  assert.equal(selection.selectedCount, 0);
  const empty = selection.page([], () => true);
  empty.toggleAllMatches();
  assert.equal(selection.allMatches, false);
  selection.setQuery(null);
  empty.toggleAllMatches();
  assert.equal(empty.enabled(), false);
  assert.equal(selection.matchCount, 0);
});

void test("mounted search retains only selected execution IDs from successful current pages, preserves view history, and clears on reapply/route", async () => {
  // eslint-disable-next-line @typescript-eslint/unbound-method -- Deliberate prototype probe, always invoked with .apply below.
  const originalPage = app.TestResultsSelection.prototype.page;
  /** @type {import('../src/lib/testResultsSelection.svelte').TestResultsSelection[]} */
  const captured = [];
  /** @type {ReturnType<typeof originalPage>[]} */
  const capabilities = [];
  app.TestResultsSelection.prototype.page = function (...args) {
    captured.push(this);
    const capability = originalPage.apply(this, args);
    capabilities.push(capability);
    return capability;
  };
  let calls = 0;
  globalThis.fetch = (input) => {
    calls++;
    const request = new URL(input instanceof Request ? input.url : input);
    const ids = request.searchParams.get("offset") === "2" ? [3, 4] : [1, 2];
    return Promise.resolve(
      json({
        count: 6,
        test_results: ids.map((id) => ({
          ...result(id),
          test_result: {
            ...result(id).test_result,
            io_log: "must not be retained in selection",
          },
          test_execution: { ...result(id).test_execution, id: id + 300 },
        })),
      }),
    );
  };
  const ui = mounted("artefacts=one&limit=2");
  try {
    await flush();
    selectionRow(ui.target, 1).click();
    await flush();
    const active = captured.at(-1);
    assert.ok(active);
    assert.deepEqual(active.snapshot().executions, [
      { resultId: 1, executionId: 301 },
    ]);
    button(ui.target, "Next page").click();
    await flush();
    selectionRow(ui.target, 3).click();
    await flush();
    assert.deepEqual(active.snapshot().executions, [
      { resultId: 1, executionId: 301 },
      { resultId: 3, executionId: 303 },
    ]);
    const first = capabilities[0];
    assert.ok(first);
    first.toggle([2], true);
    assert.deepEqual([...active.explicitIds], [1, 3]);
    const applied = app.parseSearch(
      ui.handle.currentUrl.searchParams,
      families,
    );
    const target = app.freezeBulkTarget(active.snapshot(), applied, {
      available: true,
      loading: false,
      moving: false,
      accessError: false,
      unapplied: false,
      mutating: false,
    });
    assert.ok(target.ok);
    const ids = app.executionIds(target.value);
    assert.ok(ids.ok);
    assert.deepEqual(ids.value, [301, 303]);
    const beforeViewCalls = calls;
    const view = new URL(ui.handle.currentUrl);
    view.searchParams.set("view", "invalid-presentation-is-ignored");
    ui.handle.restore(view);
    await flush();
    assert.equal(calls, beforeViewCalls);
    assert.deepEqual(active.snapshot().executions, [
      { resultId: 1, executionId: 301 },
      { resultId: 3, executionId: 303 },
    ]);
    selectionRow(ui.target, 3).click();
    await flush();
    assert.deepEqual(active.snapshot().executions, [
      { resultId: 1, executionId: 301 },
    ]);
    button(ui.target, "Search").click();
    await flush();
    assert.deepEqual(active.snapshot().executions, []);
    selectionRow(ui.target, 1).click();
    await flush();
    const route = new URL(ui.handle.currentUrl);
    route.pathname = "/custom/base/another-search-route";
    ui.handle.restore(route);
    await flush();
    assert.deepEqual(active.snapshot().executions, []);
    assert.equal(ui.target.querySelector(".selection-summary"), null);
    assert.equal(ui.target.textContent.includes("Bulk actions"), false);
  } finally {
    await ui.destroy();
    app.TestResultsSelection.prototype.page = originalPage;
  }
});

void test("actual grid row/header accessible selection and all-mode persist across server pages, with no selection API/view leakage", async () => {
  /** @type {URL[]} */
  const calls = [];
  globalThis.fetch = (input) => {
    const request = new URL(input instanceof Request ? input.url : input);
    calls.push(request);
    return Promise.resolve(
      request.searchParams.get("offset") === "2"
        ? response([3, 4], 19, 2, 2)
        : response([1, 2], 19, 2),
    );
  };
  const ui = mounted("test_result_statuses=PASSED,FAILED,SKIPPED&limit=2");
  try {
    await flush();
    const originalUrl = ui.handle.currentUrl.href;
    assert.equal(
      ui.target
        .querySelector("thead tr th")
        ?.classList.contains("sv-grid-selection-column"),
      true,
    );
    assert.equal(
      selectionHeader(ui.target).getAttribute("aria-checked"),
      "false",
    );
    selectionRow(ui.target, 1).click();
    await flush();
    assert.equal(
      selectionHeader(ui.target).getAttribute("aria-checked"),
      "mixed",
    );
    assert.match(ui.target.textContent, /1 selected by result ID/);
    assert.equal(allMatchesCheckbox(ui.target), null);
    selectionHeader(ui.target).dispatchEvent(
      new browser.KeyboardEvent("keydown", { key: " ", bubbles: true }),
    );
    await flush();
    assert.equal(
      selectionHeader(ui.target).getAttribute("aria-checked"),
      "true",
    );
    let all = allMatchesCheckbox(ui.target);
    assert.ok(all);
    assert.equal(
      all.closest("label")?.textContent.trim(),
      "Apply bulk options to all 19 matches",
    );
    all.click();
    await flush();
    assert.match(
      ui.target.textContent,
      /19 selected across the applied query \(0 excluded\)/,
    );
    assert.match(
      ui.target.textContent,
      /last server total, not\s+a\s+frozen snapshot/,
    );
    assert.equal(ui.handle.currentUrl.href, originalUrl);
    assert.equal(ui.handle.replacements.length, 0);
    assert.equal(calls.length, 1, "selection is entirely network-free");
    button(ui.target, "Next page").click();
    await flush();
    assert.equal(
      selectionRow(ui.target, 3).getAttribute("aria-checked"),
      "true",
    );
    selectionRow(ui.target, 3).click();
    await flush();
    assert.equal(
      selectionHeader(ui.target).getAttribute("aria-checked"),
      "mixed",
    );
    assert.match(
      ui.target.textContent,
      /18 selected across the applied query \(1 excluded\)/,
    );
    all = allMatchesCheckbox(ui.target);
    assert.ok(all?.checked, "active all control survives an exclusion");
    button(ui.target, "Previous page").click();
    await flush();
    assert.equal(
      selectionHeader(ui.target).getAttribute("aria-checked"),
      "true",
    );
    assert.match(ui.target.textContent, /18 selected across/);
    button(ui.target, "Next page").click();
    await flush();
    assert.equal(
      selectionRow(ui.target, 3).getAttribute("aria-checked"),
      "false",
    );
    allMatchesCheckbox(ui.target)?.click();
    await flush();
    assert.match(ui.target.textContent, /1 selected by result ID/);
    assert.equal(
      selectionRow(ui.target, 4).getAttribute("aria-checked"),
      "true",
    );
    assert.equal(allMatchesCheckbox(ui.target), null);
    button(ui.target, "Clear selection").click();
    await flush();
    assert.equal(ui.target.querySelector(".selection-summary"), null);
    assert.equal(
      selectionHeader(ui.target).getAttribute("aria-checked"),
      "false",
    );
    assert.equal(calls.length, 4);
    assert.ok(
      calls.every((request) =>
        [...request.searchParams.keys()].every((key) =>
          ["test_result_statuses", "limit", "offset"].includes(key),
        ),
      ),
    );
    assert.ok(
      ui.handle.history.every(
        (entry) => !/select|exclude|allMatches/i.test(entry.search),
      ),
    );
    assert.equal(
      ui.target.querySelector(".sv-grid-selection-bar, .sv-grid-bulk-edit"),
      null,
    );
    assert.equal(ui.target.querySelector(".sv-grid-cell-selected"), null);
  } finally {
    await ui.destroy();
  }
});

void test("explicit result IDs survive pagination and limit changes within a normalized applied query", async () => {
  let calls = 0;
  globalThis.fetch = (input) => {
    calls++;
    const request = new URL(input instanceof Request ? input.url : input);
    return Promise.resolve(
      request.searchParams.get("offset") === "2"
        ? response([3, 4], 19, 2, 2)
        : response([1, 2], 19, 2),
    );
  };
  const ui = mounted("artefacts=one,two&limit=2");
  try {
    await flush();
    selectionRow(ui.target, 1).click();
    await flush();
    button(ui.target, "Next page").click();
    await flush();
    assert.equal(
      selectionHeader(ui.target).getAttribute("aria-checked"),
      "false",
    );
    assert.match(ui.target.textContent, /1 selected by result ID/);
    selectionRow(ui.target, 3).click();
    await flush();
    assert.match(ui.target.textContent, /2 selected by result ID/);
    button(ui.target, "Previous page").click();
    await flush();
    assert.equal(
      selectionRow(ui.target, 1).getAttribute("aria-checked"),
      "true",
    );
    assert.equal(
      selectionRow(ui.target, 2).getAttribute("aria-checked"),
      "false",
    );
    ui.handle.restore(url("artefacts=two&artefacts=one&artefacts=one&limit=3"));
    await flush();
    assert.match(ui.target.textContent, /2 selected by result ID/);
    assert.equal(
      selectionRow(ui.target, 1).getAttribute("aria-checked"),
      "true",
    );
    button(ui.target, "Clear selection").click();
    await flush();
    ui.handle.restore(url("artefacts=one,two&limit=2&offset=2"));
    await flush();
    assert.equal(
      selectionRow(ui.target, 3).getAttribute("aria-checked"),
      "false",
      "Clear is global, including unloaded explicit IDs",
    );
    assert.equal(calls, 5);
  } finally {
    await ui.destroy();
  }
});

void test("local-filtered subsets cannot offer all matches; header targets full displayed rows and all-mode exclusions persist locally", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(response([1, 2], 19, 2));
  };
  const ui = mounted("artefacts=one&limit=2");
  try {
    await flush();
    await localSearch(ui.target, "case 1");
    selectionHeader(ui.target).click();
    await flush();
    assert.match(ui.target.textContent, /1 selected by result ID/);
    assert.equal(
      selectionHeader(ui.target).getAttribute("aria-checked"),
      "true",
    );
    assert.equal(
      allMatchesCheckbox(ui.target),
      null,
      "local subset is not the entire backend page",
    );
    await localSearch(ui.target, "");
    assert.equal(
      selectionHeader(ui.target).getAttribute("aria-checked"),
      "mixed",
    );
    selectionRow(ui.target, 2).click();
    await flush();
    assert.ok(allMatchesCheckbox(ui.target));
    allMatchesCheckbox(ui.target)?.click();
    await flush();
    await localSearch(ui.target, "case 1");
    selectionHeader(ui.target).click();
    await flush();
    assert.match(
      ui.target.textContent,
      /18 selected across the applied query \(1 excluded\)/,
    );
    assert.ok(allMatchesCheckbox(ui.target)?.checked);
    await localSearch(ui.target, "no rows");
    assert.equal(
      selectionHeader(ui.target).getAttribute("aria-checked"),
      "false",
    );
    selectionHeader(ui.target).click();
    await flush();
    assert.match(ui.target.textContent, /18 selected across/);
    assert.ok(
      allMatchesCheckbox(ui.target)?.checked,
      "active control remains with no displayed rows",
    );
    allMatchesCheckbox(ui.target)?.click();
    await flush();
    assert.match(
      ui.target.textContent,
      /1 selected by result ID/,
      "opting out keeps selected row 2 despite local hiding",
    );
    await localSearch(ui.target, "");
    assert.equal(
      selectionRow(ui.target, 1).getAttribute("aria-checked"),
      "false",
    );
    assert.equal(
      selectionRow(ui.target, 2).getAttribute("aria-checked"),
      "true",
    );
    button(ui.target, "Clear selection").click();
    await flush();
    await localSearch(ui.target, "no rows");
    selectionHeader(ui.target).click();
    await flush();
    assert.equal(allMatchesCheckbox(ui.target), null);
    assert.equal(ui.target.querySelector(".selection-summary"), null);
    assert.equal(calls, 1);
    const view = app.decodeView(ui.handle.currentUrl.searchParams.get("view"));
    assert.deepEqual(
      Object.keys(view ?? {}).filter((key) => /select|exclude/i.test(key)),
      [],
    );
  } finally {
    await ui.destroy();
  }
});

void test("virtualized actual-grid header selects every displayed loaded row, not just mounted DOM rows", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(
      response(
        Array.from({ length: 120 }, (_, i) => i + 1),
        1_000_000,
        200,
      ),
    );
  };
  const ui = mounted("artefacts=one&limit=200");
  try {
    await flush();
    const rendered = ui.target.querySelectorAll(
      'tbody button[aria-label="Select row"]',
    ).length;
    assert.ok(
      rendered > 0 && rendered < 120,
      `virtualization must be active (${rendered} mounted rows)`,
    );
    selectionHeader(ui.target).click();
    await flush();
    assert.match(ui.target.textContent, /120 selected by result ID/);
    assert.equal(
      selectionHeader(ui.target).getAttribute("aria-checked"),
      "true",
    );
    const all = allMatchesCheckbox(ui.target);
    assert.ok(all);
    assert.equal(
      all.closest("label")?.textContent.trim(),
      "Apply bulk options to all 1000000 matches",
    );
    all.click();
    await flush();
    assert.match(ui.target.textContent, /1000000 selected across/);
    selectionHeader(ui.target).click();
    await flush();
    assert.match(
      ui.target.textContent,
      /999880 selected across the applied query \(120 excluded\)/,
    );
    assert.ok(allMatchesCheckbox(ui.target)?.checked);
    button(ui.target, "Clear selection").click();
    await flush();
    assert.equal(ui.target.querySelector(".selection-summary"), null);
    assert.equal(calls, 1);
  } finally {
    await ui.destroy();
  }
});

void test("selection survives draft/editor, sort, visibility and view/reset/history without serialization or requests", async () => {
  let calls = 0;
  globalThis.fetch = () => {
    calls++;
    return Promise.resolve(response([2, 1], 19, 2));
  };
  const ui = mounted("artefacts=one&limit=2");
  try {
    await flush();
    selectionHeader(ui.target).click();
    await flush();
    allMatchesCheckbox(ui.target)?.click();
    await flush();
    selectionRow(ui.target, 1).click();
    await flush();
    chip(ui.target, "Artefact").click();
    await flush();
    await replaceExact(ui.target, 'input[name="artefacts"]', "draft");
    await confirmEditor(ui.target);
    assert.match(ui.target.textContent, /Changes not applied/);
    assert.match(ui.target.textContent, /18 selected across/);
    assert.match(
      ui.target.textContent,
      /not local grid filters or\s+unapplied drafts/,
    );
    const grid = ui.target.querySelector(".sv-grid-root");
    const view = app.encodeView({
      sorting: [{ id: "testCase", desc: false }],
      hiddenColumns: ["version"],
      globalFilter: "case 2",
    });
    ui.handle.restore(url(`artefacts=one&limit=2&view=${view}`));
    await flush();
    assert.equal(ui.target.querySelector(".sv-grid-root"), grid);
    assert.deepEqual(gridCases(ui.target), ["case 2"]);
    assert.equal(
      ui.target.querySelector('th[data-svgrid-header-col="version"]'),
      null,
    );
    assert.match(ui.target.textContent, /18 selected across/);
    assert.ok(allMatchesCheckbox(ui.target)?.checked);
    button(ui.target, "Reset table view").click();
    await flush();
    assert.deepEqual(gridCases(ui.target), ["case 2", "case 1"]);
    assert.equal(
      selectionRow(ui.target, 1).getAttribute("aria-checked"),
      "false",
    );
    assert.equal(
      selectionRow(ui.target, 2).getAttribute("aria-checked"),
      "true",
    );
    assert.match(ui.target.textContent, /Changes not applied/);
    assert.equal(chip(ui.target, "Artefact").title, "Artefact: draft");
    assert.equal(calls, 1);
    assert.equal(ui.handle.currentUrl.searchParams.has("view"), false);
    assert.ok(
      ui.handle.history.every(
        (entry) => !/select|exclude|allMatches/i.test(entry.search),
      ),
    );
  } finally {
    await ui.destroy();
  }
});

void test("new/identical Search, Clear all, meaningful history and remount reset selection; stale native callbacks cannot change incoming datasets", async () => {
  let calls = 0;
  let next = deferred();
  let pending = false;
  globalThis.fetch = () => {
    calls++;
    return pending ? next.promise : Promise.resolve(response([1, 2], 19, 2));
  };
  const ui = mounted("artefacts=one&limit=2");
  try {
    await flush();
    selectionHeader(ui.target).click();
    await flush();
    const oldHeader = selectionHeader(ui.target);
    const oldAll = allMatchesCheckbox(ui.target);
    const oldClear = button(ui.target, "Clear selection");
    assert.ok(oldAll);
    pending = true;
    button(ui.target, "Search").click();
    await flush();
    assert.match(ui.target.textContent, /Loading test results/);
    assert.equal(ui.target.querySelector('.results [role="checkbox"]'), null);
    assert.equal(allMatchesCheckbox(ui.target), null);
    oldHeader.click();
    oldAll.click();
    oldClear.click();
    next.resolve(response([1, 2], 19));
    await flush();
    assert.equal(
      selectionHeader(ui.target).getAttribute("aria-checked"),
      "false",
    );
    selectionHeader(ui.target).click();
    await flush();
    oldClear.click();
    oldAll.click();
    oldHeader.click();
    await flush();
    assert.match(
      ui.target.textContent,
      /2 selected by result ID/,
      "detached old page cannot clear or enable all on new results",
    );
    pending = false;
    const beforeIdentical = calls;
    button(ui.target, "Search").click();
    await flush();
    assert.equal(calls, beforeIdentical + 1);
    assert.equal(ui.target.querySelector(".selection-summary"), null);
    selectionHeader(ui.target).click();
    await flush();
    next = deferred();
    pending = true;
    ui.handle.restore(url("artefacts=different&limit=2"));
    await flush();
    assert.equal(
      ui.target.querySelector(".selection-summary"),
      null,
      "new criteria clear promptly before response",
    );
    next.resolve(response([3, 4], 19, 2));
    await flush();
    assert.equal(
      selectionHeader(ui.target).getAttribute("aria-checked"),
      "false",
    );
    selectionHeader(ui.target).click();
    await flush();
    pending = false;
    ui.handle.restore(url("artefacts=one&limit=2"));
    await flush();
    assert.equal(
      ui.target.querySelector(".selection-summary"),
      null,
      "Back to different criteria does not restore selection",
    );
    selectionHeader(ui.target).click();
    await flush();
    button(ui.target, "Clear all").click();
    await flush();
    assert.equal(ui.target.querySelector(".sv-grid-root"), null);
    ui.handle.restore(url("artefacts=one&limit=2"));
    await flush();
    assert.equal(
      selectionHeader(ui.target).getAttribute("aria-checked"),
      "false",
    );
    selectionHeader(ui.target).click();
    await flush();
  } finally {
    await ui.destroy();
  }
  pending = false;
  const fresh = mounted("artefacts=one&limit=2");
  try {
    await flush();
    assert.equal(
      selectionHeader(fresh.target).getAttribute("aria-checked"),
      "false",
      "route remount/reload never rehydrates selection",
    );
    assert.equal(fresh.target.querySelector(".selection-summary"), null);
  } finally {
    await fresh.destroy();
  }
});

void test("selection controls disappear on errors/invalid criteria and never offer bogus all prompts on empty or out-of-range pages", async () => {
  for (const failure of [401, 403, 500, "invalid"]) {
    let failing = false;
    globalThis.fetch = (input) => {
      const request = new URL(input instanceof Request ? input.url : input);
      if (request.pathname.endsWith("/users/me"))
        return Promise.resolve(json(null));
      return Promise.resolve(
        failing && typeof failure === "number"
          ? json({}, failure)
          : response([1, 2], 19, 2),
      );
    };
    const ui = mounted("artefacts=one&limit=2");
    try {
      await flush();
      selectionHeader(ui.target).click();
      await flush();
      allMatchesCheckbox(ui.target)?.click();
      await flush();
      const oldHeader = selectionHeader(ui.target);
      const oldAll = allMatchesCheckbox(ui.target);
      assert.ok(oldAll);
      failing = true;
      ui.handle.restore(
        url(
          failure === "invalid"
            ? "artefacts=one&issues=0"
            : "artefacts=one&limit=2&offset=2",
        ),
      );
      await flush();
      assert.equal(ui.target.querySelector('.results [role="checkbox"]'), null);
      assert.equal(allMatchesCheckbox(ui.target), null);
      oldHeader.click();
      oldAll.click();
      failing = false;
      ui.handle.restore(url("artefacts=one&limit=2"));
      await flush();
      assert.equal(
        selectionHeader(ui.target).getAttribute("aria-checked"),
        failure === "invalid" ? "false" : "true",
      );
      if (failure !== "invalid")
        assert.match(ui.target.textContent, /19 selected across/);
    } finally {
      await ui.destroy();
    }
  }
  for (const count of [0, 19]) {
    globalThis.fetch = () => Promise.resolve(response([], count, 2, 100));
    const ui = mounted("artefacts=one&limit=2&offset=100");
    try {
      await flush();
      assert.equal(ui.target.querySelector(".sv-grid-root"), null);
      assert.equal(allMatchesCheckbox(ui.target), null);
      assert.equal(ui.target.querySelector(".selection-summary"), null);
    } finally {
      await ui.destroy();
    }
  }
});
