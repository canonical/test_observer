// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { after, before, test } from "node:test";
import { createServer, build } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { Window } from "happy-dom";
import { resolve } from "node:path";

/** @type {import("vite").ViteDevServer | undefined} */
let vite;
/** @type {typeof import("../src/lib/stores/artefact-page.svelte").ArtefactPageStore | undefined} */
let ArtefactPageStore;
/** @type {typeof import("../src/lib/utils/artefact-filters").parseArtefactId | undefined} */
let parseArtefactId;
/** @type {typeof import("../src/lib/utils/artefact-filters").matchesExecutionStatuses | undefined} */
let matchesExecutionStatuses;
/** @type {typeof import("../src/lib/utils/artefact-filters").matchesPlanLastRunStatuses | undefined} */
let matchesPlanLastRunStatuses;
/** @type {typeof import("../src/lib/utils/artefact-filters").matchingLatestPlanRuns | undefined} */
let matchingLatestPlanRuns;
/** @type {typeof import('../src/lib/utils/artefact-filters').latestPlanStatuses | undefined} */
let latestPlanStatuses;
/** @type {typeof import("../src/lib/utils/artefact-filters").shouldFetchExpandedData | undefined} */
let shouldFetchExpandedData;
/** @type {typeof import("../src/lib/utils/artefact-filters").parsePositiveSafeInteger | undefined} */
let parsePositiveSafeInteger;
/** @type {typeof import("../src/lib/utils/artefact-filters").decodeFilterValues | undefined} */
let decodeFilterValues;
/** @type {typeof import("svelte/server").render | undefined} */
let render;
/** @type {import("svelte").Component<any> | undefined} */
let EnvironmentIssuesExpandable;
/** @type {import("svelte").Component<any> | undefined} */
let TestResultExpandable;
/** @type {import("svelte").Component<any> | undefined} */
let BulkEnvironmentSelectionControls;
/** @type {import("svelte").Component<any> | undefined} */
let EnvironmentReviewButton;
/** @type {import("svelte").Component<any> | undefined} */
let EnvironmentExpandable;
/** @type {import("svelte").Component<any> | undefined} */
let ArtefactSignoffButton;
/** @type {import("svelte").Component<any> | undefined} */
let TestPlanExpandable;
/** @type {typeof import("../tests/comment-editor-entry").mountCommentEditor | undefined} */
let mountCommentEditor;
/** @type {typeof import("../tests/comment-editor-entry").unmountCommentEditor | undefined} */
let unmountCommentEditor;
/** @type {typeof import("../tests/comment-editor-entry").mountArtefactPage | undefined} */
let mountArtefactPage;
/** @type {Window | undefined} */
let browserWindow;
/** @type {Map<string, PropertyDescriptor | undefined>} */
const originalGlobals = new Map();

before(async () => {
  vite = await createServer({
    configFile: "vite.config.ts",
    appType: "custom",
    logLevel: "silent",
    server: { middlewareMode: true },
  });
  ({ ArtefactPageStore } = await vite.ssrLoadModule(
    "/src/lib/stores/artefact-page.svelte.ts",
  ));
  ({
    parseArtefactId,
    matchesExecutionStatuses,
    matchesPlanLastRunStatuses,
    matchingLatestPlanRuns,
    latestPlanStatuses,
    shouldFetchExpandedData,
    parsePositiveSafeInteger,
    decodeFilterValues,
  } = await vite.ssrLoadModule("/src/lib/utils/artefact-filters.ts"));
  ({ render } = await vite.ssrLoadModule("svelte/server"));
  ({ default: EnvironmentIssuesExpandable } = await vite.ssrLoadModule(
    "/src/lib/components/artefact/EnvironmentIssuesExpandable.svelte",
  ));
  ({ default: TestResultExpandable } = await vite.ssrLoadModule(
    "/src/lib/components/artefact/TestResultExpandable.svelte",
  ));
  ({ default: BulkEnvironmentSelectionControls } = await vite.ssrLoadModule(
    "/src/lib/components/artefact/BulkEnvironmentSelectionControls.svelte",
  ));
  ({ default: EnvironmentReviewButton } = await vite.ssrLoadModule(
    "/src/lib/components/artefact/EnvironmentReviewButton.svelte",
  ));
  ({ default: EnvironmentExpandable } = await vite.ssrLoadModule(
    "/src/lib/components/artefact/EnvironmentExpandable.svelte",
  ));
  ({ default: ArtefactSignoffButton } = await vite.ssrLoadModule(
    "/src/lib/components/artefact/ArtefactSignoffButton.svelte",
  ));
  ({ default: TestPlanExpandable } = await vite.ssrLoadModule(
    "/src/lib/components/artefact/TestPlanExpandable.svelte",
  ));

  const buildResult =
    /** @type {{ output: { type: string; code: string }[] }[]} */ (
      /** @type {unknown} */ (
        await build({
          configFile: false,
          plugins: [
            svelte({ compilerOptions: { runes: true } }),
            {
              name: "test-app-modules",
              resolveId(id) {
                if (id.startsWith("$app/")) return `\0test:${id}`;
              },
              load(id) {
                if (id === "\0test:$app/state") {
                  return 'export const page = { url: new URL("http://localhost/snaps/1") };';
                }
                if (id === "\0test:$app/paths") {
                  return 'export const base = ""; export const resolve = (path) => path;';
                }
                if (id === "\0test:$app/navigation") {
                  return "export const goto = () => Promise.resolve();";
                }
              },
            },
          ],
          resolve: { alias: { $lib: resolve("src/lib") } },
          build: {
            write: false,
            lib: {
              entry: "tests/comment-editor-entry.js",
              formats: ["es"],
            },
            rolldownOptions: { output: { codeSplitting: false } },
          },
        })
      )
    );
  const bundle = buildResult[0]?.output.find((item) => item.type === "chunk");
  if (!bundle) throw new Error("Comment editor test bundle was not generated");
  browserWindow = new Window();
  for (const name of [
    "window",
    "document",
    "navigator",
    "Comment",
    "Text",
    "Node",
    "Element",
    "HTMLElement",
    "Event",
    "KeyboardEvent",
    "FocusEvent",
    "ResizeObserver",
  ]) {
    originalGlobals.set(
      name,
      Object.getOwnPropertyDescriptor(globalThis, name),
    );
    Object.defineProperty(globalThis, name, {
      configurable: true,
      value:
        name === "window" ? browserWindow : Reflect.get(browserWindow, name),
    });
  }
  const importedModule = /** @type {unknown} */ (
    await import(
      `data:text/javascript;base64,${Buffer.from(bundle.code).toString("base64")}`
    )
  );
  const testModule =
    /** @type {typeof import("../tests/comment-editor-entry")} */ (
      importedModule
    );
  ({ mountCommentEditor, unmountCommentEditor, mountArtefactPage } =
    testModule);
});

after(async () => {
  await vite?.close();
  for (const [name, descriptor] of originalGlobals) {
    if (descriptor) Object.defineProperty(globalThis, name, descriptor);
    else Reflect.deleteProperty(globalThis, name);
  }
  await browserWindow?.happyDOM.abort();
});

