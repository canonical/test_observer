export interface ArtefactBuild {
  id: number;
  architecture: string;
  revision: number | null;
  test_executions: TestExecution[];
}

export interface TestExecution {
  id: number;
  ci_link: string | null;
  c3_link: string | null;
  status: TestExecutionStatus;
  environment: Environment;
  is_rerun_requested: boolean;
  artefact_build_id: number;
  test_plan: string;
  relevant_links: TestExecutionRelevantLink[];
  created_at: string;
  execution_metadata: Record<string, string[]>;
  is_triaged: boolean;
}

export type TestExecutionStatus =
  | 'NOT_STARTED'
  | 'NOT_TESTED'
  | 'IN_PROGRESS'
  | 'ENDED_PREMATURELY'
  | 'FAILED'
  | 'PASSED';

export interface TestExecutionRelevantLink {
  id: number;
  label: string;
  url: string;
}

export interface Environment {
  id: number;
  name: string;
  architecture: string;
}

export interface EnvironmentReview {
  id: number;
  artefact_build: { id: number; architecture: string; revision: number | null };
  environment: Environment;
  review_comment: string;
  review_decision: string[];
}

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

export type TestResultStatus = 'PASSED' | 'FAILED' | 'SKIPPED';

export interface PreviousTestResult {
  status: TestResultStatus;
  version: string;
  artefact_id: number;
  test_execution_id: number;
  test_result_id: number;
}

export interface IssueAttachment {
  issue: Issue;
  attachment_rule: number | null;
}

export interface Issue {
  id: number;
  source: 'github' | 'jira' | 'launchpad';
  project: string;
  key: string;
  title: string;
  status: 'unknown' | 'closed' | 'open';
  url: string;
}

export interface TestEvent {
  event_name: string;
  timestamp: string;
  detail: string;
}

export interface ArtefactVersion {
  artefact_id: number;
  version: string;
}

export interface EnvironmentIssue {
  id: number;
  environment_name: string;
  description: string;
  url: string | null;
  is_confirmed: boolean;
}

export interface TestIssue {
  id: number;
  template_id: string;
  case_name: string;
  description: string;
  url: string;
}

export interface RerunRequest {
  test_execution_id: number;
  ci_link: string;
}

// Derived client-side types
export interface EnrichedTestExecution {
  testExecution: TestExecution;
  environmentReview: EnvironmentReview;
}

export interface ArtefactEnvironment {
  review: EnvironmentReview;
  runsDescending: TestExecution[];
  name: string;
  architecture: string;
}
