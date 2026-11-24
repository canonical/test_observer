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
/** @type {typeof import("../src/lib/api/changelog").fetchChangelogEntry} */
let fetchChangelogEntry;
/** @type {typeof import("../src/lib/utils/changelog").changelogPath} */
let changelogPath;
/** @type {typeof import("../src/lib/utils/changelog").snapshotValue} */
let snapshotValue;
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
  ({ pageOffset, pageHref, operationLabel, changelogPath, snapshotValue } =
    await vite.ssrLoadModule("/src/lib/utils/changelog.ts"));
  ({ fetchChangelog, fetchChangelogEntry } = await vite.ssrLoadModule(
    "/src/lib/api/changelog.ts",
  ));
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
  const props = {
    history,
    url,
    detailBase: "/wip/items/3/changelog",
    artefactId: 3,
  };
  const html = render(Table, { props }).body;
  assert.match(html, /Updated/);
  assert.match(html, /Alice \(user\)/);
  assert.match(html, /href="\/base\/changelog"/);
  assert.match(html, /href="\/wip\/items\/3\/changelog\/1"/);
  assert.match(html, /<button[^>]*>JSON<\/button>/);
  const review = render(Table, {
    props: {
      ...props,
      detailBase: "/wip/items/3/environments/8/changelog",
      reviewId: 8,
    },
  }).body;
  assert.match(review, /href="\/wip\/items\/3\/environments\/8\/changelog\/1"/);
  assert.match(review, /<button[^>]*>JSON<\/button>/);
  assert.doesNotMatch(html, />Next</);
  const empty = render(Table, {
    props: { ...props, history: { ...history, count: 0, entries: [] } },
  }).body;
  assert.match(empty, /No changelog entries found/);
  const pastEnd = render(Table, {
    props: { ...props, history: { ...history, entries: [] } },
  }).body;
  assert.match(pastEnd, /No entries on this page/);
  assert.match(pastEnd, />Previous</);
});

void test("detail fetch checks membership and selects the audit endpoint", async () => {
  /** @type {string[]} */
  const paths = [];
  let reviewExists = false;
  let missing = false;
  const detail = { id: 12, data: {} };
  /** @param {string} path */
  const mockRequest = (path) => {
    paths.push(path);
    if (path === "/artefacts/3") return Promise.resolve({ family: "generic" });
    if (path.endsWith("/environment-reviews"))
      return Promise.resolve(reviewExists ? [{ id: 8 }] : []);
    return Promise.resolve(missing ? null : detail);
  };
  const request =
    /** @type {typeof import("../src/lib/api/client").silentApi} */ (
      /** @type {unknown} */ (mockRequest)
    );
  assert.equal(await fetchChangelogEntry(3, "other", 8, 12, request), null);
  assert.deepEqual(paths.splice(0), ["/artefacts/3"]);
  assert.equal(await fetchChangelogEntry(3, "generic", 8, 12, request), null);
  assert.deepEqual(paths.splice(0), [
    "/artefacts/3",
    "/artefacts/3/environment-reviews",
  ]);
  reviewExists = true;
  assert.deepEqual(
    await fetchChangelogEntry(3, "generic", 8, 12, request),
    detail,
  );
  assert.deepEqual(paths.splice(0), [
    "/artefacts/3",
    "/artefacts/3/environment-reviews",
    "/audit/environment-reviews/8/12",
  ]);
  assert.deepEqual(
    await fetchChangelogEntry(3, "generic", undefined, 12, request),
    detail,
  );
  assert.deepEqual(paths.splice(0), ["/artefacts/3", "/audit/artefacts/3/12"]);
  missing = true;
  await assert.rejects(
    fetchChangelogEntry(3, "generic", undefined, 12, request),
    /Missing audit response/,
  );
});

void test("snapshot formatting and changelog paths preserve values", () => {
  assert.deepEqual(
    [null, false, 0, "", "text", [1, null], { a: true }].map(snapshotValue),
    ["null", "false", "0", "", "text", "[1,null]", '{"a":true}'],
  );
  assert.equal(changelogPath("items", 3, undefined), "items/3/changelog");
  assert.equal(
    changelogPath("items", 3, 8),
    "items/3/environments/8/changelog",
  );
});

void test("detail routes reject invalid identifiers and unknown families", async () => {
  for (const [path, review] of [
    ["/src/routes/[family]/[artefactId]/changelog/[auditId]/+page.ts", false],
    [
      "/src/routes/[family]/[artefactId]/environments/[reviewId]/changelog/[auditId]/+page.ts",
      true,
    ],
  ]) {
    const { load } =
      /** @type {{load: (input: {parent: () => Promise<{artefactFamilies: {name: string, api_name: string}[]}>, params: {family: string, artefactId: string, reviewId: string, auditId: string}}) => Promise<{auditId: number, reviewId?: number}>}} */ (
        await vite.ssrLoadModule(/** @type {string} */ (path))
      );
    const parent = async () => {
      await Promise.resolve();
      return { artefactFamilies: [{ name: "items", api_name: "generic" }] };
    };
    const params = {
      family: "items",
      artefactId: "3",
      reviewId: "8",
      auditId: "12",
    };
    const result = await load({ parent, params });
    assert.equal(result.auditId, 12);
    if (review) assert.equal(result.reviewId, 8);
    for (const [key, value] of [
      ["family", "other"],
      ["artefactId", "0"],
      ["auditId", "1.5"],
      ["auditId", "9007199254740992"],
      ...(review ? [["reviewId", "-1"]] : []),
    ]) {
      await assert.rejects(
        load({ parent, params: { ...params, [key]: value } }),
        (error) => {
          assert.ok(error && typeof error === "object" && "status" in error);
          assert.equal(error.status, 404);
          return true;
        },
      );
    }
  }
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
