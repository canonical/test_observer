// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import assert from "node:assert/strict";
import { before, test } from "node:test";
import { resolve } from "node:path";
import { build } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";

/** @type {typeof import('./test-results-bulk-entry')} */
let model;
const families = [
  {
    name: "configured",
    api_name: "generic",
    stages: [],
    columns: [],
    filters: [],
  },
];
const ready = {
  available: true,
  loading: false,
  moving: false,
  accessError: false,
  unapplied: false,
  mutating: false,
};
const parse = (
  /** @type {string | URLSearchParams} */ input = "artefacts=one",
) => model.parseSearch(new URLSearchParams(input), families);
const pair = (/** @type {string} */ category, /** @type {string} */ value) =>
  `${Buffer.from(category).toString("base64")}:${Buffer.from(value).toString("base64")}`;
/** @template T @param {import('../src/lib/testResultsBulk').Capability<T>} result @returns {T} */
function value(result) {
  assert.ok(result.ok, result.ok ? "" : result.reason);
  return result.value;
}
/** @param {import('../src/lib/testResultsBulk').Capability<unknown>} result @param {RegExp} reason */
function denied(result, reason) {
  assert.equal(result.ok, false);
  assert.match(result.reason, reason);
}
const json = (/** @type {unknown} */ body, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
/** @param {string} [input] */
function selected(input) {
  const query = parse(input);
  const selection = new model.TestResultsSelection();
  selection.setQuery(model.selectionQuery(query));
  selection.updateCount(100);
  const page = selection.page([11, 12], () => true, [
    { resultId: 11, executionId: 501 },
    { resultId: 12, executionId: 501 },
  ]);
  page.toggle([11, 12], true);
  return { selection, page, query };
}
/** @param {string} [input] */
function queryTarget(input) {
  const { selection, page, query } = selected(input);
  page.toggleAllMatches();
  return value(model.freezeBulkTarget(selection.snapshot(), query, ready));
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
          lib: { entry: "tests/test-results-bulk-entry.js", formats: ["es"] },
          rolldownOptions: { output: { codeSplitting: false } },
        },
      })
    )
  );
  const bundle = built[0].output.find((item) => item.type === "chunk");
  assert.ok(bundle);
  // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
  model = await import(
    `data:text/javascript;base64,${Buffer.from(bundle.code).toString("base64")}`
  );
});

void test("POST JSON preserves every active field without GET encoding, pagination, alias or presentation", () => {
  const params = new URLSearchParams({
    families: "generic",
    artefacts: "one,two",
    artefact_versions: "1+2",
    artefact_stages: ",candidate",
    artefact_tracks: "stable",
    environments: "lab",
    test_plans: "plan",
    test_cases: "case",
    template_ids: "id",
    test_result_statuses: "FAILED",
    artefact_is_archived: "false",
    execution_is_latest: "false",
    rerun_is_requested: "false",
    issues: "1,2",
    assignee_ids: "none",
    from_date: "2026-01-01T01:00:00.1234560+01:00",
    until_date: "2026-02-01T00:00:00.999999Z",
    limit: "1",
    offset: "99",
    view: "anything",
  });
  params.append("execution_metadata", pair("c:at, 🐧", "literal,:"));
  params.append("execution_metadata", pair("__proto__", "constructor"));
  const query = parse(params);
  assert.deepEqual(query.problems, []);
  const body = model.mutationFilters(query.filters);
  assert.deepEqual(JSON.parse(JSON.stringify(body)), {
    families: ["generic"],
    artefacts: ["one", "two"],
    artefact_versions: ["1+2"],
    artefact_stages: ["", "candidate"],
    artefact_tracks: ["stable"],
    environments: ["lab"],
    test_plans: ["plan"],
    test_cases: ["case"],
    template_ids: ["id"],
    test_result_statuses: ["FAILED"],
    artefact_is_archived: false,
    execution_is_latest: false,
    rerun_is_requested: false,
    issues: [1, 2],
    reviewer_ids: "none",
    from_date: "2026-01-01T01:00:00.1234560+01:00",
    until_date: "2026-02-01T00:00:00.999999Z",
    execution_metadata: {
      "c:at, 🐧": ["literal,:"],
      ["__proto__"]: ["constructor"],
    },
  });
  assert.deepEqual(
    model.mutationFilters(parse("issues=any&reviewer_ids=none").filters),
    { issues: "any", reviewer_ids: "none" },
  );
  assert.deepEqual(model.mutationFilters(model.emptyFilters()), {});
  query.filters.execution_metadata[0].values.push("later");
  assert.deepEqual(body.execution_metadata?.["c:at, 🐧"], ["literal,:"]);
  assert.ok(Object.isFrozen(body.execution_metadata["c:at, 🐧"]));
});

