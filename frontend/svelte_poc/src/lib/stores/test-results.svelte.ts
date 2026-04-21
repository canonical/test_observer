import { api } from '$lib/api/client';
import type {
  TestResultWithContext,
  TestResultSearchResponse,
  TestResultFilters,
  ArtefactSearchResponse,
  EnvironmentsSearchResponse,
  TestCasesResponse,
  ExecutionMetadataResponse,
  UsersResponse,
  IssuesGetResponse,
  MinimalIssue,
  UserInfo,
} from '$lib/types/test-results';
import { emptyFilters } from '$lib/types/test-results';

const PAGE_SIZE = 100;

// --- Serialization helpers ---

function boolFilterToParam(val: 'any' | 'yes' | 'no'): string | null {
  if (val === 'yes') return 'true';
  if (val === 'no') return 'false';
  return null;
}

export function serializeFilters(filters: TestResultFilters): URLSearchParams {
  const params = new URLSearchParams();
  for (const f of filters.families) params.append('families', f);
  for (const s of filters.statuses) params.append('test_result_statuses', s);

  if (filters.issueMode === 'has_any') {
    params.append('issues', 'ANY');
  } else if (filters.issueMode === 'has_none') {
    params.append('issues', 'NONE');
  } else if (filters.issueMode === 'specific') {
    for (const id of filters.issueIds) params.append('issues', String(id));
  }

  if (filters.assigneeMode === 'has_any') {
    params.append('assignee_ids', 'ANY');
  } else if (filters.assigneeMode === 'has_none') {
    params.append('assignee_ids', 'NONE');
  } else if (filters.assigneeMode === 'specific') {
    for (const id of filters.assigneeIds) params.append('assignee_ids', String(id));
  }

  for (const a of filters.artefacts) params.append('artefacts', a);

  const archived = boolFilterToParam(filters.archived);
  if (archived !== null) params.set('artefact_is_archived', archived);

  const rerun = boolFilterToParam(filters.rerunRequested);
  if (rerun !== null) params.set('rerun_is_requested', rerun);

  const latest = boolFilterToParam(filters.executionIsLatest);
  if (latest !== null) params.set('execution_is_latest', latest);

  for (const e of filters.environments) params.append('environments', e);
  for (const t of filters.testCases) params.append('test_cases', t);
  for (const m of filters.metadata) params.append('execution_metadata', m);

  if (filters.fromDate) params.set('from_date', filters.fromDate);
  if (filters.untilDate) params.set('until_date', filters.untilDate);

  return params;
}

export function deserializeFilters(params: URLSearchParams): TestResultFilters {
  const filters = emptyFilters();

  filters.families = params.getAll('families');
  filters.statuses = params.getAll('test_result_statuses');

  const issueVals = params.getAll('issues');
  if (issueVals.includes('ANY')) {
    filters.issueMode = 'has_any';
  } else if (issueVals.includes('NONE')) {
    filters.issueMode = 'has_none';
  } else if (issueVals.length > 0) {
    filters.issueMode = 'specific';
    filters.issueIds = issueVals.map(Number).filter((n) => !isNaN(n));
  }

  const assigneeVals = params.getAll('assignee_ids');
  if (assigneeVals.includes('ANY')) {
    filters.assigneeMode = 'has_any';
  } else if (assigneeVals.includes('NONE')) {
    filters.assigneeMode = 'has_none';
  } else if (assigneeVals.length > 0) {
    filters.assigneeMode = 'specific';
    filters.assigneeIds = assigneeVals.map(Number).filter((n) => !isNaN(n));
  }

  filters.artefacts = params.getAll('artefacts');

  const archived = params.get('artefact_is_archived');
  if (archived === 'true') filters.archived = 'yes';
  else if (archived === 'false') filters.archived = 'no';

  const rerun = params.get('rerun_is_requested');
  if (rerun === 'true') filters.rerunRequested = 'yes';
  else if (rerun === 'false') filters.rerunRequested = 'no';

  const latest = params.get('execution_is_latest');
  if (latest === 'true') filters.executionIsLatest = 'yes';
  else if (latest === 'false') filters.executionIsLatest = 'no';

  filters.environments = params.getAll('environments');
  filters.testCases = params.getAll('test_cases');
  filters.metadata = params.getAll('execution_metadata');
  filters.fromDate = params.get('from_date') ?? '';
  filters.untilDate = params.get('until_date') ?? '';

  return filters;
}

