// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

/* eslint-disable @typescript-eslint/no-unsafe-assignment */
import assert from "node:assert/strict";
import { before, test } from "node:test";
import { resolve } from "node:path";
import { build } from "vite";

/** @type {typeof import('../src/lib/issueDetailModel')} */
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
            entry: "src/lib/issueDetailModel.ts",
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

const rule = {
  id: 14,
  enabled: true,
  families: ["snap", "deb"],
  artefacts: ["example-app"],
  artefact_versions: ["1.2"],
  artefact_stages: ["", "edge"],
  artefact_tracks: ["latest/stable"],
  environment_names: ["ubuntu-24.04"],
  test_plans: ["smoke"],
  test_case_names: ["install / test"],
  template_ids: ["template-1"],
  test_result_statuses: ["FAILED", "SKIPPED"],
  execution_metadata: { "ci:provider": ["GitHub Actions", "Buildkite"] },
};

void test("attachment-rule targets accept only one strict positive safe integer", () => {
  for (const value of ["1", "14", String(Number.MAX_SAFE_INTEGER)])
    assert.equal(
      model.attachmentRuleTarget(
        new URLSearchParams({ attachmentRule: value }),
      ),
      Number(value),
    );
  for (const value of [
    "",
    "0",
    "-1",
    "01",
    "+14",
    " 14",
    "14 ",
    "1.5",
    "1e2",
    "14,15",
    "NaN",
    "Infinity",
    "9007199254740992",
    "１４",
  ])
    assert.equal(
      model.attachmentRuleTarget(
        new URLSearchParams({ attachmentRule: value }),
      ),
      null,
      value,
    );
  for (const query of [
    "",
    "other=14",
    "attachmentRule=14&attachmentRule=15",
    "attachmentRule=14&attachmentRule=14",
    "attachmentRule=14&attachmentRule=",
  ])
    assert.equal(model.attachmentRuleTarget(new URLSearchParams(query)), null);
});

void test("rule criteria shows every supported attachment filter", () => {
  assert.deepEqual(model.attachmentRuleCriteria(rule), [
    { label: "Family", values: ["snap", "deb"] },
    { label: "Artefact", values: ["example-app"] },
    { label: "Artefact Versions", values: ["1.2"] },
    { label: "Artefact Stages", values: ["", "edge"] },
    { label: "Artefact Tracks", values: ["latest/stable"] },
    { label: "Environments", values: ["ubuntu-24.04"] },
    { label: "Test Plans", values: ["smoke"] },
    { label: "Test Cases", values: ["install / test"] },
    { label: "Template IDs", values: ["template-1"] },
    { label: "Test Result Statuses", values: ["FAILED", "SKIPPED"] },
    {
      label: "Execution Metadata",
      values: [
        '"ci:provider" = "GitHub Actions"',
        '"ci:provider" = "Buildkite"',
      ],
    },
  ]);
  assert.deepEqual(
    model.attachmentRuleCriteria({
      ...rule,
      families: [],
      execution_metadata: {},
    }),
    [
      { label: "Artefact", values: ["example-app"] },
      { label: "Artefact Versions", values: ["1.2"] },
      { label: "Artefact Stages", values: ["", "edge"] },
      { label: "Artefact Tracks", values: ["latest/stable"] },
      { label: "Environments", values: ["ubuntu-24.04"] },
      { label: "Test Plans", values: ["smoke"] },
      { label: "Test Cases", values: ["install / test"] },
      { label: "Template IDs", values: ["template-1"] },
      { label: "Test Result Statuses", values: ["FAILED", "SKIPPED"] },
    ],
  );
});

void test("view-filters navigation preserves the configured base and every filter", () => {
  const href = model.viewRuleFiltersUrl("/wip/", 73, rule);
  const url = new URL(href, "https://test-observer.invalid");
  assert.equal(url.pathname, "/wip/test-results");
  assert.equal(url.searchParams.get("issues"), "73");
  assert.deepEqual(url.searchParams.getAll("families"), ["snap", "deb"]);
  assert.deepEqual(url.searchParams.getAll("artefacts"), ["example-app"]);
  assert.deepEqual(url.searchParams.getAll("artefact_versions"), ["1.2"]);
  assert.deepEqual(url.searchParams.getAll("artefact_stages"), ["", "edge"]);
  assert.deepEqual(url.searchParams.getAll("artefact_tracks"), [
    "latest/stable",
  ]);
  assert.deepEqual(url.searchParams.getAll("environments"), ["ubuntu-24.04"]);
  assert.deepEqual(url.searchParams.getAll("test_plans"), ["smoke"]);
  assert.deepEqual(url.searchParams.getAll("test_cases"), ["install / test"]);
  assert.deepEqual(url.searchParams.getAll("template_ids"), ["template-1"]);
  assert.deepEqual(url.searchParams.getAll("test_result_statuses"), [
    "FAILED",
    "SKIPPED",
  ]);
  assert.deepEqual(url.searchParams.getAll("execution_metadata"), [
    `${Buffer.from("ci:provider").toString("base64")}:${Buffer.from("GitHub Actions").toString("base64")}`,
    `${Buffer.from("ci:provider").toString("base64")}:${Buffer.from("Buildkite").toString("base64")}`,
  ]);
  assert.equal(
    new URL(
      model.viewRuleFiltersUrl("", 73, { ...rule, families: [] }),
      "https://test-observer.invalid",
    ).pathname,
    "/test-results",
  );
});

void test("rule mutation helpers replace confirmed values and remove deleted rules", () => {
  const second = { ...rule, id: 15, enabled: false };
  const disabled = { ...rule, enabled: false };
  const replaced = model.replaceAttachmentRule([rule, second], disabled);
  assert.equal(replaced[0], disabled);
  assert.equal(replaced[1], second);
  assert.equal(rule.enabled, true, "the existing page state is not mutated");
  assert.deepEqual(model.removeAttachmentRule(replaced, 14), [second]);
});
