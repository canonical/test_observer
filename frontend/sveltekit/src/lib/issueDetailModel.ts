// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { encodeMetadataPart } from "$lib/testResultsFilters";
import type { AttachmentRule } from "$lib/types/issues";

const RULE_FILTERS = [
  ["families", "Family"],
  ["artefacts", "Artefact"],
  ["artefact_versions", "Artefact Versions"],
  ["artefact_stages", "Artefact Stages"],
  ["artefact_tracks", "Artefact Tracks"],
  ["environment_names", "Environments"],
  ["test_plans", "Test Plans"],
  ["test_case_names", "Test Cases"],
  ["template_ids", "Template IDs"],
  ["test_result_statuses", "Test Result Statuses"],
] as const satisfies readonly [keyof AttachmentRule, string][];

export interface RuleCriterion {
  label: string;
  values: string[];
}

/** Human-readable full filter summary in the same vocabulary as the rule editor. */
export function attachmentRuleCriteria(rule: AttachmentRule): RuleCriterion[] {
  const criteria: RuleCriterion[] = RULE_FILTERS.flatMap(([field, label]) => {
    const values = rule[field];
    return values.length ? [{ label, values: [...values] }] : [];
  });
  const metadata = Object.entries(rule.execution_metadata).flatMap(
    ([category, values]) =>
      values.map(
        (value) => `${JSON.stringify(category)} = ${JSON.stringify(value)}`,
      ),
  );
  if (metadata.length)
    criteria.push({ label: "Execution Metadata", values: metadata });
  return criteria;
}

/** Build the test-results URL with the app's configured base and exact rule filters. */
export function viewRuleFiltersUrl(
  base: string,
  issueId: number,
  rule: AttachmentRule,
): string {
  const cleanBase = base.replace(/\/$/, "");
  const url = new URL(
    `${cleanBase}/test-results`,
    "https://test-observer.invalid",
  );
  url.searchParams.set("issues", String(issueId));
  for (const [field] of RULE_FILTERS) {
    const queryKey =
      field === "environment_names"
        ? "environments"
        : field === "test_case_names"
          ? "test_cases"
          : field;
    for (const value of rule[field]) url.searchParams.append(queryKey, value);
  }
  for (const [category, values] of Object.entries(rule.execution_metadata)) {
    for (const value of values)
      url.searchParams.append(
        "execution_metadata",
        `${encodeMetadataPart(category)}:${encodeMetadataPart(value)}`,
      );
  }
  return `${url.pathname}${url.search}`;
}

export function replaceAttachmentRule(
  rules: AttachmentRule[],
  updated: AttachmentRule,
): AttachmentRule[] {
  return rules.map((rule) => (rule.id === updated.id ? updated : rule));
}

export function removeAttachmentRule(
  rules: AttachmentRule[],
  ruleId: number,
): AttachmentRule[] {
  return rules.filter((rule) => rule.id !== ruleId);
}
