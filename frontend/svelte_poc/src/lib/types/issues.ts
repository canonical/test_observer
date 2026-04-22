export type IssueSource = 'github' | 'jira' | 'launchpad';
export type IssueStatus = 'open' | 'closed' | 'unknown';
export const ISSUE_SOURCES: IssueSource[] = ['github', 'jira', 'launchpad'];
export const ISSUE_STATUSES: IssueStatus[] = ['open', 'closed', 'unknown'];
export const DEFAULT_STATUSES: IssueStatus[] = ['open', 'unknown'];

export interface AttachmentRule {
  id: number;
  enabled: boolean;
  families: string[];
  environment_names: string[];
  test_case_names: string[];
  template_ids: string[];
  test_result_statuses: string[];
  execution_metadata: Record<string, string[]>;
}

export interface IssueDetail {
  id: number;
  source: IssueSource;
  project: string;
  key: string;
  title: string;
  status: IssueStatus;
  url: string;
  labels: string[] | null;
  attachment_rules: AttachmentRule[];
  auto_rerun_enabled: boolean;
  test_executions_count: number;
}

export interface IssueListFilters {
  source: string[];
  status: string[];
  family: string[];
  project: string;
  q: string;
}

export function emptyIssueFilters(): IssueListFilters {
  return { source: [], status: [...DEFAULT_STATUSES], family: [], project: '', q: '' };
}

export function issueDisplayKey(issue: { source: string; project: string; key: string }): string {
  if (issue.source === 'jira') return `${issue.project}-${issue.key}`;
  return `#${issue.key}`;
}