void test("semantic frozen predicates normalize duplicates, order, timezone and exact fractions without mutating input", () => {
  const a = parse(
    `artefacts=b,a,a&from_date=2026-01-01T01:00:00.123456%2B01:00&execution_metadata=${pair("c", "two")}&execution_metadata=${pair("c", "one")}`,
  );
  const b = parse(
    `artefacts=a,b&from_date=2026-01-01T00:00:00.1234560Z&limit=3&offset=88&view=no&execution_metadata=${pair("c", "one")}&execution_metadata=${pair("c", "two")}`,
  );
  const snapshot = model.selectionQuery(a);
  assert.ok(snapshot);
  assert.equal(snapshot.key, model.selectionQuery(b)?.key);
  assert.notEqual(
    snapshot.key,
    model.selectionQuery(
      parse("artefacts=a,b&from_date=2026-01-01T00:00:00.123457Z"),
    )?.key,
  );
  assert.ok(Object.isFrozen(snapshot));
  assert.throws(
    () =>
      Reflect.apply(
        Array.prototype.push,
        snapshot.filters.execution_metadata[0].values,
        ["no"],
      ),
    TypeError,
  );
  a.filters.artefacts.push("draft");
  assert.deepEqual(snapshot.filters.artefacts, ["b", "a"]);
});

void test("explicit and opted-in query snapshots are defensive and mutually exclusive; empty selection never means all", () => {
  const { selection, page, query } = selected();
  const target = value(
    model.freezeBulkTarget(selection.snapshot(), query, ready),
  );
  assert.equal(target.kind, "explicit");
  const wire = model.issueAttachmentPayload(target);
  assert.deepEqual(wire, { test_results: [11, 12] });
  assert.ok(Object.isFrozen(wire.test_results));
  assert.deepEqual(value(model.executionIds(target)), [501]);
  const leaked = /** @type {Set<number>} */ (selection.explicitIds);
  leaked.add(99);
  assert.equal(selection.explicitIds.has(99), false);
  page.toggleAllMatches();
  const all = value(model.freezeBulkTarget(selection.snapshot(), query, ready));
  assert.deepEqual(model.issueAttachmentPayload(all), {
    test_results_filters: { artefacts: ["one"] },
  });
  assert.deepEqual(wire, { test_results: [11, 12] });
  assert.ok(Object.isFrozen(all));
  selection.clear();
  denied(
    model.freezeBulkTarget(selection.snapshot(), query, ready),
    /Select at least one/,
  );
  assert.deepEqual(model.issueAttachmentPayload(all), {
    test_results_filters: { artefacts: ["one"] },
  });
});

void test("all exclusions block instead of enumerating or broadening, including zero selected count", () => {
  const { selection, page, query } = selected();
  page.toggleAllMatches();
  page.toggle([11], false);
  denied(
    model.freezeBulkTarget(selection.snapshot(), query, ready),
    /exclusions.*Remove all exclusions/,
  );
  selection.updateCount(0);
  denied(
    model.freezeBulkTarget(selection.snapshot(), query, ready),
    /exclusions/,
  );
});

void test("date-only remains a search and explicit selection but cannot become query-based mutation", () => {
  const { selection, page, query } = selected(
    "from_date=2026-01-01T00:00:00.000001Z",
  );
  assert.equal(query.hasFilters, true);
  assert.equal(
    value(model.freezeBulkTarget(selection.snapshot(), query, ready)).kind,
    "explicit",
  );
  page.toggleAllMatches();
  denied(
    model.freezeBulkTarget(selection.snapshot(), query, ready),
    /date-only/,
  );
});

