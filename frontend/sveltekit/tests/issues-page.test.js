// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-return */

import assert from "node:assert/strict";
import { before, test } from "node:test";
import { resolve } from "node:path";
import { build } from "vite";

/** @type {typeof import('../src/lib/issuePageModel')} */
let model;

before(async () => {
  const built = /** @type {{output: {type: string; code: string}[]}[]} */ (
    /** @type {unknown} */ (
      await build({
        configFile: false,
        logLevel: "silent",
        resolve: { alias: { $lib: resolve("src/lib") } },
        build: {
          write: false,
          lib: {
            entry: "src/lib/issuePageModel.ts",
            formats: ["es"],
          },
          rolldownOptions: { output: { codeSplitting: false } },
        },
      })
    )
  );
  const bundle = built[0].output.find((item) => item.type === "chunk");
  assert.ok(bundle);
  model = await import(
    `data:text/javascript;base64,${Buffer.from(bundle.code).toString("base64")}`
  );
});

const issue = (id, source, project) => ({
  id,
  source,
  project,
  key: String(id),
  title: `Issue ${id}`,
  status: "open",
  url: `https://example.invalid/${id}`,
});

void test("issue filters restore defaults and parse repeated query-backed values", () => {
  const defaults = model.parseIssueFilters(new URLSearchParams(), [
    "snap",
    "deb",
  ]);
  assert.deepEqual(defaults.statuses, ["open", "unknown"]);
  assert.deepEqual(defaults.sources, []);
  assert.deepEqual(defaults.projects, []);

  const params = new URLSearchParams();
  params.append("source", "github");
  params.append("source", "jira");
  params.append("status", "closed,open");
  params.append("family", "snap");
  params.append("family", "unknown-family");
  params.append("project", "team/repo");
  params.append("q", "  auth failure  ");
  assert.deepEqual(model.parseIssueFilters(params, ["snap", "deb"]), {
    sources: ["github", "jira"],
    statuses: ["closed", "open"],
    families: ["snap"],
    projects: ["team/repo"],
    query: "auth failure",
  });

  const allStatuses = model.parseIssueFilters(new URLSearchParams("status="), [
    "snap",
  ]);
  assert.deepEqual(allStatuses.statuses, []);
});

void test("API requests use fifty-row pages, repeated status/family filters, and query search", () => {
  const filters = {
    sources: ["github", "jira"],
    statuses: ["open", "unknown"],
    families: ["snap", "deb"],
    projects: ["team/repo", "other/repo"],
    query: "auth failure",
  };
  const params = model.issueApiParams(filters, 100);
  assert.equal(params.get("limit"), "50");
  assert.equal(params.get("offset"), "100");
  assert.deepEqual(params.getAll("status"), ["open", "unknown"]);
  assert.deepEqual(params.getAll("families"), ["snap", "deb"]);
  assert.equal(params.get("q"), "auth failure");
  assert.equal(params.has("source"), false);
  assert.equal(params.has("project"), false);
  const singleSelection = model.issueApiParams(
    { ...filters, sources: ["github"], projects: ["team/repo"] },
    0,
  );
  assert.equal(singleSelection.get("source"), "github");
  assert.equal(singleSelection.get("project"), "team/repo");
  assert.equal(model.ISSUE_PAGE_SIZE, 50);
});

void test("source and project selections filter locally while unselected dimensions remain broad", () => {
  const rows = [
    issue(1, "github", "team/repo"),
    issue(2, "jira", "OPS"),
    issue(3, "github", "other/repo"),
  ];
  const filters = {
    sources: ["github"],
    statuses: ["open"],
    families: [],
    projects: ["other/repo"],
    query: "",
  };
  assert.deepEqual(
    model
      .filterIssueRows(rows, {
        ...filters,
        sources: [],
        projects: ["OPS", "other/repo"],
      })
      .map((row) => row.id),
    [2, 3],
  );
  assert.deepEqual(
    model.filterIssueRows(rows, filters).map((row) => row.id),
    [3],
  );
  assert.deepEqual(
    model
      .filterIssueRows(rows, { ...filters, sources: [], projects: [] })
      .map((row) => row.id),
    [1, 2, 3],
  );
});