void test("artefact comment editor cancels drafts and submits Enter only once", async () => {
  if (!browserWindow || !mountCommentEditor || !unmountCommentEditor) {
    throw new Error("Comment editor browser test modules were not loaded");
  }
  const originalFetch = globalThis.fetch;
  if (!vite) throw new Error("Vite server was not started");
  const { userStore } = await vite.ssrLoadModule(
    "/src/lib/stores/user.svelte.ts",
  );
  // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
  userStore.current = { id: 5, teams: [], is_admin: true };
  // eslint-disable-next-line @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access
  await userStore.refresh(() =>
    Promise.resolve(jsonResponse({ id: 5, teams: [], is_admin: true })),
  );
  /** @type {{ method: string; body: string | undefined }[]} */
  const patches = [];
  // eslint-disable-next-line @typescript-eslint/require-await
  globalThis.fetch = async (url, options = {}) => {
    const requestUrl =
      typeof url === "string"
        ? url
        : url instanceof Request
          ? url.url
          : url.toString();
    const path = new URL(requestUrl).pathname;
    const method = options.method ?? "GET";
    if (path.endsWith("/artefacts/1") && method === "PATCH") {
      patches.push({
        method,
        body: typeof options.body === "string" ? options.body : undefined,
      });
      return jsonResponse({ id: 1, comment: "saved comment" });
    }
    if (path.endsWith("/artefacts/1")) {
      return jsonResponse({ id: 1, comment: "saved comment" });
    }
    return jsonResponse([]);
  };

  const domWindow = browserWindow;
  const target = domWindow.document.createElement("div");
  domWindow.document.body.append(target);
  const store = await initializeStore();
  // @ts-expect-error Happy DOM's element types differ from the DOM lib types.
  const component = mountCommentEditor(target, {
    artefact: { id: 1, comment: "saved comment" },
    store,
  });

  /** @param {string} value */
  const enterDraft = (value) => {
    const textarea = target.querySelector("textarea");
    assert.ok(textarea, "comment editor should be a textarea");
    textarea.value = value;
    textarea.dispatchEvent(new domWindow.Event("input", { bubbles: true }));
    return textarea;
  };
  /**
   * @param {{ dispatchEvent: (event: import("happy-dom").Event) => boolean }} element
   * @param {string} key
   */
  const keydown = (element, key) =>
    element.dispatchEvent(
      new domWindow.KeyboardEvent("keydown", {
        key,
        bubbles: true,
        cancelable: true,
      }),
    );
  const flush = () => new Promise((resolve) => setTimeout(resolve, 0));

  try {
    /** @type {HTMLButtonElement} */ (
      /** @type {unknown} */ (
        target.querySelector('[aria-label="Edit comment"]')
      )
    ).click();
    await flush();
    const canceledEditor = enterDraft("discard me");
    keydown(canceledEditor, "Escape");
    await flush();
    assert.equal(target.querySelector("textarea"), null);
    assert.match(target.textContent, /saved comment/);
    assert.deepEqual(patches, [], "Escape must discard without a PATCH");

    /** @type {HTMLButtonElement} */ (
      /** @type {unknown} */ (target.querySelector(".comment-display"))
    ).click();
    await flush();
    const savedEditor = enterDraft("new comment");
    keydown(savedEditor, "Enter");
    savedEditor.dispatchEvent(new domWindow.FocusEvent("blur"));
    await flush();

    assert.equal(patches.length, 1, "Enter followed by blur submits once");
    assert.deepEqual(patches[0], {
      method: "PATCH",
      body: JSON.stringify({ comment: "new comment" }),
    });
  } finally {
    await unmountCommentEditor(component);
    target.remove();
    globalThis.fetch = originalFetch;
    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
    userStore.current = null;
  }
});

void test("artefact comment editor is unavailable without artefact permission", async () => {
  if (!browserWindow || !mountCommentEditor || !unmountCommentEditor) {
    throw new Error("Comment editor browser test modules were not loaded");
  }
  const target = browserWindow.document.createElement("div");
  browserWindow.document.body.append(target);
  const store = {
    canChangeArtefact: false,
    updateArtefactComment: () => assert.fail("unauthorized mutation"),
  };
  // @ts-expect-error Test intentionally supplies only the component contract under test.
  const component = mountCommentEditor(target, {
    artefact: { id: 1, comment: "read only" },
    store,
  });
  try {
    assert.equal(target.querySelector('[aria-label="Edit comment"]'), null);
    assert.equal(target.querySelector("textarea"), null);
    const display = target.querySelector(".comment-display");
    assert.ok(display);
    display.dispatchEvent(
      new browserWindow.MouseEvent("click", { bubbles: true }),
    );
    await new Promise((resolve) => setTimeout(resolve, 0));
    assert.equal(target.querySelector("textarea"), null);
  } finally {
    await unmountCommentEditor(component);
    target.remove();
  }
});

function deferred() {
  /** @type {((value: Response) => void) | undefined} */
  let resolve;
  /** @type {((reason?: unknown) => void) | undefined} */
  let reject;
  const promise = /** @type {Promise<Response>} */ (
    new Promise((res, rej) => {
      resolve = res;
      reject = rej;
    })
  );
  return {
    promise,
    resolve: /** @param {Response} value */ (value) => {
      if (!resolve) throw new Error("Promise resolver is not set");
      resolve(value);
    },
    reject: /** @param {unknown} [reason] */ (reason) => {
      if (!reject) throw new Error("Promise rejecter is not set");
      reject(reason);
    },
  };
}

