import type { Artefact } from '$lib/types';

// --- Test Result Status ---
export const TEST_RESULT_STATUSES = ['PASSED', 'FAILED', 'SKIPPED'] as const;
export type TestResultStatus = (typeof TEST_RESULT_STATUSES)[number];

// --- Issue types used in test results ---
export interface MinimalIssue {
  id: number;
  source: string;
  project: string;
  key: string;
  title: string;
  status: string;
  url: string;
  labels: string[] | null;
  test_executions_count?: number;
}

export interface IssueAttachment {
  issue: MinimalIssue;
  attachment_rule: {
    id: number;
    enabled: boolean;
    families: string[];
    environment_names: string[];
    test_case_names: string[];
    template_ids: string[];
    test_result_statuses: string[];
    execution_metadata: Record<string, string[]>;
  } | null;
}

export interface PreviousTestResult {
  status: TestResultStatus;
  created_at: string;
}

// --- Core response shapes from backend ---
export interface TestResultResponse {
  id: number;
  name: string;
  created_at: string;
  category: string;
  template_id: string;
  status: TestResultStatus;
  comment: string;
  io_log: string;
  previous_results: PreviousTestResult[];
  issues: IssueAttachment[];
}

export interface EnvironmentResponse {
  id: number;
  name: string;
  architecture: string;
}

export interface ExecutionMetadata {
  [category: string]: string[];
}

export interface TestExecutionResponse {
  id: number;
  ci_link: string | null;
  c3_link: string | null;
  relevant_links: { id: number; label: string; url: string }[];
  environment: EnvironmentResponse;
  status: string;
  test_plan: string;
  created_at: string;
  execution_metadata: ExecutionMetadata;
  is_rerun_requested: boolean;
  is_triaged: boolean;
}

export interface ArtefactBuildMinimalResponse {
  id: number;
  architecture: string;
  revision: number | null;
}

export interface TestResultWithContext {
  test_result: TestResultResponse;
  test_execution: TestExecutionResponse;
  artefact: Artefact;
  artefact_build: ArtefactBuildMinimalResponse;
}

export interface TestResultSearchResponse {
  count: number;
  test_results: TestResultWithContext[];
}

// --- Filter types ---
export type IssueFilterMode = 'any_value' | 'has_any' | 'has_none' | 'specific';
export type AssigneeFilterMode = 'any_value' | 'has_any' | 'has_none' | 'specific';

export interface TestResultFilters {
  families: string[];
  statuses: string[];
  issueMode: IssueFilterMode;
  issueIds: number[];
  assigneeMode: AssigneeFilterMode;
  assigneeIds: number[];
  artefacts: string[];
  archived: 'any' | 'yes' | 'no';
  rerunRequested: 'any' | 'yes' | 'no';
  executionIsLatest: 'any' | 'yes' | 'no';
  environments: string[];
  testCases: string[];
  metadata: string[]; // base64-encoded "category:value" pairs
  fromDate: string;
  untilDate: string;
}

export function emptyFilters(): TestResultFilters {
  return {
    families: [],
    statuses: [],
    issueMode: 'any_value',
    issueIds: [],
    assigneeMode: 'any_value',
    assigneeIds: [],
    artefacts: [],
    archived: 'any',
    rerunRequested: 'any',
    executionIsLatest: 'any',
    environments: [],
    testCases: [],
    metadata: [],
    fromDate: '',
    untilDate: '',
  };
}

// --- API search response types ---
export interface ArtefactSearchResponse {
  artefacts: string[];
}

export interface TestCaseInfo {
  test_case: string;
  template_id: string | null;
}

export interface TestCasesResponse {
  test_cases: TestCaseInfo[];
}

export interface EnvironmentsSearchResponse {
  environments: string[];
}

export interface ExecutionMetadataResponse {
  execution_metadata: Record<string, string[]>;
}

export interface UserInfo {
  id: number;
  email: string;
  name: string;
  launchpad_handle: string | null;
}

export interface UsersResponse {
  users: UserInfo[];
  count: number;
}

export interface IssuesGetResponse {
  issues: MinimalIssue[];
}
