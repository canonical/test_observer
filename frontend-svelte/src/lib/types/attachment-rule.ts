// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { Issue } from "./issue.js";
import type { TestResultStatus } from "./test-result.js";
import type { ExecutionMetadata } from "./test-execution.js";

export interface AttachmentRule {
  id: number;
  enabled: boolean;
  families: string[];
  environmentNames: string[];
  testCaseNames: string[];
  templateIds: string[];
  executionMetadata: ExecutionMetadata;
  testResultStatuses: TestResultStatus[];
}

export interface AttachmentRuleFilters {
  families: string[];
  environmentNames: string[];
  testCaseNames: string[];
  templateIds: string[];
  executionMetadata: ExecutionMetadata;
  testResultStatuses: TestResultStatus[];
}

export interface IssueAttachment {
  issue: Issue;
  attachmentRule?: AttachmentRule;
}