void test("active groups compare applied status sets to defaults, including unrestricted status", () => {
  const defaults = model.parseIssueFilters(new URLSearchParams(), ["snap"]);
  assert.equal(model.issueActiveGroupCount(defaults), 0);
  assert.equal(
    model.issueActiveGroupCount({ ...defaults, statuses: ["unknown", "open"] }),
    0,
  );
  assert.equal(model.issueActiveGroupCount({ ...defaults, statuses: [] }), 1);
  assert.equal(
    model.issueActiveGroupCount({
      ...defaults,
      statuses: ["open", "closed", "unknown"],
    }),
    1,
  );
  assert.equal(
    model.issueActiveGroupCount({
      sources: ["jira", "github"],
      statuses: ["closed"],
      families: ["snap"],
      projects: ["A", "B"],
      query: "needle",
    }),
    5,
  );
});

void test("project discovery removes only the project constraint and has independent identity", () => {
  const filters = model.parseIssueFilters(
    new URLSearchParams(
      "source=jira&source=github&family=snap&status=closed&q=needle&project=A",
    ),
    ["snap"],
  );
  const discovery = model.issueProjectFilters(filters);
  assert.deepEqual(discovery, { ...filters, projects: [] });
  assert.equal(filters.projects[0], "A");
  assert.equal(
    model.issueFilterKey(discovery),
    model.issueFilterKey(
      model.issueProjectFilters({ ...filters, projects: ["B", "C"] }),
    ),
  );
  const params = model.issueApiParams(discovery, 50);
  assert.equal(params.has("project"), false);
  assert.equal(params.has("source"), false);
  assert.deepEqual(params.getAll("status"), ["closed"]);
  assert.deepEqual(params.getAll("families"), ["snap"]);
  assert.equal(params.get("q"), "needle");
});

void test("pagination accumulation deduplicates overlap and duplicates within an incoming page", () => {
  const existing = [issue(1, "github", "team/repo")];
  const appended = model.appendUniqueIssues(existing, [
    issue(1, "github", "team/repo"),
    issue(2, "jira", "OPS"),
    issue(2, "jira", "OPS"),
    issue(3, "github", "other/repo"),
  ]);
  assert.deepEqual(
    appended.map((row) => row.id),
    [1, 2, 3],
  );
  assert.deepEqual(
    existing.map((row) => row.id),
    [1],
  );
});

void test("filter keys ignore selection order but track every meaningful query value", () => {
  const first = {
    sources: ["jira", "github"],
    statuses: ["open", "closed"],
    families: ["deb", "snap"],
    projects: ["z", "a"],
    query: "needle",
  };
  const reordered = {
    sources: ["github", "jira"],
    statuses: ["closed", "open"],
    families: ["snap", "deb"],
    projects: ["a", "z"],
    query: "needle",
  };
  assert.equal(model.issueFilterKey(first), model.issueFilterKey(reordered));
  assert.notEqual(
    model.issueFilterKey(first),
    model.issueFilterKey({ ...first, query: "different" }),
  );
});

void test("external issue URLs must match supported secure tracker issue forms", () => {
  for (const url of [
    "https://github.com/canonical/test-observer/issues/42",
    "https://warthogs.atlassian.net/browse/OPS-27",
    "https://warthogs.atlassian.net/browse/ops-27",
    "https://bugs.launchpad.net/ubuntu/+source/linux/+bug/123",
    "https://bugs.launchpad.net/test-observer/+bug/123",
  ]) {
    assert.equal(model.externalIssueUrlError(url), null, url);
  }
  for (const url of [
    "",
    "not a URL",
    "http://github.com/canonical/test-observer/issues/42",
    "https://github.com.evil.test/owner/repo/issues/42",
    "https://github.com/canonical/test-observer/pulls/42",
    "https://example.test/browse/OPS-27",
    "https://bugs.launchpad.net/ubuntu/+bug/not-a-number",
    "https://user:pass@github.com/canonical/test-observer/issues/42",
    "https://github.com:444/canonical/test-observer/issues/42",
  ]) {
    assert.ok(model.externalIssueUrlError(url), url);
  }
});
