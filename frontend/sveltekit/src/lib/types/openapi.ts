// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

/*
 * These types are intentionally kept aligned with backend/schemata/openapi.json.
 * Do not add page-specific or build-scoped fields here; derive a new type in
 * a separate type module when necessary.
 */

export type TestExecutionStatus =
  | "NOT_STARTED"
  | "NOT_TESTED"
  | "IN_PROGRESS"
  | "ENDED_PREMATURELY"
  | "FAILED"
  | "PASSED";

export type ExecutionMetadata = Record<string, string[]>;

export type FamilyName = "snap" | "deb" | "charm" | "image" | "solution";

export type TestResultStatus = "PASSED" | "FAILED" | "SKIPPED";

export interface TestResultSearchFilters {
  families?: FamilyName[];
  artefacts?: string[];
  artefact_is_archived?: boolean | null;
  environments?: string[];
  test_cases?: string[];
  template_ids?: string[];
  execution_metadata?: ExecutionMetadata;
  issues?: number[] | "any" | "none";
  test_result_statuses?: TestResultStatus[];
  test_execution_statuses?: TestExecutionStatus[];
  reviewer_ids?: number[] | "any" | "none";
  assignee_ids?: number[] | "any" | "none" | null;
  rerun_is_requested?: boolean | null;
  execution_is_latest?: boolean | null;
  from_date?: string | null;
  until_date?: string | null;
  offset?: number | null;
  limit?: number | null;
}

export interface RerunRequest {
  test_execution_ids?: number[];
  test_results_filters?: TestResultSearchFilters | null;
}

export interface EnvironmentResponse {
  id: number;
  name: string;
  architecture: string;
}

export interface TestExecutionRelevantLinkResponse {
  id: number;
  label: string;
  url: string;
}

export interface TestExecutionResponse {
  id: number;
  ci_link: string | null;
  c3_link: string | null;
  status: TestExecutionStatus;
  environment: EnvironmentResponse;
  is_rerun_requested: boolean;
  test_plan: string;
  relevant_links?: TestExecutionRelevantLinkResponse[];
  created_at: string;
  execution_metadata: ExecutionMetadata;
  is_triaged: boolean;
}

export interface MinimalIssueTestResultAttachmentRuleResponse {
  id: number;
  enabled: boolean;
  families: FamilyName[];
  environment_names: string[];
  test_case_names: string[];
  template_ids: string[];
  test_result_statuses: TestResultStatus[];
  execution_metadata: ExecutionMetadata;
}

export interface MinimalIssueResponse {
  id: number;
  source: "github" | "jira" | "launchpad";
  project: string;
  key: string;
  title: string;
  status: "unknown" | "closed" | "open";
  url: string;
  labels?: string[] | null;
  test_executions_count?: number;
}

export interface ArtefactResponse {
  id: number;
  name: string;
  version: string;
  track: string;
  store: string;
  branch: string;
  series: string;
  repo: string;
  source: string;
  os: string;
  release: string;
  owner: string;
  sha256: string;
  image_url: string;
  stage: string;
  family: string;
  status: "APPROVED" | "MARKED_AS_FAILED" | "UNDECIDED";
  comment: string;
  archived: boolean;
  reviewers: ReviewerResponse[];
  due_date: string | null;
  created_at: string;
  bug_link: string;
  jira_issue: string | null;
  risk: string;
  all_environment_reviews_count: number;
  completed_environment_reviews_count: number;
  bundled_builds?: ArtefactBuildMinimalResponse[];
  assignee: ReviewerResponse | null;
}

export interface PendingRerunResponse {
  test_execution_id: number;
  ci_link: string | null;
  family: FamilyName;
  test_execution: TestExecutionResponse;
  artefact: ArtefactResponse;
  artefact_build: ArtefactBuildMinimalResponse;
}

export interface ReviewerResponse {
  id: number;
  email: string;
  launchpad_email: string;
  name: string;
  launchpad_handle?: string | null;
}

export interface ArtefactBuildMinimalResponse {
  id: number;
  architecture: string;
  revision: number | null;
}

export interface ArtefactMinimalResponse {
  id: number;
  name: string;
  version: string;
  family: string;
}

export type ArtefactBuildEnvironmentReviewDecision =
  | "REJECTED"
  | "APPROVED_INCONSISTENT_TEST"
  | "APPROVED_UNSTABLE_PHYSICAL_INFRA"
  | "APPROVED_CUSTOMER_PREREQUISITE_FAIL"
  | "APPROVED_FAULTY_HARDWARE"
  | "APPROVED_ALL_TESTS_PASS";

export interface ArtefactBuildEnvironmentReviewResponse {
  id: number;
  review_decision: ArtefactBuildEnvironmentReviewDecision[];
  review_comment: string;
  environment: EnvironmentResponse;
  artefact_build: ArtefactBuildMinimalResponse;
  reviewers: ReviewerResponse[];
}

export interface ArtefactBuildResponse {
  id: number;
  architecture: string;
  revision: number | null;
  test_executions: TestExecutionResponse[];
  bundled_in: ArtefactMinimalResponse[];
}

export interface ArtefactVersionResponse {
  artefact_id: number;
  version: string;
}

export interface EnvironmentReportedIssueResponse {
  id: number;
  environment_name: string;
  description: string;
  url: string | null;
  is_confirmed: boolean;
  created_at: string;
  updated_at: string;
}

export interface TestReportedIssueResponse {
  id: number;
  template_id: string;
  case_name: string;
  description: string;
  url: string;
  created_at: string;
  updated_at: string;
}