void test("invalid IDs and invalid, unknown, empty, stale or unavailable predicates fail closed", () => {
  const { selection, query } = selected();
  for (const id of [0, -1, 1.5, Number.MAX_SAFE_INTEGER + 1, NaN])
    denied(
      model.freezeBulkTarget(
        { ...selection.snapshot(), explicitIds: [11, id] },
        query,
        ready,
      ),
      /invalid result IDs/,
    );
  for (const input of [
    "unknown=x&artefacts=one",
    "issues=0",
    "from_date=bad",
    "",
    "view=x&limit=1",
    "families=unknown",
  ])
    denied(
      model.freezeBulkTarget(selection.snapshot(), parse(input), ready),
      /valid applied query/,
    );
  denied(
    model.freezeBulkTarget(selection.snapshot(), parse("artefacts=two"), ready),
    /valid applied query/,
  );
  const bad = { ...query, filters: { ...query.filters, unknown: ["x"] } };
  denied(
    model.freezeBulkTarget(selection.snapshot(), bad, ready),
    /valid applied query/,
  );
  assert.throws(() => model.mutationFilters(bad.filters), /Unknown/);
  for (const state of [
    { loading: true },
    { moving: true },
    { accessError: true },
    { available: false },
    { unapplied: true },
    { mutating: true },
  ])
    assert.equal(
      model.freezeBulkTarget(selection.snapshot(), query, {
        ...ready,
        ...state,
      }).ok,
      false,
    );
});

void test("selected execution context retains cross-page IDs, prunes unselected rows and has no response/private state", () => {
  const { selection, page, query } = selected();
  page.toggle([12], false);
  const row = { resultId: 21, executionId: 600, io_log: "private" };
  const second = selection.page([21, 22], () => true, [
    row,
    { resultId: 22, executionId: 601 },
  ]);
  second.toggle([21], true);
  row.executionId = 999;
  assert.deepEqual(selection.snapshot().executions, [
    { resultId: 11, executionId: 501 },
    { resultId: 21, executionId: 600 },
  ]);
  assert.deepEqual(
    value(
      model.executionIds(
        value(model.freezeBulkTarget(selection.snapshot(), query, ready)),
      ),
    ),
    [501, 600],
  );
  second.toggle([21], false);
  assert.deepEqual(selection.snapshot().executions, [
    { resultId: 11, executionId: 501 },
  ]);
  assert.throws(() => {
    selection.snapshot().executions[0].executionId = 1;
  }, TypeError);
  selection.clear();
  second.toggle([21], true);
  assert.deepEqual(selection.snapshot().executions, []);
  assert.equal(
    second.enabled(),
    false,
    "clear revokes even same-query capabilities",
  );
});

void test("stale pages and stale queries cannot import context; all mode stores no enumerated execution IDs", () => {
  const { selection, page, query } = selected();
  let current = false;
  const stale = selection.page([22], () => current, [
    { resultId: 22, executionId: 700 },
  ]);
  stale.toggle([22], true);
  assert.equal(
    selection.snapshot().executions.some((item) => item.executionId === 700),
    false,
  );
  page.toggleAllMatches();
  assert.deepEqual(selection.snapshot().executions, []);
  selection.setQuery(model.selectionQuery(parse("artefacts=two")));
  current = true;
  stale.toggle([22], true);
  assert.deepEqual(selection.snapshot().executions, []);
  denied(
    model.freezeBulkTarget(selection.snapshot(), query, ready),
    /current valid applied/,
  );
});

void test("missing/invalid/conflicting execution context never sends result IDs as executions", () => {
  const { selection, query } = selected();
  const base = value(
    model.freezeBulkTarget(selection.snapshot(), query, ready),
  );
  assert.equal(base.kind, "explicit");
  for (const executions of [
    [],
    [{ resultId: 11, executionId: -1 }],
    [
      { resultId: 11, executionId: 500 },
      { resultId: 11, executionId: 501 },
    ],
  ])
    assert.equal(model.executionIds({ ...base, executions }).ok, false);
});

void test("query reruns intersect default guards without ID/criteria OR or pagination", () => {
  const target = queryTarget("artefacts=one&limit=1&offset=50");
  assert.deepEqual(value(model.rerunPlan(target, "create")), {
    payload: {
      test_results_filters: {
        artefacts: ["one"],
        rerun_is_requested: false,
        execution_is_latest: true,
        artefact_is_archived: false,
      },
    },
    silent: true,
    scope: "query-intersection",
  });
  assert.deepEqual(value(model.rerunPlan(target, "delete")), {
    payload: {
      test_results_filters: { artefacts: ["one"], rerun_is_requested: true },
    },
    silent: true,
    scope: "query-intersection",
  });
  assert.equal(
    "test_execution_ids" in value(model.rerunPlan(target, "create")).payload,
    false,
  );
  const priority = value(model.rerunPlan(target, "create", { priority: 0 }));
  assert.equal(priority.payload.priority, 0);
  assert.ok(Object.isFrozen(priority.payload.test_results_filters?.artefacts));
});