function serializeToApiQuery(filters: TestResultFilters, limit: number, offset: number): string {
  const params = serializeFilters(filters);
  params.set('limit', String(limit));
  params.set('offset', String(offset));
  return params.toString();
}

// --- Store ---

export class TestResultsStore {
  results = $state<TestResultWithContext[]>([]);
  totalCount = $state(0);
  loading = $state(false);
  loadingMore = $state(false);
  error = $state<string | null>(null);

  appliedFilters = $state<TestResultFilters>(emptyFilters());
  workingFilters = $state<TestResultFilters>(emptyFilters());

  metadataOptions = $state<Record<string, string[]>>({});
  cachedUsers = $state<UserInfo[]>([]);
  cachedIssues = $state<MinimalIssue[]>([]);

  private _metadataLoaded = false;

  filtersModified = $derived(
    JSON.stringify(this.workingFilters) !== JSON.stringify(this.appliedFilters),
  );

  hasFilters = $derived.by(() => {
    const f = this.appliedFilters;
    return (
      f.families.length > 0 ||
      f.statuses.length > 0 ||
      f.issueMode !== 'any_value' ||
      f.assigneeMode !== 'any_value' ||
      f.artefacts.length > 0 ||
      f.archived !== 'any' ||
      f.rerunRequested !== 'any' ||
      f.executionIsLatest !== 'any' ||
      f.environments.length > 0 ||
      f.testCases.length > 0 ||
      f.metadata.length > 0 ||
      f.fromDate !== '' ||
      f.untilDate !== ''
    );
  });

  hasMore = $derived(this.results.length < this.totalCount);

  initFromUrl(params: URLSearchParams) {
    const filters = deserializeFilters(params);
    const serialized = JSON.stringify(filters);
    if (serialized !== JSON.stringify(this.appliedFilters)) {
      this.appliedFilters = filters;
      this.workingFilters = JSON.parse(serialized) as TestResultFilters;
      if (this.hasFilters) {
        this.search(filters);
      } else {
        this.results = [];
        this.totalCount = 0;
      }
    }
  }

  async search(filters: TestResultFilters) {
    this.loading = true;
    this.error = null;
    const query = serializeToApiQuery(filters, PAGE_SIZE, 0);
    const data = await api<TestResultSearchResponse>(`/test-results?${query}`);
    if (data) {
      this.results = data.test_results;
      this.totalCount = data.count;
    } else {
      this.results = [];
      this.totalCount = 0;
      this.error = 'Failed to load test results';
    }
    this.loading = false;
  }

  async loadMore() {
    if (!this.hasMore || this.loadingMore) return;
    this.loadingMore = true;
    const query = serializeToApiQuery(this.appliedFilters, PAGE_SIZE, this.results.length);
    const data = await api<TestResultSearchResponse>(`/test-results?${query}`);
    if (data) {
      this.results = [...this.results, ...data.test_results];
      this.totalCount = data.count;
    }
    this.loadingMore = false;
  }

  async loadMetadata() {
    if (this._metadataLoaded) return;
    this._metadataLoaded = true;
    const data = await api<ExecutionMetadataResponse>('/execution-metadata');
    if (data) {
      this.metadataOptions = data.execution_metadata;
    }
  }

  async loadUsers() {
    if (this.cachedUsers.length > 0) return;
    const data = await api<UsersResponse>('/users');
    if (data) {
      this.cachedUsers = data.users;
    }
  }

  async loadIssues(query: string): Promise<MinimalIssue[]> {
    const data = await api<IssuesGetResponse>(`/issues?q=${encodeURIComponent(query)}&limit=20`);
    return data?.issues ?? [];
  }

