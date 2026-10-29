// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { FILTER_DEFINITIONS, type SearchFilter } from "$lib/testResultsFilters";
import type { AttachmentRuleFilters } from "$lib/testResultsBulk";
import { positiveId } from "$lib/testResultsPredicate";

export function ruleCriteria(filters: AttachmentRuleFilters) {
  return Object.entries(filters).map(([key, value]) => ({
    label:
      FILTER_DEFINITIONS[
        (key === "environment_names"
          ? "environments"
          : key === "test_case_names"
            ? "test_cases"
            : key) as SearchFilter
      ].label,
    // Keep JSON quoting so the empty stage and literal metadata are readable.
    value: JSON.stringify(value),
  }));
}

/** The minimal POST response omits issue_id. Verify membership separately via
 * GET /issues/{chosenId} before claiming success, not a guessed response field. */
export function createdRule(body: unknown): number {
  if (
    !body ||
    typeof body !== "object" ||
    !("id" in body) ||
    !positiveId(body.id) ||
    !("enabled" in body) ||
    body.enabled !== true
  )
    throw new Error(
      "The server did not confirm a valid enabled attachment rule.",
    );
  return body.id;
}

export function confirmRuleIssue(
  body: unknown,
  issueId: number,
  ruleId: number,
) {
  if (
    !body ||
    typeof body !== "object" ||
    !("id" in body) ||
    body.id !== issueId ||
    !("attachment_rules" in body) ||
    !Array.isArray(body.attachment_rules) ||
    !body.attachment_rules.some(
      (rule: unknown) =>
        rule !== null &&
        typeof rule === "object" &&
        "id" in rule &&
        rule.id === ruleId &&
        "enabled" in rule &&
        rule.enabled === true,
    )
  )
    throw new Error(
      "Could not confirm the enabled rule belongs to the chosen issue. Inspect the issue before creating another rule.",
    );
}
