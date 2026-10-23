// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

/* eslint-disable @typescript-eslint/no-floating-promises -- node:test registers tests synchronously */

import assert from "node:assert/strict";
import { after, test } from "node:test";
import { createServer } from "vite";

const server = await createServer({
  server: { middlewareMode: true },
  appType: "custom",
  logLevel: "error",
});
/** @type {typeof import("../src/lib/tableView")} */
const tableView = /** @type {never} */ (
  await server.ssrLoadModule("/src/lib/tableView.ts")
);
/** @type {typeof import("../src/lib/tableViewUrl")} */
const tableViewUrl = /** @type {never} */ (
  await server.ssrLoadModule("/src/lib/tableViewUrl.ts")
);
const { filterArtefacts, nextSorting, pageCount, paginate, sortArtefacts } =
  tableView;
const { decodeView, encodeView } = tableViewUrl;

const columns = [
  { key: "name", label: "Name", field: "name" },
  { key: "version", label: "Version", field: "version" },
  { key: "left", label: "Left", format: "reviewsRemaining" },
];
const artefacts = [
  {
    id: 1,
    name: "beta",
    version: "10",
    all_environment_reviews_count: 3,
    completed_environment_reviews_count: 1,
  },
  {
    id: 2,
    name: "Alpha",
    version: "9",
    all_environment_reviews_count: 1,
    completed_environment_reviews_count: 1,
  },
  {
    id: 3,
    name: "gamma",
    version: "",
    all_environment_reviews_count: 5,
    completed_environment_reviews_count: 0,
  },
];
/** @param {{ id: number }[]} rows */
const ids = (rows) => rows.map((a) => a.id);

test("sorts text case-insensitively and numbers naturally", () => {
  assert.deepEqual(
    ids(sortArtefacts(artefacts, columns, { id: "name", desc: false })),
    [2, 1, 3],
  );
  assert.deepEqual(
    ids(sortArtefacts(artefacts, columns, { id: "left", desc: true })),
    [3, 1, 2],
  );
});

test("empty values sort last in both directions", () => {
  for (const desc of [false, true]) {
    const sorted = sortArtefacts(artefacts, columns, { id: "version", desc });
    assert.equal(sorted.at(-1).id, 3);
  }
});

test("sorting cycles ascending, descending, off", () => {
  const first = nextSorting(null, "name");
  assert.deepEqual(first, { id: "name", desc: false });
  const second = nextSorting(first, "name");
  assert.deepEqual(second, { id: "name", desc: true });
  assert.equal(nextSorting(second, "name"), null);
  assert.deepEqual(nextSorting(second, "version"), {
    id: "version",
    desc: false,
  });
});

test("global search only looks at visible columns", () => {
  const all = new Set(["name", "version", "left"]);
  const view = { globalFilter: "9", columnFilters: {} };
  assert.deepEqual(ids(filterArtefacts(artefacts, columns, all, view)), [2]);
  const noVersion = new Set(["name", "left"]);
  assert.deepEqual(
    ids(filterArtefacts(artefacts, columns, noVersion, view)),
    [],
  );
});

test("column filters combine and ignore blanks", () => {
  const all = new Set(["name", "version", "left"]);
  const view = {
    globalFilter: "",
    columnFilters: { name: "A", version: "  ", constructor: "" },
  };
  assert.deepEqual(
    ids(filterArtefacts(artefacts, columns, all, view)),
    [1, 2, 3],
  );
  view.columnFilters.version = "9";
  assert.deepEqual(ids(filterArtefacts(artefacts, columns, all, view)), [2]);
});

test("view encoding round-trips and drops default state", () => {
  assert.equal(
    encodeView({
      sorting: null,
      globalFilter: "  ",
      columnFilters: { name: "" },
    }),
    null,
  );
  const view = {
    sorting: { id: "name", desc: true },
    globalFilter: "é",
    columnFilters: { name: "x" },
    hiddenColumns: ["version"],
  };
  assert.deepEqual(decodeView(encodeView(view)), view);
});

test("malformed views are rejected", () => {
  assert.equal(decodeView("not base64 !!"), null);
  const bad = encodeView({ globalFilter: "x" });
  assert.deepEqual(decodeView(bad), { globalFilter: "x" });
  assert.equal(decodeView("a".repeat(9000)), null);
  const wrongShape = btoa(JSON.stringify({ columnFilters: { a: 1 } }));
  assert.equal(decodeView(wrongShape), null);
});

test("paginate slices and clamps the page", () => {
  const items = [1, 2, 3, 4, 5];
  assert.deepEqual(paginate(items, 1, 2), { rows: [3, 4], page: 1 });
  assert.deepEqual(paginate(items, 9, 2), { rows: [5], page: 2 });
  assert.deepEqual(paginate(items, -1, 2), { rows: [1, 2], page: 0 });
  assert.deepEqual(paginate([], 3, 2), { rows: [], page: 0 });
  assert.equal(pageCount(0, 25), 1);
  assert.equal(pageCount(26, 25), 2);
});

after(() => server.close());