void test("query rerun contradictions block, never override the applied archive/latest/request state", () => {
  for (const input of [
    "artefact_is_archived=true",
    "execution_is_latest=false",
    "rerun_is_requested=true",
  ])
    denied(model.rerunPlan(queryTarget(input), "create"), /contradicts/);
  denied(
    model.rerunPlan(queryTarget("rerun_is_requested=false"), "delete"),
    /contradicts/,
  );
  denied(
    model.rerunPlan(queryTarget("artefact_is_archived=true"), "delete", {
      eligibleOnly: true,
    }),
    /contradicts/,
  );
  const target = queryTarget(
    "artefact_is_archived=true&execution_is_latest=false",
  );
  assert.deepEqual(
    value(model.rerunPlan(target, "create", { eligibleOnly: false })).payload,
    {
      test_results_filters: {
        artefact_is_archived: true,
        execution_is_latest: false,
        rerun_is_requested: false,
      },
    },
  );
  assert.equal(model.rerunPlan(target, "delete").ok, true);
});

void test("explicit reruns require honest exact-group opt-in with no eligibility/request-state filters", () => {
  const { selection, query } = selected();
  const target = value(
    model.freezeBulkTarget(selection.snapshot(), query, ready),
  );
  denied(model.rerunPlan(target, "create"), /ORs execution IDs/);
  denied(model.rerunPlan(target, "delete"), /ORs execution IDs/);
  denied(
    model.rerunPlan(target, "create", {
      explicitMode: "exact",
      eligibleOnly: true,
    }),
    /guarded explicit/,
  );
  assert.deepEqual(
    value(model.rerunPlan(target, "create", { explicitMode: "exact" })),
    {
      payload: { test_execution_ids: [501] },
      scope: "exact-execution-groups",
      silent: true,
    },
  );
  assert.deepEqual(
    value(model.rerunPlan(target, "delete", { explicitMode: "exact" })).payload,
    { test_execution_ids: [501] },
  );
  for (const priority of [1.1, NaN, 1_000_001])
    denied(
      model.rerunPlan(target, "create", { explicitMode: "exact", priority }),
      /priority/,
    );
  denied(
    model.rerunPlan(target, "delete", { explicitMode: "exact", priority: 0 }),
    /priority/,
  );
});

void test("query-level future rule adapter maps every supported field and ignores presentation/pagination", () => {
  const params = new URLSearchParams({
    families: "generic",
    artefacts: "one",
    artefact_versions: "1",
    artefact_stages: "",
    artefact_tracks: "track",
    environments: "lab",
    test_plans: "plan",
    test_cases: "case",
    template_ids: "template",
    test_result_statuses: "FAILED",
    execution_metadata: pair("cat", "value"),
    view: "view",
    limit: "1",
    offset: "999",
  });
  const rules = value(model.attachmentRuleFilters(parse(params), ready));
  assert.deepEqual(rules, {
    families: ["generic"],
    artefacts: ["one"],
    artefact_versions: ["1"],
    artefact_stages: [""],
    artefact_tracks: ["track"],
    environment_names: ["lab"],
    test_plans: ["plan"],
    test_case_names: ["case"],
    template_ids: ["template"],
    test_result_statuses: ["FAILED"],
    execution_metadata: { cat: ["value"] },
  });
  assert.ok(Object.isFrozen(rules.execution_metadata.cat));
});

void test("rule adapter rejects each unsupported active condition and status-only, never drops filters", () => {
  for (const condition of [
    "artefact_is_archived=false",
    "execution_is_latest=false",
    "rerun_is_requested=false",
    "issues=none",
    "reviewer_ids=any",
    "from_date=2026-01-01T00:00:00Z",
    "until_date=2026-01-01T00:00:00Z",
  ])
    denied(
      model.attachmentRuleFilters(parse(`artefacts=one&${condition}`), ready),
      /cannot represent/,
    );
  denied(
    model.attachmentRuleFilters(parse("test_result_statuses=FAILED"), ready),
    /non-status/,
  );
  denied(
    model.attachmentRuleFilters(parse("artefacts=one&unknown=x"), ready),
    /valid/,
  );
  denied(
    model.attachmentRuleFilters(parse(), { ...ready, unapplied: true }),
    /draft/,
  );
});

