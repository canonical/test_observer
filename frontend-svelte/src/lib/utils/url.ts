// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { base } from "$app/paths";

export function artefactPath(
  family: string,
  artefactId: number,
  opts?: { testExecutionId?: number; testResultId?: number },
): string {
  const path = `${base}/${family}/${artefactId}`;
  const params = new URLSearchParams();
  if (opts?.testExecutionId) params.set("testExecutionId", String(opts.testExecutionId));
  if (opts?.testResultId) params.set("testResultId", String(opts.testResultId));
  return params.size > 0 ? `${path}?${params}` : path;
}

export function issuePath(issueId: number, attachmentRuleId?: number): string {
  const path = `${base}/issues/${issueId}`;
  if (attachmentRuleId) return `${path}?attachmentRule=${attachmentRuleId}`;
  return path;
}

export function familyPath(family: string): string {
  return `${base}/${family}`;
}
