// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { createServer } from "vite";

/** @type {import("vite").ViteDevServer | undefined} */
let vite;
/** @type {typeof import("../src/lib/stores/artefact-page.svelte").ArtefactPageStore | undefined} */
let ArtefactPageStore;

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
});

after(async () => {
  await vite?.close();
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
    if (path.endsWith("/reported-issues") && reportedIssuesStatus) {
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
