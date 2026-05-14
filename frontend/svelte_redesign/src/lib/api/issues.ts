// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { apiFetch } from "./client.js";
import type { Issue, IssueWithContext } from "$lib/types/issue.js";
import type { AttachmentRule } from "$lib/types/attachment-rule.js";

export function getIssues(
  params: Record<string, string>,
  fetchFn: typeof fetch = fetch,
): Promise<Issue[]> {
  const qs = new URLSearchParams(params).toString();
  const path = qs ? `/v1/issues?${qs}` : "/v1/issues";
  return apiFetch<Issue[]>(path, {}, fetchFn);
}

export function createIssue(
  data: Record<string, unknown>,
  fetchFn: typeof fetch = fetch,
): Promise<Issue> {
  return apiFetch<Issue>("/v1/issues", {
    method: "PUT",
    body: JSON.stringify(data),
  }, fetchFn);
}

export function getIssue(
  id: number,
  fetchFn: typeof fetch = fetch,
): Promise<IssueWithContext> {
  return apiFetch<IssueWithContext>(`/v1/issues/${id}`, {}, fetchFn);
}

export function attachIssue(
  id: number,
  data: Record<string, unknown>,
  fetchFn: typeof fetch = fetch,
): Promise<Issue> {
  return apiFetch<Issue>(`/v1/issues/${id}/attach`, {
    method: "POST",
    body: JSON.stringify(data),
  }, fetchFn);
}

export function detachIssue(
  id: number,
  data: Record<string, unknown>,
  fetchFn: typeof fetch = fetch,
): Promise<Issue> {
  return apiFetch<Issue>(`/v1/issues/${id}/detach`, {
    method: "POST",
    body: JSON.stringify(data),
  }, fetchFn);
}

export function patchIssue(
  id: number,
  patch: Record<string, unknown>,
  fetchFn: typeof fetch = fetch,
): Promise<IssueWithContext> {
  return apiFetch<IssueWithContext>(`/v1/issues/${id}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  }, fetchFn);
}

export function createAttachmentRule(
  issueId: number,
  data: Record<string, unknown>,
  fetchFn: typeof fetch = fetch,
): Promise<AttachmentRule> {
  return apiFetch<AttachmentRule>(`/v1/issues/${issueId}/attachment-rules`, {
    method: "POST",
    body: JSON.stringify(data),
  }, fetchFn);
}

export function deleteAttachmentRule(
  issueId: number,
  ruleId: number,
  fetchFn: typeof fetch = fetch,
): Promise<void> {
  return apiFetch<void>(`/v1/issues/${issueId}/attachment-rules/${ruleId}`, {
    method: "DELETE",
  }, fetchFn);
}

export function patchAttachmentRule(
  issueId: number,
  ruleId: number,
  patch: Record<string, unknown>,
  fetchFn: typeof fetch = fetch,
): Promise<void> {
  return apiFetch<void>(`/v1/issues/${issueId}/attachment-rules/${ruleId}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  }, fetchFn);
}
