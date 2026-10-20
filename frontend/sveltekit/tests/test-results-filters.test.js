// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import assert from "node:assert/strict";
import { before, test } from "node:test";
import { resolve } from "node:path";
import { readFile } from "node:fs/promises";
import { build } from "vite";

/** @type {typeof import('../src/lib/testResultsSearch')} */
let model;
const families = [
  {
    name: "configured",
    api_name: "snap",
    stages: [],
    columns: [],
    filters: [],
  },
];
const parse = (/** @type {string | URLSearchParams} */ input) =>
  model.parseSearch(new URLSearchParams(input), families);
const pair = (/** @type {string} */ category, /** @type {string} */ value) =>
  `${Buffer.from(category).toString("base64")}:${Buffer.from(value).toString("base64")}`;

before(async () => {
  const built = /** @type {{output: {type: string; code: string}[]}[]} */ (
    /** @type {unknown} */ (
      await build({
        configFile: false,
        logLevel: "silent",
        resolve: { alias: { $lib: resolve("src/lib") } },
        build: {
          write: false,
          lib: { entry: "src/lib/testResultsSearch.ts", formats: ["es"] },
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

void test("all typed filter definitions match the existing GET contract, without exposing deferred editors", async () => {
  // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
  const schema =
    /** @type {{paths: Record<string, {get: {parameters: {name: string}[]}}>}} */ (
      JSON.parse(
        await readFile(
          new URL("../../../backend/schemata/openapi.json", import.meta.url),
          "utf8",
        ),
      )
    );
  const names = schema.paths["/v1/test-results"].get.parameters.map(
    (param) => param.name,
  );
  for (const key of model.SEARCH_FILTERS) assert.ok(names.includes(key), key);
  assert.equal(model.SEARCH_FILTERS.length, 18);
  assert.equal(model.EDITABLE_SEARCH_FILTERS.length, 8);
  assert.ok(
    !model.SEARCH_FILTERS.includes(
      /** @type {never} */ ("test_execution_statuses"),
    ),
  );
  assert.equal(model.hasFilters(model.emptyFilters()), false);
  assert.equal(parse("view=anything&limit=2&offset=3").hasFilters, false);
});

void test("round-trips every typed field through page and repeated API parameters, preserving false, none stage and Unicode metadata", () => {
  const params = new URLSearchParams({
    families: "snap",
    test_result_statuses: "FAILED,PASSED",
    artefacts: "one,two",
    artefact_versions: "1+2",
    artefact_tracks: "stable",
    environments: "lab",
    test_plans: "smoke",
    test_cases: "case",
    artefact_stages: ",candidate",
    artefact_is_archived: "false",
    rerun_is_requested: "true",
    execution_is_latest: "false",
    issues: "001,2",
    reviewer_ids: "none",
    from_date: "2024-02-29T00:00:00.123456+01:30",
    until_date: "2026-10-20T15:10:00Z",
    template_ids: "id-one,id-two",
    execution_metadata: `${pair("c:at, 🐧", "a,b:c /+?é")},${pair("c:at, 🐧", "二")}`,
    view: "presentation-only",
  });
  params.append("execution_metadata", pair("__proto__", "constructor"));
  params.append("execution_metadata", pair(" c:at ", " \uFEFF值 "));
  const query = parse(params);
  assert.deepEqual(query.problems, []);
  assert.equal(query.hasFilters, true);
  assert.deepEqual(query.filters.artefact_stages, ["", "candidate"]);
  assert.deepEqual(query.filters.issues, [1, 2]);
  assert.equal(query.filters.reviewer_ids, "none");
  assert.equal(query.filters.artefact_is_archived, false);
  assert.equal(query.filters.execution_is_latest, false);
  assert.deepEqual(query.filters.execution_metadata, [
    { category: "c:at, 🐧", values: ["a,b:c /+?é", "二"] },
    { category: "__proto__", values: ["constructor"] },
    { category: " c:at ", values: [" \uFEFF值 "] },
  ]);
  const api = model.searchParams(query.filters, 3, 6);
  assert.deepEqual(api.getAll("artefacts"), ["one", "two"]);
  assert.deepEqual(api.getAll("artefact_stages"), ["", "candidate"]);
  assert.deepEqual(api.getAll("issues"), ["1", "2"]);
  assert.deepEqual(api.getAll("template_ids"), ["id-one", "id-two"]);
  assert.deepEqual(api.getAll("execution_metadata"), [
    pair("c:at, 🐧", "a,b:c /+?é"),
    pair("c:at, 🐧", "二"),
    pair("__proto__", "constructor"),
    pair(" c:at ", " \uFEFF值 "),
  ]);
  assert.equal(api.has("view"), false);
  assert.equal(api.get("from_date"), params.get("from_date"));
  assert.equal(api.get("offset"), "6");
  assert.deepEqual(parse(api).filters, query.filters);
  assert.deepEqual(parse(api).problems, []);
  assert.equal(model.filtersEqual(parse(api).filters, query.filters), true);
});

void test("each meaningful scalar, date, empty stage, ID mode and metadata condition is independently active", () => {
  for (const input of [
    "artefact_is_archived=false",
    "rerun_is_requested=false",
    "execution_is_latest=false",
    "artefact_stages=",
    "issues=any",
    "issues=none",
    "reviewer_ids=1",
    "reviewer_ids=none",
    "from_date=2026-01-01T00:00:00Z",
    "until_date=2026-01-01T00:00:00Z",
    `execution_metadata=${pair("a", "b")}`,
    "template_ids=template",
  ]) {
    const query = parse(input);
    assert.deepEqual(query.problems, [], input);
    assert.equal(query.hasFilters, true, input);
    assert.ok(model.searchParams(query.filters).size > 1, input);
  }
  const empty = model.emptyFilters();
  for (const key of model.SEARCH_FILTERS)
    assert.equal(model.filterIsActive(key, empty), false, key);
  assert.equal(empty.from_date, null);
  assert.equal(empty.artefact_is_archived, null);
});

void test("repeated and comma ID alternatives deduplicate safely; sentinels cannot mix with IDs or one another", () => {
  for (const key of ["issues", "reviewer_ids", "assignee_ids"]) {
    const target = key === "assignee_ids" ? "reviewer_ids" : key;
    assert.deepEqual(
      Reflect.get(parse(`${key}=1, 002&${key}=2,3`).filters, target),
      [1, 2, 3],
    );
    for (const mode of ["any", "none"]) {
      const query = parse(`${key}=${mode}&${key}=${mode}`);
      assert.deepEqual(query.problems, []);
      assert.equal(Reflect.get(query.filters, target), mode);
    }
    for (const invalid of [
      "any,none",
      "any,1",
      "1,none",
      "0",
      "-1",
      "1.1",
      "1e2",
      "+1",
      "Infinity",
      "9007199254740992",
      "",
      "1,",
      "1,nope",
      "ANY",
    ]) {
      assert.ok(
        parse(new URLSearchParams([[key, invalid]])).problems.length,
        `${key}=${invalid}`,
      );
    }
    assert.deepEqual(parse(`${key}=9007199254740991`).problems, []);
  }
});

void test("legacy assignee links migrate to canonical reviewer IDs; explicit canonical presence wins, never invalid fallback", () => {
  for (const [input, expected] of [
    ["assignee_ids=1,2", [1, 2]],
    ["assignee_ids=any", "any"],
    ["assignee_ids=1&reviewer_ids=none", "none"],
    ["reviewer_ids=2&assignee_ids=1", [2]],
    // A shadowed deprecated alias is not the selected condition, as in Flutter.
    ["reviewer_ids=2&assignee_ids=invalid", [2]],
  ]) {
    const query = parse(/** @type {string} */ (input));
    assert.deepEqual(query.problems, []);
    assert.deepEqual(query.filters.reviewer_ids, expected);
    const api = model.searchParams(query.filters);
    assert.equal(api.has("assignee_ids"), false);
    assert.deepEqual(
      api.getAll("reviewer_ids"),
      Array.isArray(expected) ? expected.map(String) : [expected],
    );
  }
  for (const input of [
    "reviewer_ids=&assignee_ids=1",
    "reviewer_ids=bad&assignee_ids=1",
    "reviewer_ids=none,1&assignee_ids=any",
  ])
    assert.ok(parse(input).problems.length, input);
});

void test("metadata is strict UTF-8 standard Base64, safely groups categories, and never drops malformed pairs", () => {
  const params = new URLSearchParams();
  params.append(
    "execution_metadata",
    `${pair("a:b,c", "one")},${pair("a:b,c", "two")}`,
  );
  params.append("execution_metadata", pair("a:b,c", "one"));
  params.append("execution_metadata", pair("\uFEFF", "\uFEFF"));
  assert.deepEqual(parse(params).filters.execution_metadata, [
    { category: "a:b,c", values: ["one", "two"] },
    { category: "\uFEFF", values: ["\uFEFF"] },
  ]);
  assert.equal(
    model.encodeMetadataPart("🐧:+/漢"),
    Buffer.from("🐧:+/漢").toString("base64"),
  );
  for (const invalid of [
    "",
    "plain text",
    "YQ==",
    "YQ==:",
    ":Yg==",
    "YQ==:Yg==:Yw==",
    "YQ==:Yg",
    "YQ==:Yg__",
    "YQ==:Yg--",
    "YQ==:Yh==", // noncanonical padding bits
    "YQ==: Yg==",
    "YQ==:/w==",
    "YQ==:wK8=", // malformed UTF-8
    `${pair("a", "b")},`,
  ]) {
    const query = parse(
      new URLSearchParams([
        ["execution_metadata", invalid],
        ["artefacts", "valid"],
      ]),
    );
    assert.ok(
      query.problems.some((problem) => problem.includes("execution_metadata")),
      invalid,
    );
  }
});

void test("dates validate real Gregorian ISO instants, explicit offsets and one-sided inclusive bounds without normalization", () => {
  for (const value of [
    "2024-02-29T00:00:00Z",
    "2000-02-29T23:59:59.123456Z",
    "0001-01-01T00:00:00Z",
    "0099-12-31T00:00:00-01:00",
    "2026-01-01T12:00:00+05:45",
    "2026-01-01T00:00:00-23:59",
  ]) {
    const query = parse(new URLSearchParams([["from_date", value]]));
    assert.deepEqual(query.problems, [], value);
    assert.equal(query.filters.from_date, value);
    assert.equal(model.searchParams(query.filters).get("from_date"), value);
  }
  for (const value of [
    "",
    "2026-01-01",
    "2026-01-01T12:00:00",
    "2026-01-01 12:00:00Z",
    "2026-02-29T00:00:00Z",
    "1900-02-29T00:00:00Z",
    "2024-02-30T00:00:00Z",
    "2026-04-31T00:00:00Z",
    "2026-13-01T00:00:00Z",
    "2026-00-01T00:00:00Z",
    "2026-01-00T00:00:00Z",
    "2026-01-01T24:00:00Z",
    "2026-01-01T00:60:00Z",
    "2026-01-01T00:00:60Z",
    "0000-01-01T00:00:00Z",
    "2026-01-01T00:00:00+24:00",
    "2026-01-01T00:00:00+00:60",
    "2026-01-01T00:00:00+0100",
    "2026-01-01T00:00:00.Z",
  ]) {
    for (const key of ["from_date", "until_date"])
      assert.ok(
        parse(new URLSearchParams([[key, value]])).problems.length,
        `${key}=${value}`,
      );
  }
  assert.ok(
    parse("from_date=2026-01-01T00:00:00Z&from_date=2026-01-02T00:00:00Z")
      .problems.length,
  );
  for (const [from, until, valid] of [
    ["2026-01-01T01:00:00+01:00", "2026-01-01T00:00:00Z", true],
    ["2026-01-01T00:00:00.100Z", "2026-01-01T00:00:00.1Z", true],
    ["2026-01-01T00:00:00.123456Z", "2026-01-01T00:00:00.123455Z", false],
    ["2026-01-01T00:00:00.000001Z", "2026-01-01T00:00:00Z", false],
    ["2026-01-01T00:00:00Z", "2025-12-31T23:59:59.999999Z", false],
    ["2026-01-01T00:00:00-01:00", "2026-01-01T00:30:00Z", false],
  ]) {
    const query = parse(
      new URLSearchParams([
        ["from_date", String(from)],
        ["until_date", String(until)],
      ]),
    );
    assert.equal(query.problems.length === 0, valid, `${from} to ${until}`);
  }
});

void test("date bounds reject sub-microsecond values rather than allowing backend truncation, while exact microseconds and trailing zeros round-trip unchanged", () => {
  for (const fraction of ["0000001", "1234567", "1234560001", "9999999"]) {
    const value = `2026-01-01T00:00:00.${fraction}Z`;
    assert.throws(() => model.parseIsoInstant(value), /microsecond/);
    for (const key of ["from_date", "until_date"]) {
      const query = parse(new URLSearchParams([[key, value]]));
      assert.ok(
        query.problems.some(
          (problem) => problem.includes(key) && problem.includes("microsecond"),
        ),
        value,
      );
      assert.equal(
        Reflect.get(query.filters, key),
        null,
        "unrepresentable bounds are not rounded or truncated",
      );
    }
  }
  for (const fraction of [
    "000001",
    "123456",
    "999999",
    "0000000",
    "123456000",
    "1000000000",
  ]) {
    const value = `2026-01-01T00:00:00.${fraction}+01:30`;
    for (const key of ["from_date", "until_date"]) {
      const query = parse(new URLSearchParams([[key, value]]));
      assert.deepEqual(query.problems, [], value);
      assert.equal(query.hasFilters, true);
      assert.equal(Reflect.get(query.filters, key), value);
      assert.equal(
        model.searchParams(query.filters).get(key),
        value,
        "representable bounds retain their original text",
      );
    }
  }
  for (const [left, right, expected] of [
    ["2026-01-01T00:00:00.000001Z", "2026-01-01T00:00:00Z", 1],
    ["2026-01-01T00:00:00.123455Z", "2026-01-01T00:00:00.123456Z", -1],
    ["2026-01-01T01:30:00.123456000+01:30", "2026-01-01T00:00:00.123456Z", 0],
  ]) {
    const from = model.parseIsoInstant(String(left));
    const until = model.parseIsoInstant(String(right));
    assert.equal(model.compareInstants(from, until), expected);
    const query = parse(
      new URLSearchParams([
        ["from_date", from],
        ["until_date", until],
      ]),
    );
    assert.deepEqual(
      query.problems,
      expected === 1
        ? ["Invalid date range: from_date must not be after until_date."]
        : [],
    );
  }
});

void test("strict scalar validation and unknown names visibly block instead of treating typos as absence", () => {
  for (const key of [
    "artefact_is_archived",
    "rerun_is_requested",
    "execution_is_latest",
  ]) {
    for (const value of ["", "null", "0", "yes", "true,false", " false "])
      assert.ok(
        parse(new URLSearchParams([[key, value]])).problems.length,
        `${key}=${value}`,
      );
    assert.ok(parse(`${key}=true&${key}=false`).problems.length);
    assert.deepEqual(parse(`${key}=FALSE`).problems, []);
  }
  for (const key of [
    "unknown",
    "test_execution_statuses",
    "reviewers",
    "fromDate",
  ])
    assert.ok(parse(`${key}=bad&artefacts=valid`).problems.length, key);
});

void test("shared operations preserve deep draft isolation and distinguish all active typed values", () => {
  const query = parse(
    new URLSearchParams([
      ["artefact_stages", ""],
      ["artefact_is_archived", "false"],
      ["issues", "1,2"],
      ["execution_metadata", `${pair("a", "one")},${pair("a", "two")}`],
    ]),
  );
  const copy = model.cloneFilters(query.filters);
  assert.deepEqual(copy, query.filters);
  copy.artefact_stages.push("candidate");
  assert.ok(Array.isArray(copy.issues));
  copy.issues.push(3);
  copy.execution_metadata[0].values.push("three");
  assert.deepEqual(query.filters.artefact_stages, [""]);
  assert.deepEqual(query.filters.issues, [1, 2]);
  assert.deepEqual(query.filters.execution_metadata[0].values, ["one", "two"]);
  assert.equal(model.filtersEqual(copy, query.filters), false);
  const reordered = model.cloneFilters(query.filters);
  assert.ok(Array.isArray(reordered.issues));
  reordered.issues.reverse();
  reordered.execution_metadata[0].values.reverse();
  assert.equal(model.filtersEqual(reordered, query.filters), true);
  for (const key of [
    "artefact_is_archived",
    "artefact_stages",
    "issues",
    "execution_metadata",
  ]) {
    const cleared = model.clearFilter(
      query.filters,
      /** @type {import('../src/lib/testResultsFilters').SearchFilter} */ (key),
    );
    assert.equal(model.filtersEqual(cleared, query.filters), false, key);
    assert.equal(
      model.filterIsActive(
        /** @type {import('../src/lib/testResultsFilters').SearchFilter} */ (
          key
        ),
        cleared,
      ),
      false,
    );
  }
});

void test("compact-editor URL replacement retains every URL-only constraint, including invalid and unknown conditions", () => {
  const source = new URLSearchParams([
    ["artefacts", "old"],
    ["artefact_stages", ""],
    ["artefact_is_archived", "false"],
    ["issues", "1,bad"],
    ["assignee_ids", "2"],
    ["execution_metadata", "invalid"],
    ["from_date", "invalid"],
    ["unsupported", "blocked"],
    ["offset", "20"],
    ["limit", "2"],
    ["view", "presentation"],
  ]);
  const draft = parse(source).filters;
  draft.artefacts = ["new", "second"];
  const edited = model.editedSearchParams(draft, source);
  for (const key of [
    "artefact_stages",
    "artefact_is_archived",
    "issues",
    "assignee_ids",
    "execution_metadata",
    "from_date",
    "unsupported",
  ])
    assert.deepEqual(edited.getAll(key), source.getAll(key), key);
  assert.deepEqual(edited.getAll("artefacts"), ["new", "second"]);
  assert.equal(edited.has("offset"), false);
  assert.equal(edited.has("view"), false);
  assert.equal(edited.get("limit"), "50");
  assert.ok(parse(edited).problems.length);
  assert.equal(
    model.editedSearchParams(
      model.emptyFilters(),
      new URLSearchParams("artefacts=old&view=anything"),
    ).size,
    0,
  );
  const identity = model.searchQueryString(source);
  source.set("view", "different");
  assert.equal(model.searchQueryString(source), identity);
  source.set("issues", "1");
  assert.notEqual(model.searchQueryString(source), identity);
});
