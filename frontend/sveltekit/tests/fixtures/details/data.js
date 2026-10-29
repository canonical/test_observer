// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

// Synthetic read-only examples, never sent to an API. No family-specific logic.
/** @type {import('../../../src/lib/types').Family[]} */
export const families = [
  {
    name: "configured-routes",
    api_name: "example",
    stages: [],
    columns: [],
    filters: [],
  },
];
export const literal =
  '<script>globalThis.detailsInjected=true</script><img src=x onerror="alert(1)"> & 🐧 Ω 二 :, /';
const path =
  "workspace/long-component-name/integration/scenarios/representative-system/";
const stack = `Traceback (most recent call last):\n  File "${path}check_relations.py", line 128, in verify\n    assert observed == expected\nAssertionError: relation [database:client, queue:peer] → unavailable 🐧`;

/** @type {import('../../../src/lib/testResultsSearch').SearchResultDetails} */
export const largeResult = {
  test_result: {
    id: 9001,
    name: `${path.repeat(3)}test_multiple_relations_recover_after_interruption[primary-secondary-Ω]`,
    category: "integration / recovery / generic representative workload",
    template_id: `template:${path.repeat(4)}case[parameter=long-alternative,unicode=二]`,
    status: "FAILED",
    io_log: `${literal}\n  leading indentation\nNAME                     STATUS       DURATION\ncomponent-one            waiting      12.25s\ncomponent-two            active       0.12s\n\n${Array.from({ length: 800 }, (_, i) => `  ${String(i).padStart(4, "0")} | relation:client → server | result: retry ${i % 7}\n${i % 25 === 0 ? `${stack}\n${"long-unbroken-token_".repeat(50)}\n` : ""}`).join("")}\nEND OF COMPLETE REPRESENTATIVE LOG 🐧`,
    issues: [
      {
        issue: {
          id: 101,
          source: "github",
          project: "example/project",
          key: "EX-101",
          title: `Literal issue ${literal}`,
          status: "open",
        },
      },
      {
        issue: {
          id: 102,
          source: "jira",
          project: "another/project",
          key: "EX-102",
          title: "Relation timeout, secondary recovery — 二",
          status: "closed",
        },
      },
    ],
  },
  artefact: {
    id: 42,
    name: `${path}representative-artefact`,
    version: "2026.10.20+build.123456789",
    track: "candidate/recovery-testing",
    family: "example",
  },
  artefact_build: { architecture: "architecture-example" },
  test_execution: {
    id: 7,
    status: "FAILED",
    environment: {
      name: `${path.repeat(2)}long-environment-name-with-many-connected-services`,
    },
    test_plan: `${path.repeat(3)}test-plan[recovery:client-server,secondary]`,
    created_at: "2026-02-03T12:34:56+05:30",
    execution_metadata: {
      ...Object.fromEntries(
        Array.from({ length: 36 }, (_, i) => [
          `pipeline:workflow_hash:${String(35 - i).padStart(2, "0")}:${"long_category_segment_".repeat(3)}`,
          [
            `alternative-z:${i}:colon,comma,space Ω`,
            `alternative-a:${i}:${"unbroken_value_".repeat(25)}`,
          ],
        ]),
      ),
      "pipeline:workflow_hash": [
        "fedcba9876543210".repeat(10),
        "0123456789abcdef".repeat(10),
      ],
      "failure:charm:component:status": [
        stack,
        literal,
        ...Array.from(
          { length: 24 },
          (_, i) =>
            `alternative:${23 - i} relation:client/peer → service, status: waiting; message: ${path}timeout`,
        ),
      ],
      "relations:messages:stacktrace": [
        stack.repeat(4),
        "  preserved leading spaces\n    second indented line\n\nlast line",
      ],
      "empty:alternatives": [],
      "ζ Unicode 🐧 : , <literal>": ["二", "一", literal],
    },
  },
};

/** @type {import('../../../src/lib/testResultsSearch').SearchResultDetails} */
export const emptyResult = {
  ...largeResult,
  test_result: {
    ...largeResult.test_result,
    id: 9002,
    name: "Short empty comparison",
    category: "",
    template_id: "",
    issues: [],
    io_log: "",
  },
  artefact: {
    ...largeResult.artefact,
    name: "Short artefact",
    version: "",
    track: "",
    family: "unconfigured",
  },
  test_execution: {
    ...largeResult.test_execution,
    test_plan: "",
    created_at: "",
    environment: { name: "" },
    execution_metadata: {},
  },
};
