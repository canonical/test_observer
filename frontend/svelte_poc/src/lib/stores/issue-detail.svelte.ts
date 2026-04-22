import { api } from '$lib/api/client';
import type { IssueDetail, AttachmentRule } from '$lib/types/issues';
import type {
  TestResultWithContext,
  TestResultSearchResponse,
  TestResultFilters,
  ArtefactSearchResponse,
  EnvironmentsSearchResponse,
  TestCasesResponse,
} from '$lib/types/test-results';
import { emptyFilters } from '$lib/types/test-results';
import { serializeFilters } from '$lib/stores/test-results.svelte';

const PAGE_SIZE = 100;

export class IssueDetailStore {
  issue = $state<IssueDetail | null>(null);
  issueLoading = $state(false);
  issueError = $state<string | null>(null);

  results = $state<TestResultWithContext[]>([]);
  totalCount = $state(0);
  resultsLoading = $state(false);
  resultsLoadingMore = $state(false);

  appliedFilters = $state<TestResultFilters>(emptyFilters());
  workingFilters = $state<TestResultFilters>(emptyFilters());

  private _issueId = 0;

  filtersModified = $derived(
    JSON.stringify(this.workingFilters) !== JSON.stringify(this.appliedFilters),
  );

  hasMore = $derived(this.results.length < this.totalCount);

  hasFilters = $derived.by(() => {
    const f = this.appliedFilters;
    return (
      f.families.length > 0 ||
      f.statuses.length > 0 ||
      f.artefacts.length > 0 ||
      f.environments.length > 0 ||
      f.testCases.length > 0 ||
      f.fromDate !== '' ||
      f.untilDate !== ''
    );
  });

  async loadIssue(id: number) {
    this._issueId = id;
    this.issueLoading = true;
    this.issueError = null;
    const data = await api<IssueDetail>(`/issues/${id}`);
    if (data) {
      this.issue = data;
    } else {
      this.issue = null;
      this.issueError = 'Failed to load issue';
    }
    this.issueLoading = false;
  }

  async searchResults(filters: TestResultFilters) {
    this.appliedFilters = JSON.parse(JSON.stringify(filters));
    this.workingFilters = JSON.parse(JSON.stringify(filters));
    this.resultsLoading = true;

    const params = serializeFilters(filters);
    params.set('issues', String(this._issueId));
    params.set('limit', String(PAGE_SIZE));
    params.set('offset', '0');

    const data = await api<TestResultSearchResponse>(`/test-results?${params}`);
    if (data) {
      this.results = data.test_results;
      this.totalCount = data.count;
    } else {
      this.results = [];
      this.totalCount = 0;
    }
    this.resultsLoading = false;
  }

  async loadMoreResults() {
    if (!this.hasMore || this.resultsLoadingMore) return;
    this.resultsLoadingMore = true;

    const params = serializeFilters(this.appliedFilters);
    params.set('issues', String(this._issueId));
    params.set('limit', String(PAGE_SIZE));
    params.set('offset', String(this.results.length));

    const data = await api<TestResultSearchResponse>(`/test-results?${params}`);
    if (data) {
      this.results = [...this.results, ...data.test_results];
      this.totalCount = data.count;
    }
    this.resultsLoadingMore = false;
  }

  async enableRule(ruleId: number) {
    await api(`/issues/${this._issueId}/attachment-rules/${ruleId}`, {
      method: 'PATCH',
      body: JSON.stringify({ enabled: true }),
    });
    await this.loadIssue(this._issueId);
  }

  async disableRule(ruleId: number) {
    await api(`/issues/${this._issueId}/attachment-rules/${ruleId}`, {
      method: 'PATCH',
      body: JSON.stringify({ enabled: false }),
    });
    await this.loadIssue(this._issueId);
  }

  async deleteRule(ruleId: number) {
    await api(`/issues/${this._issueId}/attachment-rules/${ruleId}`, {
      method: 'DELETE',
    });
    await this.loadIssue(this._issueId);
  }

  async setAutoRerun(issueId: number, enabled: boolean): Promise<void> {
    const result = await api<IssueDetail>(`/issues/${issueId}`, {
      method: 'PATCH',
      body: JSON.stringify({ auto_rerun_enabled: enabled }),
    });
    if (result) {
      this.issue = result;
    } else {
      throw new Error('Failed to update auto-rerun setting');
    }
  }

  async createReruns(filters: TestResultFilters) {
    const params = serializeFilters(filters);
    params.set('issues', String(this._issueId));
    await api('/test-executions/reruns?silent=true', {
      method: 'POST',
      body: JSON.stringify({ test_results_filters: paramsToApiBody(params) }),
    });
  }

  async deleteReruns(filters: TestResultFilters) {
    const params = serializeFilters(filters);
    params.set('issues', String(this._issueId));
    await api('/test-executions/reruns', {
      method: 'DELETE',
      body: JSON.stringify({ test_results_filters: paramsToApiBody(params) }),
    });
  }

  async searchArtefacts(query: string, families: string[]): Promise<string[]> {
    const params = new URLSearchParams();
    params.set('q', query);
    params.set('limit', '20');
    for (const f of families) params.append('families', f);
    const data = await api<ArtefactSearchResponse>(`/artefacts/search?${params}`);
    return data?.artefacts ?? [];
  }

  async searchEnvironments(query: string, families: string[]): Promise<string[]> {
    const params = new URLSearchParams();
    params.set('q', query);
    params.set('limit', '20');
    for (const f of families) params.append('families', f);
    const data = await api<EnvironmentsSearchResponse>(`/environments?${params}`);
    return data?.environments ?? [];
  }

  async searchTestCases(query: string, families: string[]): Promise<string[]> {
    const params = new URLSearchParams();
    params.set('q', query);
    params.set('limit', '20');
    for (const f of families) params.append('families', f);
    const data = await api<TestCasesResponse>(`/test-cases?${params}`);
    return data?.test_cases.map((tc) => tc.test_case) ?? [];
  }
}

function paramsToApiBody(params: URLSearchParams): Record<string, unknown> {
  const body: Record<string, unknown> = {};
  const families = params.getAll('families');
  if (families.length) body.families = families;
  const statuses = params.getAll('test_result_statuses');
  if (statuses.length) body.test_result_statuses = statuses;
  const issues = params.getAll('issues');
  if (issues.length) body.issues = issues.map(Number).filter((n) => !isNaN(n));
  const artefacts = params.getAll('artefacts');
  if (artefacts.length) body.artefacts = artefacts;
  const environments = params.getAll('environments');
  if (environments.length) body.environments = environments;
  const testCases = params.getAll('test_cases');
  if (testCases.length) body.test_cases = testCases;
  if (params.get('from_date')) body.from_date = params.get('from_date');
  if (params.get('until_date')) body.until_date = params.get('until_date');
  return body;
}
