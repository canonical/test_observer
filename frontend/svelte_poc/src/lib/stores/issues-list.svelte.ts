import { api } from '$lib/api/client';
import type { MinimalIssue, IssuesGetResponse } from '$lib/types/test-results';
import type { IssueListFilters } from '$lib/types/issues';
import { emptyIssueFilters } from '$lib/types/issues';

const PAGE_SIZE = 50;

interface IssueGroup {
  source: string;
  project: string;
  issues: MinimalIssue[];
}

export class IssuesListStore {
  issues = $state<MinimalIssue[]>([]);
  loading = $state(false);
  loadingMore = $state(false);
  error = $state<string | null>(null);
  filters = $state<IssueListFilters>(emptyIssueFilters());

  private _totalLoaded = 0;
  private _lastFetchCount = 0;

  hasMore = $derived(this._lastFetchCount >= PAGE_SIZE);

  grouped = $derived.by((): IssueGroup[] => {
    const groups: IssueGroup[] = [];
    let current: IssueGroup | null = null;
    for (const issue of this.issues) {
      if (!current || current.source !== issue.source || current.project !== issue.project) {
        current = { source: issue.source, project: issue.project, issues: [] };
        groups.push(current);
      }
      current.issues.push(issue);
    }
    return groups;
  });

  projectOptions = $derived.by((): string[] => {
    const set = new Set<string>();
    for (const issue of this.issues) {
      if (issue.project) set.add(issue.project);
    }
    return [...set].sort();
  });

  hasFilters = $derived(
    this.filters.source.length > 0 ||
      this.filters.status.length > 0 ||
      this.filters.project !== '' ||
      this.filters.q !== '',
  );

  initFromUrl(params: URLSearchParams) {
    const source = params.getAll('source');
    const status = params.getAll('status');
    const project = params.get('project') ?? '';
    const q = params.get('q') ?? '';

    const newFilters: IssueListFilters = { source, status, project, q };
    if (JSON.stringify(newFilters) !== JSON.stringify(this.filters)) {
      this.filters = newFilters;
      this.fetchIssues();
    }
  }

  serializeToUrl(): URLSearchParams {
    const params = new URLSearchParams();
    for (const s of this.filters.source) params.append('source', s);
    for (const s of this.filters.status) params.append('status', s);
    if (this.filters.project) params.set('project', this.filters.project);
    if (this.filters.q) params.set('q', this.filters.q);
    return params;
  }

  private buildQuery(limit: number, offset: number): string {
    const params = new URLSearchParams();
    for (const s of this.filters.source) params.append('source', s);
    for (const s of this.filters.status) params.append('status', s);
    if (this.filters.project) params.set('project', this.filters.project);
    if (this.filters.q) params.set('q', this.filters.q);
    params.set('limit', String(limit));
    params.set('offset', String(offset));
    return params.toString();
  }

  async fetchIssues() {
    this.loading = true;
    this.error = null;
    const query = this.buildQuery(PAGE_SIZE, 0);
    const data = await api<IssuesGetResponse>(`/issues?${query}`);
    if (data) {
      this.issues = data.issues;
      this._totalLoaded = data.issues.length;
      this._lastFetchCount = data.issues.length;
    } else {
      this.issues = [];
      this._totalLoaded = 0;
      this._lastFetchCount = 0;
      this.error = 'Failed to load issues';
    }
    this.loading = false;
  }

  async loadMore() {
    if (!this.hasMore || this.loadingMore) return;
    this.loadingMore = true;
    const query = this.buildQuery(PAGE_SIZE, this._totalLoaded);
    const data = await api<IssuesGetResponse>(`/issues?${query}`);
    if (data) {
      this.issues = [...this.issues, ...data.issues];
      this._totalLoaded += data.issues.length;
      this._lastFetchCount = data.issues.length;
    }
    this.loadingMore = false;
  }

  async addIssueByUrl(url: string): Promise<number | null> {
    const result = await api<{ id: number }>('/issues', {
      method: 'PUT',
      body: JSON.stringify({ url }),
    });
    if (result) {
      await this.fetchIssues();
      return result.id;
    }
    return null;
  }
}