/** @param {unknown} data */
function jsonResponse(data) {
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

void test("sidebar toggle names its action in both states", async () => {
  if (!browserWindow || !mountArtefactPage || !unmountCommentEditor) {
    throw new Error("Artefact page browser test modules were not loaded");
  }
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (url) => {
    const path = new URL(url instanceof Request ? url.url : url).pathname;
    return Promise.resolve(
      path.endsWith("/artefacts/1")
        ? jsonResponse({
            id: 1,
            name: "Test artefact",
            family: "snap",
            status: "UNDECIDED",
            reviewers: [],
            comment: "",
          })
        : jsonResponse([]),
    );
  };
  const target = browserWindow.document.createElement("div");
  browserWindow.document.body.append(target);
  // @ts-expect-error Happy DOM's element types differ from DOM lib types.
  const component = mountArtefactPage(target, {
    data: {
      artefactId: 1,
      family: {
        name: "snaps",
        api_name: "snap",
        friendly_name: "Snaps",
        stages: [],
        columns: [],
        filters: [],
      },
    },
  });
  const flush = () => new Promise((resolve) => setTimeout(resolve, 0));
  try {
    await flush();
    const toggle = target.querySelector("button.sidebar-toggle");
    assert.ok(toggle, target.innerHTML);
    assert.equal(toggle.getAttribute("aria-label"), "Hide sidebar");
    assert.equal(toggle.getAttribute("aria-pressed"), "true");
    assert.ok(target.querySelector(".sidebar"));
    toggle.dispatchEvent(
      new browserWindow.MouseEvent("click", { bubbles: true }),
    );
    await flush();
    assert.equal(toggle.getAttribute("aria-label"), "Show sidebar");
    assert.equal(toggle.getAttribute("aria-pressed"), "false");
    assert.equal(target.querySelector(".sidebar"), null);
    toggle.dispatchEvent(
      new browserWindow.MouseEvent("click", { bubbles: true }),
    );
    await flush();
    assert.equal(toggle.getAttribute("aria-label"), "Hide sidebar");
    assert.ok(target.querySelector(".sidebar"));
  } finally {
    await unmountCommentEditor(component);
    target.remove();
    globalThis.fetch = originalFetch;
  }
});

void test("superseded session responses return no authorization evidence", async () => {
  if (!vite) throw new Error("Vite server was not started");
  const { userStore } =
    /** @type {typeof import("../src/lib/stores/user.svelte")} */ (
      await vite.ssrLoadModule("/src/lib/stores/user.svelte.ts")
    );
  const admin = {
    id: 5,
    teams: [],
    is_admin: true,
    email: "admin@example.com",
    name: "Admin",
    launchpad_handle: null,
  };
  try {
    for (const olderAuthenticated of [true, false]) {
      const older = deferred();
      const newer = deferred();
      const olderRequest = userStore.refresh(() => older.promise);
      const newerRequest = userStore.refresh(() => newer.promise);
      newer.resolve(
        olderAuthenticated
          ? new Response("{}", { status: 401 })
          : jsonResponse(admin),
      );
      assert.equal(
        await newerRequest,
        olderAuthenticated ? "unauthenticated" : "authenticated",
      );
      older.resolve(
        olderAuthenticated
          ? jsonResponse(admin)
          : new Response("{}", { status: 401 }),
      );
      assert.equal(await olderRequest, "unknown");
      assert.deepEqual(userStore.current, olderAuthenticated ? null : admin);
      assert.equal(userStore.isConfirmedAdmin, !olderAuthenticated);
      assert.equal(userStore.isLoggedIn, !olderAuthenticated);
    }
  } finally {
    await userStore.refresh(() =>
      Promise.resolve(new Response("{}", { status: 401 })),
    );
  }
});

void test("superseded init failures preserve the newer page without refreshing the session", async () => {
  if (!ArtefactPageStore) throw new Error("Store module was not loaded");
  const originalFetch = globalThis.fetch;
  try {
    // Cover both the primary request and a required secondary request failing
    // after navigation B has finished loading, including authorization errors.
    for (const failedPath of ["/artefacts/1", "/artefacts/1/builds"]) {
      for (const status of [401, 403, 500]) {
        const older = deferred();
        const started = deferred();
        let sessionChecks = 0;
        globalThis.fetch = (url) => {
          const path = new URL(url instanceof Request ? url.url : url).pathname;
          if (path.endsWith("/users/me")) {
            sessionChecks++;
            return Promise.resolve(new Response("{}", { status: 401 }));
          }
          if (path.endsWith(failedPath)) {
            started.resolve(jsonResponse(null));
            return older.promise;
          }
          if (/\/artefacts\/[12]$/.test(path)) {
            return Promise.resolve(
              jsonResponse({ id: Number(path.slice(-1)) }),
            );
          }
          return Promise.resolve(jsonResponse([]));
        };
        /** @type {import("../src/lib/stores/artefact-page.svelte").ArtefactPageStore} */
        const store = new ArtefactPageStore();
        const olderRequest = store.init(1);
        await started.promise;
        await store.init(2);
        const newerArtefact = store.artefact;
        assert.equal(newerArtefact?.id, 2);
        assert.equal(store.accessError, null);
        assert.equal(store.loading, false);
        older.resolve(new Response("{}", { status }));
        await olderRequest;
        assert.equal(store.artefact, newerArtefact, `${failedPath}: ${status}`);
        assert.equal(store.accessError, null);
        assert.equal(store.loading, false);
        assert.equal(sessionChecks, 0, "stale failures must not refresh /me");
      }
    }
  } finally {
    globalThis.fetch = originalFetch;
  }
});

void test("artefact route IDs require complete positive safe integers", () => {
  assert.ok(parseArtefactId);
  for (const value of ["1", "42", "9007199254740991"]) {
    assert.equal(parseArtefactId(value), Number(value));
  }
  for (const value of [
    "",
    "0",
    "-1",
    "1tail",
    "1.5",
    " 1",
    "+1",
    "9007199254740992",
  ]) {
    assert.equal(parseArtefactId(value), null, value);
  }
});

void test("execution deep-link IDs require complete positive safe integers", async () => {
  assert.ok(parsePositiveSafeInteger);
  for (const value of ["1", "42", "9007199254740991"]) {
    assert.equal(parsePositiveSafeInteger(value), Number(value));
  }
  for (const value of [
    "",
    "0",
    "-1",
    "1tail",
    "1.5",
    " 1",
    "+1",
    "9007199254740992",
  ]) {
    assert.equal(parsePositiveSafeInteger(value), null, value);
  }

  const components = await Promise.all(
    [
      "EnvironmentExpandable",
      "TestPlanExpandable",
      "TestExecutionExpandable",
    ].map((name) =>
      readFile(
        new URL(
          `../src/lib/components/artefact/${name}.svelte`,
          import.meta.url,
        ),
        "utf8",
      ),
    ),
  );
  for (const source of components) {
    assert.match(source, /parsePositiveSafeInteger\(/);
    assert.doesNotMatch(source, /parseInt\(targetExecutionId/);
  }
});

void test("malformed filter encoding is ignored without throwing", () => {
  assert.ok(decodeFilterValues);
  assert.deepEqual(decodeFilterValues("env%20one,broken%,FAILED"), [
    "env one",
    "FAILED",
  ]);
  assert.deepEqual(decodeFilterValues("%E0%A4%A"), []);
  assert.deepEqual(decodeFilterValues(null), []);
});

void test("execution filter matches any run while plan-last-run uses latest status per plan", () => {
  assert.ok(matchesExecutionStatuses);
  assert.ok(matchesPlanLastRunStatuses);
  assert.ok(latestPlanStatuses);
  /** @type {{ status: import("../src/lib/types/openapi").TestExecutionStatus; test_plan: string }[]} */
  const runs = [
    { status: "PASSED", test_plan: "alpha" },
    { status: "FAILED", test_plan: "alpha" },
    { status: "IN_PROGRESS", test_plan: "beta" },
    { status: "PASSED", test_plan: "beta" },
  ];
  assert.equal(matchesExecutionStatuses(runs, ["FAILED"]), true);
  assert.equal(matchesExecutionStatuses(runs, ["CANCELLED"]), false);
  assert.equal(matchesPlanLastRunStatuses(runs, ["PASSED"]), true);
  assert.equal(matchesPlanLastRunStatuses(runs, ["FAILED"]), false);
  assert.equal(matchesPlanLastRunStatuses(runs, ["IN_PROGRESS"]), true);
  assert.deepEqual(latestPlanStatuses(runs), ["PASSED", "IN_PROGRESS"]);
});

void test("rerun candidates use each plan's latest run and selected plan statuses", () => {
  assert.ok(matchingLatestPlanRuns);
  /** @type {{ id: number; status: import("../src/lib/types/openapi").TestExecutionStatus; test_plan: string; artefact_build_id: number; environment: { id: number; name: string; architecture: string } }[]} */
  const runs = [
    {
      id: 5,
      status: "PASSED",
      test_plan: "alpha",
      artefact_build_id: 1,
      environment: { id: 9, name: "env", architecture: "amd64" },
    },
    {
      id: 4,
      status: "FAILED",
      test_plan: "alpha",
      artefact_build_id: 1,
      environment: { id: 9, name: "env", architecture: "amd64" },
    },
    {
      id: 3,
      status: "FAILED",
      test_plan: "beta",
      artefact_build_id: 1,
      environment: { id: 9, name: "env", architecture: "amd64" },
    },
    {
      id: 2,
      status: "PASSED",
      test_plan: "beta",
      artefact_build_id: 1,
      environment: { id: 9, name: "env", architecture: "amd64" },
    },
    {
      id: 1,
      status: "FAILED",
      test_plan: "gamma",
      artefact_build_id: 1,
      environment: { id: 9, name: "env", architecture: "amd64" },
    },
  ];
  assert.deepEqual(
    matchingLatestPlanRuns(runs, ["FAILED"]).map(({ id }) => id),
    [3, 1],
  );
  assert.deepEqual(
    matchingLatestPlanRuns(runs, []).map(({ id }) => id),
    [5, 3, 1],
  );
});

void test("expanded content fetch requires an expanded parent and unloaded content", () => {
  assert.ok(shouldFetchExpandedData);
  assert.equal(shouldFetchExpandedData(false, true, true), false);
  assert.equal(shouldFetchExpandedData(true, false, true), false);
  assert.equal(shouldFetchExpandedData(true, true, false), false);
  assert.equal(shouldFetchExpandedData(true, true, true), true);
});

void test("event and result requests stay gated through collapsed component ancestors", async () => {
  assert.ok(shouldFetchExpandedData);
  const fetchIfExpanded = shouldFetchExpandedData;
  /** @param {string} name */
  const componentPath = (name) =>
    new URL(`../src/lib/components/artefact/${name}.svelte`, import.meta.url);
  const [environment, plan, execution, eventLog, resultGroup] =
    await Promise.all(
      [
        "EnvironmentExpandable",
        "TestPlanExpandable",
        "TestExecutionExpandable",
        "EventLogExpandable",
        "TestResultsGroup",
      ].map((name) => readFile(componentPath(name), "utf8")),
    );

  // The nested props carry each ancestor's open state down to both actual
  // request effects, which use the tested predicate before calling the store.
  assert.match(environment, /parentExpanded=\{open\}/);
  assert.match(plan, /parentExpanded=\{open && parentExpanded\}/);
  assert.match(execution, /parentExpanded=\{open && parentExpanded\}/);
  assert.match(
    execution,
    /shouldFetchExpandedData\(parentExpanded, open, showResults\)[\s\S]*?store\.fetchTestResults\(run\.id\)/,
  );
  assert.match(
    eventLog,
    /shouldFetchExpandedData\(parentExpanded, open, events === undefined\)[\s\S]*?store\.fetchTestEvents\(executionId\)/,
  );
  assert.match(
    resultGroup,
    /shouldFetchExpandedData\([\s\S]*?parentExpanded,[\s\S]*?open \|\| isDeepLinkTarget,[\s\S]*?allResults === undefined,[\s\S]*?\) &&[\s\S]*?fetchResults\(\)/,
  );

  assert.equal(fetchIfExpanded(false, true, true), false);
  assert.equal(fetchIfExpanded(true, false, true), false);
  assert.equal(fetchIfExpanded(true, true, true), true);
});

void test("artefact load distinguishes unauthenticated, forbidden, and inconclusive checks", async () => {
  const originalFetch = globalThis.fetch;
  const cases = [
    { pageStatus: 401, sessionStatus: 401, expected: "requiresLogin" },
    { pageStatus: 403, sessionStatus: 200, expected: "forbidden" },
    { pageStatus: 401, sessionStatus: 503, expected: "sessionCheckFailed" },
  ];

  try {
    for (const testCase of cases) {
      globalThis.fetch = (url) => {
        const requestUrl =
          url instanceof Request ? url.url : url instanceof URL ? url : url;
        const path = new URL(requestUrl).pathname;
        if (path.endsWith("/users/me")) {
          return Promise.resolve(
            testCase.sessionStatus === 200
              ? jsonResponse({ id: 5 })
              : new Response("{}", { status: testCase.sessionStatus }),
          );
        }
        if (path.endsWith("/artefacts/1")) {
          return Promise.resolve(
            testCase.pageStatus === 200
              ? jsonResponse({ id: 1 })
              : new Response("{}", { status: testCase.pageStatus }),
          );
        }
        return Promise.resolve(jsonResponse([]));
      };

      const store = ArtefactPageStore && new ArtefactPageStore();
      if (!store) throw new Error("Store module was not loaded");
      await store.init(1);
      assert.equal(store.accessError, testCase.expected);
    }
  } finally {
    globalThis.fetch = originalFetch;
  }
});

void test("artefact store rejects data whose family differs from the route", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (url) => {
    const requestUrl =
      url instanceof Request ? url.url : url instanceof URL ? url : url;
    if (new URL(requestUrl).pathname.endsWith("/artefacts/1")) {
      return Promise.resolve(jsonResponse({ id: 1, family: "deb" }));
    }
    return Promise.resolve(jsonResponse([]));
  };

  try {
    const store = ArtefactPageStore && new ArtefactPageStore();
    if (!store) throw new Error("Store module was not loaded");
    await store.init(1, "snap");
    assert.equal(store.accessError, "familyMismatch");
    assert.equal(store.artefact, null);
    assert.equal(store.loading, false);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

void test("artefact detail route maps its plural family name to the API family", async () => {
  const familiesPath = new URL("../static/families.json", import.meta.url);
  const routePath = new URL(
    "../src/routes/[family]/[artefactId]/+page.svelte",
    import.meta.url,
  );
  const [familiesJson, routeSource] = await Promise.all([
    readFile(familiesPath, "utf8"),
    readFile(routePath, "utf8"),
  ]);
  // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
  const { families } =
    /** @type {{ families: { name: string; api_name: string }[] }} */ (
      JSON.parse(familiesJson)
    );
  const routeFamily = families.find(({ name }) => name === "snaps");
  assert.ok(routeFamily);
  assert.equal(routeFamily.api_name, "snap");
  assert.match(routeSource, /store\.init\(artefactId, family\.api_name\)/);

  const originalFetch = globalThis.fetch;
  globalThis.fetch = (url) => {
    const requestUrl =
      url instanceof Request ? url.url : url instanceof URL ? url : url;
    const path = new URL(requestUrl).pathname;
    if (path.endsWith("/artefacts/1")) {
      return Promise.resolve(jsonResponse({ id: 1, family: "snap" }));
    }
    return Promise.resolve(jsonResponse([]));
  };

  try {
    const store = ArtefactPageStore && new ArtefactPageStore();
    if (!store) throw new Error("Store module was not loaded");
    await store.init(1, routeFamily.api_name);

    assert.equal(store.accessError, null);
    assert.equal(store.artefact?.family, "snap");
  } finally {
    globalThis.fetch = originalFetch;
  }
});

async function initializeStore() {
  if (!ArtefactPageStore) throw new Error("Store module was not loaded");
  const store = new ArtefactPageStore();
  await store.init(1);
  return store;
}

/**
 * @param {{
 *   results?: (Promise<Response> | Response)[],
 *   events?: (Promise<Response> | Response)[],
 *   mutations?: (Promise<Response> | Response)[],
 *   reportedIssuesStatus?: number,
 * }} [responses]
 */
function installFetch(responses = {}) {
  const {
    results = [],
    events = [],
    mutations = [],
    reportedIssuesStatus,
  } = responses;
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url, options = {}) => {
    const requestUrl =
      typeof url === "string"
        ? url
        : url instanceof Request
          ? url.url
          : url.toString();
    const path = new URL(requestUrl).pathname;
    if (
      (path.endsWith("/reported-issues") ||
        path.endsWith("/environment-reviews")) &&
      reportedIssuesStatus
    ) {
      return new Response(JSON.stringify({ detail: "Forbidden" }), {
        status: reportedIssuesStatus,
        headers: { "Content-Type": "application/json" },
      });
    }
    if (path.endsWith("/test-results")) {
      const response = results.shift();
      return response ?? jsonResponse([]);
    }
    if (path.endsWith("/status_update")) {
      const response = events.shift();
      return response ?? jsonResponse([]);
    }
    if (
      path.includes("/artefacts/") &&
      options.method === "PATCH" &&
      mutations.length
    ) {
      return mutations.shift() ?? jsonResponse({ id: 1 });
    }
    if (path.endsWith("/artefacts/1")) return jsonResponse({ id: 1 });
    if (path.endsWith("/artefacts/2")) return jsonResponse({ id: 2 });
    if (path.includes("/artefacts/")) return jsonResponse([]);
    return jsonResponse([]);
  };
  return () => {
    globalThis.fetch = originalFetch;
  };
}

void test("reinitialization prevents old results and events successes from caching", async () => {
  const oldResults = deferred();
  const oldEvents = deferred();
  const restoreFetch = installFetch({
    results: [oldResults.promise],
    events: [oldEvents.promise],
  });

  try {
    const store = await initializeStore();
    const resultsRequest = store.fetchTestResults(10);
    const eventsRequest = store.fetchTestEvents(10);

    await store.init(2);
    oldResults.resolve(jsonResponse([{ id: 1 }]));
    oldEvents.resolve(jsonResponse([{ id: 2 }]));
    await Promise.all([resultsRequest, eventsRequest]);

    assert.equal(store.getTestResults(10), undefined);
    assert.equal(store.getTestEvents(10), undefined);
  } finally {
    restoreFetch();
  }
});

void test("older same-page mutation responses cannot overwrite newer state", async () => {
  const older = deferred();
  const newer = deferred();
  const restoreFetch = installFetch({
    mutations: [older.promise, newer.promise],
  });

  try {
    const store = await initializeStore();
    const olderRequest = store.updateArtefactStatus(1, "APPROVED");
    const newerRequest = store.updateArtefactStatus(1, "MARKED_AS_FAILED");

    newer.resolve(jsonResponse({ id: 1, status: "MARKED_AS_FAILED" }));
    await newerRequest;
    older.resolve(jsonResponse({ id: 1, status: "APPROVED" }));
    await olderRequest;

    assert.equal(store.artefact?.status, "MARKED_AS_FAILED");
  } finally {
    restoreFetch();
  }
});

void test("mutation responses from a previous page cannot overwrite reinitialized state", async () => {
  const oldMutation = deferred();
  const restoreFetch = installFetch({ mutations: [oldMutation.promise] });

  try {
    const store = await initializeStore();
    const mutationRequest = store.updateArtefactStatus(1, "APPROVED");

    await store.init(2);
    oldMutation.resolve(jsonResponse({ id: 1, status: "APPROVED" }));
    await mutationRequest;

    assert.equal(store.artefact?.id, 2);
  } finally {
    restoreFetch();
  }
});

void test("mutation for a stale artefact ID cannot update the active page", async () => {
  const staleMutation = deferred();
  const restoreFetch = installFetch({ mutations: [staleMutation.promise] });

  try {
    const store = await initializeStore();
    await store.init(2);

    // The page is loaded for artefact 2, but a delayed caller still submits
    // a mutation for artefact 1 without causing another init generation.
    const mutationRequest = store.updateArtefactStatus(1, "APPROVED");
    staleMutation.resolve(jsonResponse({ id: 1, status: "APPROVED" }));
    await mutationRequest;

    assert.equal(store.artefact?.id, 2);
  } finally {
    restoreFetch();
  }
});

void test("review mutation for a stale artefact ID cannot update active reviews", async () => {
  const staleMutation = deferred();
  const restoreFetch = installFetch({ mutations: [staleMutation.promise] });

  try {
    const store = await initializeStore();
    await store.init(2);
    store.reviews = [
      {
        id: 7,
        review_decision: [],
        review_comment: "",
        environment: { id: 1, name: "env", architecture: "amd64" },
        artefact_build: { id: 1, architecture: "amd64", revision: null },
        reviewers: [],
      },
    ];

    const mutationRequest = store.submitReview(1, 7, {
      review_decision: ["APPROVED_ALL_TESTS_PASS"],
      review_comment: "Reviewed",
    });
    staleMutation.resolve(
      jsonResponse({
        id: 7,
        review_decision: ["APPROVED_ALL_TESTS_PASS"],
        review_comment: "Reviewed",
      }),
    );
    await mutationRequest;

    assert.deepEqual(store.reviews[0]?.review_decision, []);
  } finally {
    restoreFetch();
  }
});

void test("optional reported-issue 403s do not fail core page loading or show a global error", async () => {
  if (!vite) throw new Error("Vite server was not started");
  const { errorStore } =
    /** @type {{ errorStore: { clear: () => void, hasError: boolean } }} */ (
      await vite.ssrLoadModule("/src/lib/stores/error.svelte.ts")
    );
  errorStore.clear();
  const restoreFetch = installFetch({ reportedIssuesStatus: 403 });

  try {
    const store = await initializeStore();

    assert.equal(store.loading, false);
    assert.equal(store.artefact?.id, 1);
    assert.deepEqual(store.builds, []);
    assert.deepEqual(store.reviews, []);
    assert.deepEqual(store.environmentIssues, []);
    assert.deepEqual(store.testIssues, []);
    assert.equal(errorStore.hasError, false);
  } finally {
    restoreFetch();
    errorStore.clear();
  }
});

void test("environment review 403 does not hide an accessible artefact", async () => {
  if (!vite) throw new Error("Vite server was not started");
  const { errorStore } =
    /** @type {{ errorStore: { clear: () => void, hasError: boolean } }} */ (
      await vite.ssrLoadModule("/src/lib/stores/error.svelte.ts")
    );
  errorStore.clear();
  const restoreFetch = installFetch({ reportedIssuesStatus: 403 });

  try {
    const store = await initializeStore();
    assert.equal(store.loading, false);
    assert.equal(store.accessError, null);
    assert.equal(store.artefact?.id, 1);
    assert.deepEqual(store.reviews, []);
    assert.equal(errorStore.hasError, false);
  } finally {
    restoreFetch();
    errorStore.clear();
  }
});

void test("environment review 403 preserves accessible artefact executions", async () => {
  if (!vite) throw new Error("Vite server was not started");
  const { errorStore } =
    /** @type {{ errorStore: { clear: () => void, hasError: boolean } }} */ (
      await vite.ssrLoadModule("/src/lib/stores/error.svelte.ts")
    );
  const originalFetch = globalThis.fetch;
  errorStore.clear();
  const { userStore } = await vite.ssrLoadModule(
    "/src/lib/stores/user.svelte.ts",
  );
  // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
  userStore.current = {
    id: 5,
    teams: [{ permissions: ["change_artefact"] }],
    is_admin: false,
  };
  globalThis.fetch = (url) => {
    const requestUrl =
      url instanceof Request ? url.url : url instanceof URL ? url : url;
    const path = new URL(requestUrl).pathname;
    if (path.endsWith("/environment-reviews")) {
      return Promise.resolve(new Response("{}", { status: 403 }));
    }
    if (path.endsWith("/builds")) {
      return Promise.resolve(
        jsonResponse([
          {
            id: 12,
            architecture: "amd64",
            revision: 1,
            bundled_in: [],
            test_executions: [
              {
                id: 34,
                status: "PASSED",
                test_plan: "visible plan",
                execution_metadata: {},
                relevant_links: [],
                created_at: "2026-01-01T00:00:00Z",
                environment: {
                  id: 56,
                  name: "accessible environment",
                  architecture: "amd64",
                },
              },
            ],
          },
        ]),
      );
    }
    if (path.endsWith("/artefacts/1")) {
      return Promise.resolve(jsonResponse({ id: 1 }));
    }
    return Promise.resolve(jsonResponse([]));
  };

  try {
    const store = await initializeStore();
    assert.equal(store.loading, false);
    assert.equal(store.artefact?.id, 1);
    assert.equal(store.builds.length, 1);
    assert.deepEqual(store.reviews, []);
    assert.equal(store.reviewsAvailable, false);
    assert.deepEqual(
      store.allEnvironments.map((environment) => ({
        name: environment.name,
        hasReview: environment.review !== null,
        executions: environment.runsDescending.map((run) => run.id),
      })),
      [
        {
          name: "accessible environment",
          hasReview: false,
          executions: [34],
        },
      ],
    );
    if (!render || !EnvironmentExpandable) {
      throw new Error("Environment component test modules were not loaded");
    }
    const environmentBody = render(EnvironmentExpandable, {
      props: {
        env: store.allEnvironments[0],
        store,
        artefactId: 1,
      },
    }).body;
    assert.match(environmentBody, /accessible environment/);
    assert.doesNotMatch(environmentBody, /Undecided/);
    assert.doesNotMatch(environmentBody, /<button class="trigger/);
    assert.equal(errorStore.hasError, false);
  } finally {
    globalThis.fetch = originalFetch;
    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
    userStore.current = null;
    errorStore.clear();
  }
});

void test("successful empty and partial reviews preserve every build execution without inventing review controls", async () => {
  if (
    !vite ||
    !render ||
    !EnvironmentExpandable ||
    !BulkEnvironmentSelectionControls
  ) {
    throw new Error("Environment component test modules were not loaded");
  }
  const { userStore } =
    /** @type {typeof import("../src/lib/stores/user.svelte")} */ (
      await vite.ssrLoadModule("/src/lib/stores/user.svelte.ts")
    );
  const originalUser = userStore.current;
  const originalFetch = globalThis.fetch;
  const environment = {
    id: 10,
    name: "shared environment",
    architecture: "amd64",
  };
  const otherEnvironment = {
    ...environment,
    id: 20,
    name: "other environment",
  };
  const review = {
    id: 101,
    environment,
    artefact_build: { id: 1, architecture: "amd64", revision: 1 },
    review_decision: [],
    review_comment: "",
    reviewers: [],
  };
  const builds = [1, 2].map((id) => ({
    id,
    architecture: "amd64",
    revision: id,
    bundled_in: [],
    test_executions: [environment, environment, otherEnvironment].map(
      (env, index) => ({
        id: id * 10 + index,
        environment: env,
        status: "PASSED",
        test_plan: "visible plan",
        execution_metadata: {},
        relevant_links: [],
        created_at: "2026-01-01T00:00:00Z",
      }),
    ),
  }));
  try {
    userStore.current = {
      id: 5,
      email: "reviewer@example.com",
      name: "Reviewer",
      launchpad_handle: null,
      teams: [{ permissions: ["change_environment_review"] }],
      is_admin: false,
    };
    for (const reviews of [[], [review]]) {
      globalThis.fetch = (url) => {
        const path = new URL(url instanceof Request ? url.url : url).pathname;
        if (path.endsWith("/environment-reviews"))
          return Promise.resolve(jsonResponse(reviews));
        if (path.endsWith("/builds"))
          return Promise.resolve(jsonResponse(builds));
        if (path.endsWith("/artefacts/1"))
          return Promise.resolve(jsonResponse({ id: 1 }));
        return Promise.resolve(jsonResponse([]));
      };
      const store = await initializeStore();
      assert.equal(store.loading, false);
      assert.equal(store.accessError, null);
      assert.equal(store.reviewsAvailable, true);
      assert.deepEqual(store.reviews, reviews, "no synthetic reviews");
      assert.equal(store.enrichedExecutions.length, 6);
      assert.deepEqual(
        store.allEnvironments.map((row) => ({
          key: row.key,
          reviewId: row.review?.id ?? null,
          runs: row.runsDescending.map((run) => run.id),
        })),
        [
          {
            key: reviews.length ? "review:101" : "build:1:environment:10",
            reviewId: reviews.length ? 101 : null,
            runs: [11, 10],
          },
          { key: "build:1:environment:20", reviewId: null, runs: [12] },
          { key: "build:2:environment:10", reviewId: null, runs: [21, 20] },
          { key: "build:2:environment:20", reviewId: null, runs: [22] },
        ],
      );
      const unmatchedRows = store.allEnvironments.filter(
        (row) => row.review === null,
      );
      for (const env of store.allEnvironments) {
        const body = render(EnvironmentExpandable, {
          props: { env, store, artefactId: 1 },
        }).body;
        assert.match(body, new RegExp(env.name));
        if (env.review) {
          assert.match(body, /env-checkbox/);
          assert.match(body, /<button class="trigger/);
        } else {
          assert.doesNotMatch(body, /env-checkbox/);
          assert.doesNotMatch(body, /<button class="trigger/);
          assert.doesNotMatch(body, /Undecided/);
        }
      }
      const bulkBody = render(BulkEnvironmentSelectionControls, {
        props: {
          environments: unmatchedRows,
          artefactId: 1,
          store: { isSelected: () => true },
        },
      }).body;
      assert.match(bulkBody, /0 of/);
      assert.doesNotMatch(bulkBody, />Review \d+ environment/);
    }
  } finally {
    globalThis.fetch = originalFetch;
    userStore.current = originalUser;
  }
});

void test("environment review server and network failures stay visible", async () => {
  if (!vite) throw new Error("Vite server was not started");
  const { errorStore } =
    /** @type {{ errorStore: { clear: () => void, hasError: boolean, message: string | null } }} */ (
      await vite.ssrLoadModule("/src/lib/stores/error.svelte.ts")
    );
  const originalFetch = globalThis.fetch;
  const responses = [
    {
      name: "server error",
      response: () => Promise.resolve(new Response("{}", { status: 500 })),
      message: "Request failed: 500",
    },
    {
      name: "network error",
      response: () => Promise.reject(new Error("network unavailable")),
      message: "network unavailable",
    },
  ];
  const failures = responses.map((response) => ({
    ...response,
    path: "/environment-reviews",
  }));

  try {
    for (const failure of failures) {
      errorStore.clear();
      globalThis.fetch = (url) => {
        const requestUrl =
          url instanceof Request ? url.url : url instanceof URL ? url : url;
        const path = new URL(requestUrl).pathname;
        if (path.endsWith(failure.path)) return failure.response();
        if (path.endsWith("/artefacts/1")) {
          return Promise.resolve(jsonResponse({ id: 1 }));
        }
        return Promise.resolve(jsonResponse([]));
      };

      const store = await initializeStore();
      assert.equal(store.loading, false, `${failure.name}: loading completes`);
      assert.equal(
        store.artefact,
        null,
        `${failure.name}: page enters the failure state`,
      );
      assert.equal(
        errorStore.hasError,
        true,
        `${failure.name}: error is visible`,
      );
      assert.equal(
        errorStore.message,
        failure.message,
        `${failure.path}: ${failure.name}`,
      );
    }
  } finally {
    globalThis.fetch = originalFetch;
    errorStore.clear();
  }
});

void test("environment issue mutations require a confirmed session", async () => {
  const originalFetch = globalThis.fetch;
  let authenticated = false;
  /** @type {string[]} */
  let permissions = [];
  /** @type {{ method: string; path: string }[]} */
  const mutationRequests = [];
  const existingIssue = {
    id: 12,
    environment_name: "amd64",
    description: "intermittent network",
    url: null,
    is_confirmed: false,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  };

  globalThis.fetch = (url, options = {}) => {
    const requestUrl =
      typeof url === "string"
        ? url
        : url instanceof Request
          ? url.url
          : url.toString();
    const path = new URL(requestUrl).pathname;
    const method = options.method ?? "GET";
    if (path.endsWith("/users/me")) {
      return Promise.resolve(
        authenticated
          ? jsonResponse({
              id: 5,
              teams: [{ permissions }],
              is_admin: false,
            })
          : new Response("{}", { status: 401 }),
      );
    }
    if (path.endsWith("/reported-issues") && method === "GET") {
      return Promise.resolve(jsonResponse([existingIssue]));
    }
    if (path.includes("/reported-issues") && method !== "GET") {
      mutationRequests.push({ method, path });
      if (method === "DELETE")
        return Promise.resolve(new Response(null, { status: 204 }));
      return Promise.resolve(
        jsonResponse({ ...existingIssue, description: "updated issue" }),
      );
    }
    if (path.endsWith("/artefacts/1"))
      return Promise.resolve(jsonResponse({ id: 1 }));
    return Promise.resolve(jsonResponse([]));
  };

  try {
    const store = await initializeStore();

    await assert.rejects(
      store.createEnvironmentIssue({
        environment_name: "amd64",
        description: "new issue",
        url: null,
        is_confirmed: false,
      }),
      /authenticated session is required/,
    );
    await assert.rejects(
      store.updateEnvironmentIssue(12, { description: "updated issue" }),
      /authenticated session is required/,
    );
    await assert.rejects(
      store.deleteEnvironmentIssue(12),
      /authenticated session is required/,
    );
    assert.deepEqual(mutationRequests, []);

    authenticated = true;
    await assert.rejects(
      store.createEnvironmentIssue({
        environment_name: "amd64",
        description: "view-only issue",
        url: null,
        is_confirmed: false,
      }),
      /mutations are not permitted/,
    );
    assert.deepEqual(mutationRequests, []);

    permissions = ["change_environment_reported_issue"];
    await store.createEnvironmentIssue({
      environment_name: "amd64",
      description: "new issue",
      url: null,
      is_confirmed: false,
    });
    await store.updateEnvironmentIssue(12, { description: "updated issue" });
    await store.deleteEnvironmentIssue(12);
    assert.deepEqual(
      mutationRequests.map(({ method }) => method),
      ["POST", "PUT", "DELETE"],
    );

    permissions = [];
    await assert.rejects(
      store.createEnvironmentIssue({
        environment_name: "amd64",
        description: "revoked issue",
        url: null,
        is_confirmed: false,
      }),
      /mutations are not permitted/,
    );
    assert.equal(mutationRequests.length, 3);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

void test("environment issue UI gates mutations on change permission", async () => {
  if (!render || !EnvironmentIssuesExpandable || !vite) {
    throw new Error("Svelte component test modules were not loaded");
  }
  const renderComponent = render;
  const issuesComponent = EnvironmentIssuesExpandable;
  const { userStore } = await vite.ssrLoadModule(
    "/src/lib/stores/user.svelte.ts",
  );
  const store = {
    environmentIssues: [
      {
        id: 1,
        environment_name: "amd64",
        description: "Issue with a URL",
        url: "https://example.com/issue/1",
        is_confirmed: false,
      },
      {
        id: 2,
        environment_name: "amd64",
        description: "Issue without a URL",
        url: null,
        is_confirmed: true,
      },
    ],
  };
  const renderIssues = () =>
    renderComponent(issuesComponent, {
      props: { environmentName: "amd64", store },
    }).body;

  // Anonymous users cannot mutate, even when a GET returns issues.
  // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
  userStore.current = null;
  let body = renderIssues();
  assert.doesNotMatch(body, />\+ add</);
  assert.doesNotMatch(body, />edit</);

  // A successful read (and a logged-in session) does not grant write access.
  // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
  userStore.current = {
    id: 5,
    teams: [{ permissions: ["view_environment_reported_issue"] }],
    is_admin: false,
  };
  body = renderIssues();
  assert.match(body, /href="https:\/\/example\.com\/issue\/1"/);
  assert.doesNotMatch(body, /href="(?:null|undefined)"/);
  assert.doesNotMatch(body, />\+ add</);
  assert.doesNotMatch(body, />edit</);

  // The explicit change grant makes controls available.
  // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
  userStore.current = {
    id: 5,
    teams: [{ permissions: ["change_environment_reported_issue"] }],
    is_admin: false,
  };
  body = renderIssues();
  assert.match(body, />\+ add</);
  assert.match(body, />edit</);

  // Administrators follow the backend permission checker's bypass.
  // eslint-disable-next-line @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access
  await userStore.refresh(() =>
    Promise.resolve(jsonResponse({ id: 5, teams: [], is_admin: true })),
  );
  body = renderIssues();
  assert.match(body, />\+ add</);
  assert.match(body, />edit</);
});

void test("environment review controls are hidden without change permission", async () => {
  if (
    !render ||
    !BulkEnvironmentSelectionControls ||
    !EnvironmentReviewButton ||
    !vite
  ) {
    throw new Error("Svelte component test modules were not loaded");
  }
  const renderComponent = render;
  const bulkControls = BulkEnvironmentSelectionControls;
  const reviewButton = EnvironmentReviewButton;
  const { userStore } =
    /** @type {typeof import("../src/lib/stores/user.svelte")} */ (
      await vite.ssrLoadModule("/src/lib/stores/user.svelte.ts")
    );
  const review = {
    id: 1,
    review_decision: [],
    review_comment: "",
    environment: { id: 1, name: "amd64", architecture: "amd64" },
    artefact_build: { id: 1, architecture: "amd64", revision: null },
    reviewers: [],
  };
  const env = {
    review,
    runsDescending: [],
    name: "amd64",
    architecture: "amd64",
  };
  const store = {
    isSelected: () => true,
    selectAll: () => undefined,
    deselectAll: () => undefined,
  };
  const renderBulk = () =>
    renderComponent(bulkControls, {
      props: { environments: [env], artefactId: 1, store },
    }).body;
  const renderReview = () =>
    renderComponent(reviewButton, {
      props: { review, artefactId: 1, store },
    }).body;

  const user = {
    id: 5,
    email: "reviewer@example.com",
    name: "Reviewer",
    launchpad_handle: null,
    teams: [{ permissions: ["view_environment_review"] }],
    is_admin: false,
  };
  const permission = "change_environment_review";
  /** @param {boolean} allowed */
  const assertReviewAccess = (allowed) => {
    assert.equal(userStore.hasPermission(permission), allowed);
    if (allowed) {
      assert.match(renderBulk(), />Review 1 environment/);
      assert.match(renderReview(), /<button class="trigger/);
    } else {
      assert.doesNotMatch(renderBulk(), />Review 1 environment/);
      assert.doesNotMatch(renderReview(), /<button class="trigger/);
    }
  };
  try {
    userStore.current = user;
    assertReviewAccess(false);

    // Explicit team grants do not depend on the administrator bypass.
    userStore.current = {
      ...user,
      teams: [{ permissions: [permission] }],
    };
    assertReviewAccess(true);
    assert.equal(
      await userStore.refresh(() =>
        Promise.resolve(new Response("{}", { status: 503 })),
      ),
      "unknown",
    );
    assertReviewAccess(true);

    const admin = { ...user, teams: [], is_admin: true };
    const confirmAdmin = () =>
      userStore.refresh(() => Promise.resolve(jsonResponse(admin)));
    assert.equal(await confirmAdmin(), "authenticated");
    assertReviewAccess(true);
    assert.equal(
      await userStore.refresh(() =>
        Promise.resolve(new Response("{}", { status: 503 })),
      ),
      "unknown",
    );
    assert.equal(userStore.current.is_admin, true, "profile remains cached");
    assertReviewAccess(false);

    assert.equal(await confirmAdmin(), "authenticated");
    assertReviewAccess(true);
  } finally {
    await userStore.refresh(() =>
      Promise.resolve(new Response("{}", { status: 401 })),
    );
  }
});

void test("artefact mutation capabilities fail closed without a matching-rule signal", async () => {
  if (!render || !ArtefactSignoffButton || !TestPlanExpandable || !vite) {
    throw new Error("Permission-gated component modules were not loaded");
  }
  const renderComponent = render;
  const signoffButton = ArtefactSignoffButton;
  const testPlanExpandable = TestPlanExpandable;
  const { userStore } = await vite.ssrLoadModule(
    "/src/lib/stores/user.svelte.ts",
  );
  const store = ArtefactPageStore && new ArtefactPageStore();
  if (!store) throw new Error("Store module was not loaded");
  // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
  userStore.current = {
    id: 5,
    teams: [
      {
        permissions: ["change_artefact", "change_rerun", "change_rerun_bulk"],
      },
    ],
    is_admin: false,
  };
  assert.equal(store.canChangeArtefact, false);
  assert.equal(store.canChangeRerun, false);
  assert.equal(store.canChangeRerunBulk, false);

  // A logged-in view-only user is likewise not granted mutation affordances.
  // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
  userStore.current = { id: 6, teams: [], is_admin: false };
  assert.equal(store.canChangeArtefact, false);
  assert.equal(store.canChangeRerun, false);
  assert.equal(store.canChangeRerunBulk, false);

  // Admin status is present in /users/me and bypasses the backend's matching
  // rule checks, so administrators retain the existing actions.
  // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
  userStore.current = { id: 7, teams: [], is_admin: true };
  assert.equal(store.canChangeArtefact, false);
  assert.equal(
    // eslint-disable-next-line @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access
    await userStore.refresh(() =>
      Promise.resolve(jsonResponse({ id: 7, teams: [], is_admin: true })),
    ),
    "authenticated",
  );
  assert.equal(store.canChangeArtefact, true);
  assert.equal(store.canChangeRerun, true);
  assert.equal(store.canChangeRerunBulk, true);

  const artefact = { id: 1, status: "UNDECIDED" };
  const onstatuschange = () => undefined;
  const renderStatus = () =>
    renderComponent(signoffButton, {
      props: {
        artefact,
        canChangeStatus: store.canChangeArtefact,
        onstatuschange,
      },
    }).body;

  const run = {
    id: 5,
    status: "PASSED",
    test_plan: "plan",
    artefact_build_id: 1,
    environment: { id: 2, name: "env", architecture: "amd64" },
    is_rerun_requested: false,
    execution_metadata: {},
  };
  const renderPlan = () =>
    renderComponent(testPlanExpandable, {
      props: {
        planName: "plan",
        runs: [run],
        store: {
          canChangeRerun: store.canChangeRerun,
          rerunExecutions: () => Promise.resolve(),
          getTestEvents: () => undefined,
          getTestResults: () => undefined,
          fetchTestEvents: () => Promise.resolve(),
          fetchTestResults: () => Promise.resolve(),
        },
        isOnlyPlan: false,
        parentExpanded: false,
      },
    }).body;

  // Authenticated users with global write permissions still lack a signal for
  // the artefact-specific matching-rule grant.
  // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
  userStore.current = {
    id: 5,
    teams: [
      {
        permissions: ["change_artefact", "change_rerun", "change_rerun_bulk"],
      },
    ],
    is_admin: false,
  };
  assert.doesNotMatch(renderStatus(), /class="trigger(?:\s|")/);
  assert.doesNotMatch(renderPlan(), /class="rerun-btn(?:\s|")/);

  // Admins are the only existing /me signal that confirms bypass access.
  // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
  userStore.current = { id: 7, teams: [], is_admin: true };
  assert.match(renderStatus(), /class="trigger(?:\s|")/);
  assert.match(renderPlan(), /class="rerun-btn(?:\s|")/);

  // A retained admin profile is not authorization evidence after a failed
  // session refresh (for example, if /users/me cannot be reached).
  assert.equal(
    // eslint-disable-next-line @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access
    await userStore.refresh(() =>
      Promise.resolve(new Response("{}", { status: 503 })),
    ),
    "unknown",
  );
  // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
  assert.equal(userStore.current?.is_admin, true);
  assert.equal(store.canChangeArtefact, false);
  assert.equal(store.canChangeRerun, false);
  assert.equal(store.canChangeRerunBulk, false);
  assert.doesNotMatch(renderStatus(), /class="trigger(?:\s|")/);
  assert.doesNotMatch(renderPlan(), /class="rerun-btn(?:\s|")/);

  assert.equal(
    // eslint-disable-next-line @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access
    await userStore.refresh(() =>
      Promise.resolve(new Response("{}", { status: 401 })),
    ),
    "unauthenticated",
  );
  assert.equal(store.canChangeArtefact, false);
  assert.equal(store.canChangeRerun, false);
  assert.equal(store.canChangeRerunBulk, false);

  const routeSource = await readFile(
    new URL(
      "../src/routes/[family]/[artefactId]/+page.svelte",
      import.meta.url,
    ),
    "utf8",
  );
  assert.match(
    routeSource,
    /store\.canChangeRerun && store\.canChangeRerunBulk/,
  );
  assert.match(
    routeSource,
    /!store\.canChangeRerun \|\|\s*!store\.canChangeRerunBulk/,
  );
  // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
  userStore.current = null;
  // Reset the confirmation state too; these tests share the module singleton.
  // eslint-disable-next-line @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access
  await userStore.refresh(() =>
    Promise.resolve(new Response("{}", { status: 401 })),
  );
});

void test("version navigation resolves a base-independent artefact route", async () => {
  const source = await readFile(
    new URL(
      "../src/lib/components/artefact/ArtefactPageHeader.svelte",
      import.meta.url,
    ),
    "utf8",
  );

  assert.match(source, /goto\(resolve\(`\/\$\{family\.name\}\/\$\{id\}`\)\)/);
  assert.doesNotMatch(source, /resolve\(`\$\{base\}\/\$\{family\.name\}/);
});

void test("test issue links render only when the API supplies a URL", () => {
  if (!render || !TestResultExpandable) {
    throw new Error("Svelte component test modules were not loaded");
  }
  const renderComponent = render;
  const resultComponent = TestResultExpandable;
  const body = renderComponent(resultComponent, {
    props: {
      result: {
        id: 31,
        name: "network-check",
        status: "FAILED",
        template_id: "network-check-template",
        category: "network",
        comment: "",
        io_log: "",
        previous_results: [],
        issues: [
          {
            issue: {
              id: 1,
              source: "github",
              project: "org/project",
              key: "42",
              title: "Attached issue",
              status: "open",
              url: "https://example.com/attached",
            },
            attachment_rule: null,
          },
          {
            issue: {
              id: 2,
              source: "jira",
              project: "OPS",
              key: "43",
              title: "No URL issue",
              status: "unknown",
              url: "",
            },
            attachment_rule: null,
          },
        ],
      },
      store: {
        testIssues: [
          {
            id: 3,
            template_id: "network-check-template",
            case_name: "network-check",
            description: "Reported test issue",
            url: "https://example.com/reported",
          },
          {
            id: 4,
            template_id: "other-template",
            case_name: "other-test",
            description: "Reported test issue without a URL",
            url: "",
          },
        ],
      },
    },
  }).body;

  assert.match(body, /href="https:\/\/example\.com\/attached"/);
  assert.match(body, /href="https:\/\/example\.com\/reported"/);
  assert.doesNotMatch(body, /href=""/);
});

void test("lazy result and event failures stay local and can be retried", async () => {
  if (!vite) throw new Error("Vite server was not started");
  const { errorStore } =
    /** @type {{ errorStore: { clear: () => void, hasError: boolean } }} */ (
      await vite.ssrLoadModule("/src/lib/stores/error.svelte.ts")
    );
  errorStore.clear();
  const restoreFetch = installFetch({
    results: [
      Promise.reject(new Error("temporary results failure")),
      jsonResponse([{ id: 5 }]),
    ],
    events: [
      Promise.reject(new Error("temporary events failure")),
      jsonResponse([{ id: 6 }]),
    ],
  });

  try {
    const store = await initializeStore();

    await store.fetchTestResults(10);
    assert.equal(store.getTestResults(10), undefined);
    assert.equal(errorStore.hasError, false);

    await store.fetchTestResults(10);
    assert.deepEqual(store.getTestResults(10), [{ id: 5 }]);

    await store.fetchTestEvents(10);
    assert.equal(store.getTestEvents(10), "error");
    assert.equal(errorStore.hasError, false);

    await store.fetchTestEvents(10);
    assert.deepEqual(store.getTestEvents(10), [{ id: 6 }]);
  } finally {
    restoreFetch();
    errorStore.clear();
  }
});

void test("old failures cannot clear newer results or events loading markers", async () => {
  const oldResults = deferred();
  const newResults = deferred();
  const oldEvents = deferred();
  const newEvents = deferred();
  const restoreFetch = installFetch({
    results: [oldResults.promise, newResults.promise],
    events: [oldEvents.promise, newEvents.promise],
  });

  try {
    const store = await initializeStore();
    const oldRequest = store.fetchTestResults(10);
    const oldEventsRequest = store.fetchTestEvents(10);

    await store.init(2);
    const newRequest = store.fetchTestResults(10);
    const newEventsRequest = store.fetchTestEvents(10);
    assert.equal(store.getTestResults(10), "loading");
    assert.equal(store.getTestEvents(10), "loading");

    oldResults.reject(new Error("stale request failed"));
    oldEvents.reject(new Error("stale events request failed"));
    await Promise.all([oldRequest, oldEventsRequest]);
    assert.equal(store.getTestResults(10), "loading");
    assert.equal(store.getTestEvents(10), "loading");

    newResults.resolve(jsonResponse([{ id: 3 }]));
    newEvents.resolve(jsonResponse([{ id: 4 }]));
    await Promise.all([newRequest, newEventsRequest]);
    assert.deepEqual(store.getTestResults(10), [{ id: 3 }]);
    assert.deepEqual(store.getTestEvents(10), [{ id: 4 }]);
  } finally {
    restoreFetch();
  }
});

void test("rows group by build/environment review and shared environment selection updates each review", async () => {
  if (!ArtefactPageStore) throw new Error("Store module was not loaded");
  const environment = {
    id: 10,
    name: "shared environment",
    architecture: "amd64",
  };
  const reviews = [101, 102].map((id, index) => ({
    id,
    environment,
    artefact_build: {
      id: index + 1,
      architecture: "amd64",
      revision: index + 1,
    },
    review_decision: [],
    review_comment: "",
    reviewers: [],
  }));
  const builds = reviews.map((review, index) => ({
    ...review.artefact_build,
    bundled_in: [],
    test_executions: [index * 10 + 1, index * 10 + 2].map((id) => ({
      id,
      environment,
      status: "PASSED",
      test_plan: "plan",
    })),
  }));
  const originalFetch = globalThis.fetch;
  /** @type {{ id: number }[]} */
  const submittedReviews = [];
  globalThis.fetch = (url, options = {}) => {
    const requestUrl =
      url instanceof Request ? url.url : url instanceof URL ? url : url;
    const path = new URL(requestUrl).pathname;
    if (path.endsWith("/environment-reviews")) {
      if (options.method === "PATCH") {
        if (typeof options.body === "string") {
          // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
          const submitted = JSON.parse(options.body);
          // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
          submittedReviews.push(.../** @type {{ id: number }[]} */ (submitted));
        }
        return Promise.resolve(
          jsonResponse(
            reviews.map((review) => ({
              ...review,
              review_decision: ["APPROVED_ALL_TESTS_PASS"],
              review_comment: "Reviewed",
            })),
          ),
        );
      }
      return Promise.resolve(jsonResponse(reviews));
    }
    if (path.endsWith("/builds")) return Promise.resolve(jsonResponse(builds));
    if (path.endsWith("/artefacts/1"))
      return Promise.resolve(jsonResponse({ id: 1 }));
    return Promise.resolve(jsonResponse([]));
  };

  try {
    const store = await initializeStore();
    assert.equal(store.allEnvironments.length, 2);
    const reviewedRows = store.allEnvironments.filter(
      (row) => row.review !== null,
    );
    /** @param {import("../src/lib/types/artefact-page").ArtefactEnvironment} row */
    const reviewFor = (row) => {
      if (!row.review) throw new Error("Expected an environment review");
      return row.review;
    };
    assert.deepEqual(
      reviewedRows.map((row) => ({
        reviewId: reviewFor(row).id,
        runs: row.runsDescending.map((run) => run.id),
      })),
      [
        { reviewId: 101, runs: [2, 1] },
        { reviewId: 102, runs: [12, 11] },
      ],
    );

    store.selectAll(reviewedRows.map((row) => reviewFor(row).id));
    assert.equal(store.selectedEnvironmentIds.size, 2);
    const selectedRows = reviewedRows.filter((row) =>
      store.isSelected(reviewFor(row).id),
    );
    assert.equal(selectedRows.length, 2);
    await store.bulkUpdateEnvironmentReviews(
      1,
      selectedRows.map((row) => ({
        id: reviewFor(row).id,
        review_decision: ["APPROVED_ALL_TESTS_PASS"],
        review_comment: "Reviewed",
      })),
    );
    assert.deepEqual(
      submittedReviews.map((review) => review.id),
      [101, 102],
    );
    assert.ok(
      store.allEnvironments
        .filter((row) => row.review !== null)
        .every((row) =>
          reviewFor(row).review_decision.includes("APPROVED_ALL_TESTS_PASS"),
        ),
    );
    assert.equal(store.artefact?.completed_environment_reviews_count, 2);

    store.selectAll([101]);
    const filteredRows = reviewedRows.filter((row) =>
      store.isSelected(reviewFor(row).id),
    );
    assert.deepEqual(
      filteredRows.map((row) => reviewFor(row).id),
      [101],
    );
    assert.equal(filteredRows.length, 1);
    store.toggleSelection(101);
    assert.equal(store.selectedEnvironmentIds.size, 0);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
