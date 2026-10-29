// Copyright 2026 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { FetchError, silentApi } from "$lib/api/client";
import type {
  AttachmentRule,
  Issue,
  IssueDetail,
  IssueListResponse,
} from "$lib/types/issues";

export async function listIssues(
  params: URLSearchParams,
): Promise<IssueListResponse> {
  const query = params.toString();
  const response = await silentApi<IssueListResponse>(
    `issues${query ? `?${query}` : ""}`,
  );
  if (
    !response ||
    !Array.isArray(response.issues) ||
    !Number.isSafeInteger(response.count) ||
    !Number.isSafeInteger(response.limit) ||
    !Number.isSafeInteger(response.offset)
  ) {
    throw new Error("The issues API returned an invalid list response.");
  }
  return response;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isStringArray(value: unknown): value is string[] {
  return (
    Array.isArray(value) && value.every((item) => typeof item === "string")
  );
}

function isExecutionMetadata(
  value: unknown,
): value is Record<string, string[]> {
  return (
    isRecord(value) &&
    Object.values(value).every((items) => isStringArray(items))
  );
}

const RULE_FAMILIES = new Set<string>([
  "snap",
  "deb",
  "charm",
  "image",
  "solution",
]);

const RULE_ARRAY_FIELDS = [
  "families",
  "artefacts",
  "artefact_versions",
  "artefact_stages",
  "artefact_tracks",
  "environment_names",
  "test_plans",
  "test_case_names",
  "template_ids",
  "test_result_statuses",
] as const;

function isAttachmentRule(value: unknown): value is AttachmentRule {
  if (
    !isRecord(value) ||
    typeof value.id !== "number" ||
    !Number.isSafeInteger(value.id) ||
    value.id < 1 ||
    typeof value.enabled !== "boolean" ||
    !isExecutionMetadata(value.execution_metadata)
  )
    return false;
  if (!RULE_ARRAY_FIELDS.every((field) => isStringArray(value[field])))
    return false;
  const statuses = value.test_result_statuses;
  const families = value.families;
  return (
    isStringArray(statuses) &&
    statuses.every(
      (status) =>
        status === "PASSED" || status === "FAILED" || status === "SKIPPED",
    ) &&
    isStringArray(families) &&
    families.every((family) => RULE_FAMILIES.has(family))
  );
}

function isIssueDetail(value: unknown): value is IssueDetail {
  return (
    isRecord(value) &&
    typeof value.id === "number" &&
    Number.isSafeInteger(value.id) &&
    value.id > 0 &&
    (value.source === "github" ||
      value.source === "jira" ||
      value.source === "launchpad") &&
    typeof value.project === "string" &&
    typeof value.key === "string" &&
    typeof value.title === "string" &&
    (value.status === "unknown" ||
      value.status === "closed" ||
      value.status === "open") &&
    typeof value.url === "string" &&
    (value.labels === null || isStringArray(value.labels)) &&
    typeof value.auto_rerun_enabled === "boolean" &&
    Array.isArray(value.attachment_rules) &&
    value.attachment_rules.every(isAttachmentRule)
  );
}

function assertIssueDetail(value: unknown): IssueDetail {
  if (!isIssueDetail(value))
    throw new Error(
      "The issues API returned an invalid issue detail response.",
    );
  return value;
}

export async function getIssue(id: number): Promise<IssueDetail> {
  if (!Number.isSafeInteger(id) || id <= 0)
    throw new Error("Invalid issue ID.");
  return assertIssueDetail(await silentApi<unknown>(`issues/${id}`));
}

export async function createIssue(url: string): Promise<Issue> {
  const response = await silentApi<Issue>("issues", {
    method: "PUT",
    body: JSON.stringify({ url }),
  });
  if (!response || !Number.isSafeInteger(response.id)) {
    throw new Error("The issues API returned an invalid issue.");
  }
  return response;
}

export async function setAttachmentRuleEnabled(
  issueId: number,
  ruleId: number,
  enabled: boolean,
): Promise<AttachmentRule> {
  const response = await silentApi<unknown>(
    `issues/${issueId}/attachment-rules/${ruleId}`,
    { method: "PATCH", body: JSON.stringify({ enabled }) },
  );
  const rule = response;
  if (!isAttachmentRule(rule) || rule.id !== ruleId || rule.enabled !== enabled)
    throw new Error(
      "The issues API did not confirm the attachment rule update.",
    );
  return rule;
}

export async function deleteAttachmentRule(
  issueId: number,
  ruleId: number,
): Promise<void> {
  await silentApi<null>(`issues/${issueId}/attachment-rules/${ruleId}`, {
    method: "DELETE",
  });
}

export async function issueErrorMessage(error: unknown): Promise<string> {
  if (error instanceof FetchError) {
    try {
      const body: unknown = await error.res.json();
      if (
        typeof body === "object" &&
        body !== null &&
        "detail" in body &&
        typeof body.detail === "string"
      ) {
        return body.detail;
      }
    } catch {
      // Fall through to a status-based message for non-JSON error responses.
    }
    return `Request failed (${error.status}).`;
  }
  return error instanceof Error ? error.message : "Unable to load issues.";
}
