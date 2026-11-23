// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { before, test } from "node:test";
import ts from "typescript";

/** @type {typeof import("../src/lib/families") | undefined} */
let families;

before(async () => {
  const source = await readFile(
    new URL("../src/lib/families.ts", import.meta.url),
    "utf8",
  );
  const { outputText } = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.ESNext },
  });
  const moduleValue = /** @type {unknown} */ (
    await import(
      `data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`
    )
  );
  families = /** @type {typeof import("../src/lib/families")} */ (moduleValue);
});

void test("family routes use exact names and avoid static route collisions", () => {
  if (!families) throw new Error("Family route helpers were not loaded");
  const knownFamilies = [
    { name: "snap" },
    { name: "news" },
    { name: "issue" },
    { name: "test-result" },
    { name: "issues" },
    { name: "test-results" },
  ];

  assert.equal(families.findFamilyByName(knownFamilies, "news")?.name, "news");
  assert.equal(families.findFamilyByName(knownFamilies, "new"), undefined);
  assert.equal(families.familyDashboardRoute({ name: "news" }), "family/news");
  assert.equal(
    families.familyDetailRoute({ name: "news" }, 42),
    "family/news/42",
  );
  assert.equal(
    families.familyDashboardRoute({ name: "issues" }),
    "family/issues",
  );
  assert.equal(
    families.familyDashboardRoute({ name: "test-results" }),
    "family/test-results",
  );
  assert.equal(
    families.familyDashboardRoute({ name: "issue" }),
    "family/issue",
  );
  assert.equal(
    families.familyDashboardRoute({ name: "test-result" }),
    "family/test-result",
  );

  // These names remain unchanged for existing navigation labels and saved views.
  assert.equal(families.familyRouteName({ name: "snap" }), "snaps");
  assert.equal(families.familyNavLabel({ name: "snap" }), "Snaps");
  assert.equal(
    families.findFamilyByLegacyRouteName(knownFamilies, "snaps")?.name,
    "snap",
  );
});

void test("legacy redirects preserve query strings, detail ids, and the base path", () => {
  if (!families) throw new Error("Family route helpers were not loaded");
  /** @param {string} path */
  const addBasePath = (path) => `/wip/${path}`;
  const query = "?view=a%2Bb&filter=x%20y";

  assert.equal(
    families.familyRedirectTarget({ name: "snap" }, null, query, addBasePath),
    `/wip/family/snap${query}`,
  );
  assert.equal(
    families.familyRedirectTarget({ name: "snap" }, 42, query, addBasePath),
    `/wip/family/snap/42${query}`,
  );
  assert.equal(
    families.familyRedirectTarget(
      { name: "test-results" },
      null,
      "",
      addBasePath,
    ),
    "/wip/family/test-results",
  );
});