const permissions = [
  "change_issue_attachment",
  "change_issue_attachment_bulk",
  "change_rerun",
  "change_rerun_bulk",
  "change_attachment_rule",
  "change_issue",
  "view_issue",
];
const user = (grants = permissions, is_admin = false) => ({
  id: 1,
  email: "a@example.invalid",
  name: "User",
  launchpad_handle: null,
  is_admin,
  teams: [{ permissions: grants }],
});
/** @param {unknown} body @param {number} [status] */
const auth = (body, status = 200) =>
  model.refreshBulkPermissions(() => Promise.resolve(json(body, status)));

void test("refreshed global team grants allow every action including reruns without admin or AMR inference", async () => {
  const gate = await auth(user());
  for (const action of /** @type {const} */ ([
    "issueAttachment",
    "rerun",
    "attachmentRule",
    "createIssue",
    "lookupIssue",
  ]))
    assert.equal(gate.check(action).ok, true);
  const restricted = await auth(
    user(["change_rerun", "change_issue_attachment"]),
  );
  assert.equal(restricted.check("rerun", false).ok, true);
  assert.equal(restricted.check("issueAttachment", false).ok, true);
  denied(
    restricted.check("rerun"),
    /change_rerun_bulk.*AMR|change_rerun_bulk.*Artefact-matching/,
  );
  denied(restricted.check("issueAttachment"), /change_issue_attachment_bulk/);
  denied(restricted.check("lookupIssue"), /view_issue/);
  denied(restricted.check("createIssue"), /change_issue/);
});

void test("cached admin is not authorization; only a fresh confirmed admin can allow", async () => {
  model.userStore.current = user([], true);
  const unknown = await auth(null, 500);
  assert.equal(
    model.userStore.current.is_admin,
    true,
    "display cache is retained",
  );
  denied(unknown.check("rerun"), /unknown/);
  const confirmed = await auth(user([], true));
  assert.equal(confirmed.check("rerun").ok, true);
  assert.equal(confirmed.check("createIssue").ok, true);
});

void test("unknown and expired sessions fail closed for team grants and admin; older gates are revoked", async () => {
  for (const profile of [user(), user([], true)]) {
    const prior = await auth(profile);
    const unknown = await auth(null, 503);
    denied(unknown.check("rerun"), /unknown/);
    denied(prior.check("rerun"), /superseded/);
    for (const status of [401, 403]) {
      const gate = await auth(profile);
      const expired = await auth(null, status);
      denied(expired.check("issueAttachment"), /Log in/);
      denied(gate.check("rerun"), /superseded/);
      assert.equal(model.userStore.current, null);
    }
  }
  denied((await auth(null)).check("lookupIssue"), /Log in/);
});

void test("superseded/aborted permission refreshes and any subsequent refresh cannot authorize", async () => {
  /** @type {(response: Response) => void} */
  let complete = (response) => {
    throw new Error(`Unexpected completion: ${response.status}`);
  };
  const pending = model.refreshBulkPermissions(
    () =>
      new Promise((resolve) => {
        complete = resolve;
      }),
  );
  const newer = await auth(user([]));
  complete(json(user([], true)));
  denied((await pending).check("rerun"), /superseded/);
  denied(newer.check("rerun"), /Missing/);
  const controller = new AbortController();
  const gate = await model.refreshBulkPermissions(
    () => Promise.resolve(json(user())),
    controller.signal,
  );
  controller.abort();
  denied(gate.check("rerun"), /cancelled/);
  const aborted = new AbortController();
  const delayed = model.refreshBulkPermissions(
    () =>
      new Promise((resolve) => {
        complete = resolve;
      }),
    aborted.signal,
  );
  aborted.abort();
  complete(json(user([], true)));
  denied((await delayed).check("rerun"), /cancelled/);
  const valid = await auth(user());
  const other = model.userStore.refresh(
    () =>
      new Promise((resolve) => {
        complete = resolve;
      }),
  );
  denied(valid.check("rerun"), /superseded/);
  complete(json(user()));
  await other;
});
