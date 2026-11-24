// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0
import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { createServer } from "vite";

/** @type {import("vite").ViteDevServer} */
let vite;
/** @type {typeof import("../src/lib/utils/changelog").pageOffset} */
let pageOffset;
/** @type {typeof import("../src/lib/utils/changelog").pageHref} */
let pageHref;
/** @type {typeof import("../src/lib/utils/changelog").operationLabel} */
let operationLabel;
/** @type {typeof import("../src/lib/api/changelog").fetchChangelog} */
let fetchChangelog;
/** @type {typeof import("svelte/server").render} */
let render;
/** @type {typeof import("../src/lib/components/changelog/ChangelogTable.svelte").default} */
let Table;

before(async () => {
  vite = await createServer({
    configFile: "vite.config.ts",
    appType: "custom",
    logLevel: "silent",
    server: { middlewareMode: true },
  });
  ({ pageOffset, pageHref, operationLabel } = await vite.ssrLoadModule(
    "/src/lib/utils/changelog.ts",
  ));
  ({ fetchChangelog } = await vite.ssrLoadModule("/src/lib/api/changelog.ts"));
  ({ render } = await vite.ssrLoadModule("svelte/server"));
  ({ default: Table } = await vite.ssrLoadModule(
    "/src/lib/components/changelog/ChangelogTable.svelte",
  ));
});

after(async () => {
  await vite.close();
});

void test("pagination validates URL pages and preserves base paths and other parameters", () => {
  for (const value of [null, "", "0", "-1", "1.5", "999999999999999999999"])
    assert.equal(pageOffset(value), 0);
  assert.equal(pageOffset("2"), 50);
  assert.equal(
    pageHref("https://example.test/base/family/3/changelog?foo=bar&page=2", 1),
    "/base/family/3/changelog?foo=bar",
  );
  assert.equal(
    pageHref("https://example.test/base/family/3/changelog?foo=bar", 2),
    "/base/family/3/changelog?foo=bar&page=2",
  );
  assert.deepEqual(["I", "U", "D"].map(operationLabel), [
    "Created",
    "Updated",
    "Deleted",
  ]);
});

void test("table renders entries, empty pages and pagination", () => {
  const url = "https://example.test/base/changelog?page=2";
  /** @type {import("../src/lib/types/openapi").AuditHistoryResponse} */
  const history = {
    count: 51,
    limit: 50,
    offset: 50,
    entries: [
      {
        id: 1,
        created_at: "2026-01-01T00:00:00Z",
        operation: "U",
        author: {
          name: "Alice",
          kind: "user",
          user_id: 1,
          application_id: null,
          automation_name: null,
        },
      },
    ],
  };
  const html = render(Table, { props: { history, url } }).body;
  assert.match(html, /Updated/);
  assert.match(html, /Alice \(user\)/);
  assert.match(html, /href="\/base\/changelog"/);
  assert.doesNotMatch(html, />Next</);
  const empty = render(Table, {
    props: { history: { ...history, count: 0, entries: [] }, url },
  }).body;
  assert.match(empty, /No changelog entries found/);
  const pastEnd = render(Table, {
    props: { history: { ...history, entries: [] }, url },
  }).body;
  assert.match(pastEnd, /No entries on this page/);
  assert.match(pastEnd, />Previous</);
});

void test("review history is requested only after checking its artefact and family", async () => {
  /** @type {string[]} */
  const paths = [];
  let reviews = [{ id: 8 }];
  /** @param {string} path */
  const mockRequest = (path) => {
    paths.push(path);
    if (path === "/artefacts/3") return Promise.resolve({ family: "generic" });
    if (path.endsWith("/environment-reviews")) return Promise.resolve(reviews);
    return Promise.resolve({ entries: [], count: 0, limit: 50, offset: 50 });
  };
  const request =
    /** @type {typeof import("../src/lib/api/client").silentApi} */ (
      /** @type {unknown} */ (mockRequest)
    );
  assert.equal(await fetchChangelog(3, "other", 8, 0, request), null);
  assert.deepEqual(paths.splice(0), ["/artefacts/3"]);
  reviews = [{ id: 9 }];
  assert.equal(await fetchChangelog(3, "generic", 8, 0, request), null);
  assert.deepEqual(paths.splice(0), [
    "/artefacts/3",
    "/artefacts/3/environment-reviews",
  ]);
  reviews = [{ id: 8 }];
  await fetchChangelog(3, "generic", 8, 50, request);
  assert.deepEqual(paths.splice(0), [
    "/artefacts/3",
    "/artefacts/3/environment-reviews",
    "/audit/environment-reviews/8?limit=50&offset=50",
  ]);
  await fetchChangelog(3, "generic", undefined, 0, request);
  assert.deepEqual(paths, [
    "/artefacts/3",
    "/audit/artefacts/3?limit=50&offset=0",
  ]);
});
