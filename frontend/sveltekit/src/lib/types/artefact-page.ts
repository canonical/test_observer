// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import type {
  ArtefactBuildEnvironmentReviewResponse,
  ArtefactVersionResponse,
  EnvironmentReportedIssueResponse,
  MinimalIssueResponse,
  MinimalIssueTestResultAttachmentRuleResponse,
  RerunRequest,
  TestResultStatus,
  TestExecutionResponse,
} from "./openapi";

export type TestExecution = TestExecutionResponse & {
  artefact_build_id: number;
};

export type { TestResultStatus } from "./openapi";

export type ArtefactVersion = ArtefactVersionResponse;
export type EnvironmentReview = ArtefactBuildEnvironmentReviewResponse;
export type EnvironmentIssue = EnvironmentReportedIssueResponse;

export interface TestResult {
  id: number;
  name: string;
  status: TestResultStatus;
  created_at: string;
  category: string;
  comment: string;
  template_id: string;
  io_log: string;
  previous_results: PreviousTestResult[];
  issues: IssueAttachment[];
}

export interface PreviousTestResult {
  status: TestResultStatus;
  version: string;
  artefact_id: number;
  test_execution_id: number;
  test_result_id: number;
}

export interface IssueAttachment {
  issue: Issue;
  attachment_rule: MinimalIssueTestResultAttachmentRuleResponse | null;
}

export type Issue = MinimalIssueResponse;

export interface TestEvent {
  event_name: string;
  timestamp: string;
  detail: string;
}

export interface EnrichedTestExecution {
  testExecution: TestExecution;
  environmentReview: ArtefactBuildEnvironmentReviewResponse | null;
}

// This store operation always issues an ID-based rerun, while the API also
// accepts filter-based requests. Require IDs in the call-specific body type.
export type RerunExecutionsRequest = Required<
  Pick<RerunRequest, "test_execution_ids">
>;

export interface ArtefactEnvironment {
  key: string;
  review: ArtefactBuildEnvironmentReviewResponse | null;
  runsDescending: TestExecution[];
  name: string;
  architecture: string;
}