  // --- Async search for filter dropdowns ---
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

  // --- Bulk actions ---
  async attachIssue(issueId: number, filters: TestResultFilters) {
    await api(`/issues/${issueId}/attach`, {
      method: 'POST',
      body: JSON.stringify({ test_results_filters: filtersToApiBody(filters) }),
    });
  }

  async detachIssue(issueId: number, filters: TestResultFilters) {
    await api(`/issues/${issueId}/detach`, {
      method: 'POST',
      body: JSON.stringify({ test_results_filters: filtersToApiBody(filters) }),
    });
  }

  async createReruns(filters: TestResultFilters) {
    await api('/test-executions/reruns?silent=true', {
      method: 'POST',
      body: JSON.stringify({ test_results_filters: filtersToApiBody(filters) }),
    });
  }

  async deleteReruns(filters: TestResultFilters) {
    await api('/test-executions/reruns', {
      method: 'DELETE',
      body: JSON.stringify({ test_results_filters: filtersToApiBody(filters) }),
    });
  }

  async getOrCreateIssue(url: string): Promise<number | null> {
    const issue = await api<{ id: number }>('/issues', {
      method: 'PUT',
      body: JSON.stringify({ url }),
    });
    return issue?.id ?? null;
  }

  async createAttachmentRule(issueId: number, filters: TestResultFilters) {
    const body = filtersToApiBody(filters);
    await api(`/issues/${issueId}/attachment-rules`, {
      method: 'POST',
      body: JSON.stringify({
        enabled: true,
        families: body.families ?? [],
        environment_names: body.environments ?? [],
        test_case_names: body.test_cases ?? [],
        template_ids: [],
        test_result_statuses: body.test_result_statuses ?? [],
        execution_metadata: body.execution_metadata ?? {},
      }),
    });
  }
}

// Convert frontend filters → backend TestResultSearchFilters body
function filtersToApiBody(filters: TestResultFilters): Record<string, unknown> {
  const body: Record<string, unknown> = {};
  if (filters.families.length > 0) body.families = filters.families;
  if (filters.statuses.length > 0) body.test_result_statuses = filters.statuses;
  if (filters.artefacts.length > 0) body.artefacts = filters.artefacts;
  if (filters.environments.length > 0) body.environments = filters.environments;
  if (filters.testCases.length > 0) body.test_cases = filters.testCases;

  if (filters.issueMode === 'has_any') body.issues = 'ANY';
  else if (filters.issueMode === 'has_none') body.issues = 'NONE';
  else if (filters.issueMode === 'specific' && filters.issueIds.length > 0) {
    body.issues = filters.issueIds;
  }

  if (filters.assigneeMode === 'has_any') body.assignee_ids = 'ANY';
  else if (filters.assigneeMode === 'has_none') body.assignee_ids = 'NONE';
  else if (filters.assigneeMode === 'specific' && filters.assigneeIds.length > 0) {
    body.assignee_ids = filters.assigneeIds;
  }

  if (filters.archived !== 'any') body.artefact_is_archived = filters.archived === 'yes';
  if (filters.rerunRequested !== 'any') body.rerun_is_requested = filters.rerunRequested === 'yes';
  if (filters.executionIsLatest !== 'any')
    body.execution_is_latest = filters.executionIsLatest === 'yes';

  if (filters.metadata.length > 0) {
    // Decode base64 pairs and group into { category: [value, ...] }
    const grouped: Record<string, string[]> = {};
    for (const encoded of filters.metadata) {
      const colonIdx = encoded.indexOf(':');
      if (colonIdx === -1) continue;
      try {
        const category = atob(encoded.slice(0, colonIdx));
        const value = atob(encoded.slice(colonIdx + 1));
        if (!grouped[category]) grouped[category] = [];
        grouped[category].push(value);
      } catch {
        // skip invalid
      }
    }
    body.execution_metadata = grouped;
  }

  if (filters.fromDate) body.from_date = filters.fromDate;
  if (filters.untilDate) body.until_date = filters.untilDate;

  return body;
}
