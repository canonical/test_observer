// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { createServer } from "vite";

/** @type {import("vite").ViteDevServer | undefined} */
let vite;
/** @type {typeof import("../src/lib/artefactMetadata").columnValue | undefined} */
let columnValue;
/** @type {typeof import("../src/lib/artefactMetadata").columnSortValue | undefined} */
let columnSortValue;
/** @type {typeof import("svelte/server").render | undefined} */
let render;
/** @type {import("svelte").Component<any> | undefined} */
let StagesBreadcrumb;

/** @param {string} stage
 * @returns {import("../src/lib/types").Artefact}
 */
function artefactWithStage(stage) {
  return {
    id: 1,
    name: "test",
    version: "",
    track: "",
    store: "",
    branch: "",
    series: "",
    repo: "",
    source: "",
    os: "",
    release: "",
    owner: "",
    sha256: "",
    image_url: "",
    stage,
    family: "test",
    status: "UNDECIDED",
    comment: "",
    archived: false,
    reviewers: [],
    due_date: null,
    created_at: "",
    bug_link: "",
    jira_issue: null,
    all_environment_reviews_count: 0,
    completed_environment_reviews_count: 0,
  };
}

before(async () => {
  vite = await createServer({
    configFile: "vite.config.ts",
    appType: "custom",
    logLevel: "silent",
    server: { middlewareMode: true },
  });
  ({ columnValue, columnSortValue } = await vite.ssrLoadModule(
    "/src/lib/artefactMetadata.ts",
  ));
  ({ render } = await vite.ssrLoadModule("svelte/server"));
  ({ default: StagesBreadcrumb } = await vite.ssrLoadModule(
    "/src/lib/components/artefact/StagesBreadcrumb.svelte",
  ));
});

after(async () => {
  await vite?.close();
});

void test("stage columns display arbitrary and empty stage values", () => {
  if (!columnValue || !columnSortValue) {
    throw new Error("Stage column formatter was not loaded");
  }

  const column = {
    key: "stage",
    label: "Stage",
    field: "stage",
    format: "stage",
  };
  assert.equal(columnValue(artefactWithStage("beta"), column), "beta");
  assert.equal(
    columnValue(artefactWithStage("custom-channel"), column),
    "custom-channel",
  );
  assert.equal(columnValue(artefactWithStage(""), column), "empty stage");
  assert.equal(columnSortValue(artefactWithStage(""), column), "");
  assert.equal(
    columnSortValue(artefactWithStage("empty stage"), column),
    "empty stage",
  );
});

void test("stage breadcrumb displays only the artefact's current stage", () => {
  if (!render || !StagesBreadcrumb) {
    throw new Error("Stage breadcrumb test modules were not loaded");
  }

  const body = render(StagesBreadcrumb, {
    props: { artefact: { stage: "custom-channel" } },
  }).body;
  assert.match(
    body,
    /class="stage current[^"]*"[^>]*aria-current="step"[^>]*>[\s\S]*?Custom-channel/,
  );
  assert.doesNotMatch(body, /separator/);
});

void test("stage breadcrumb labels an empty stage", () => {
  if (!render || !StagesBreadcrumb) {
    throw new Error("Stage breadcrumb test modules were not loaded");
  }

  const body = render(StagesBreadcrumb, {
    props: { artefact: { stage: "" } },
  }).body;
  assert.match(body, /Empty stage/);
});
