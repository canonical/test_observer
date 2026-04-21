import { api } from '$lib/api/client';
import type { Artefact } from '$lib/types';
import type {
  ArtefactBuild,
  EnvironmentReview,
  ArtefactVersion,
  EnvironmentIssue,
  TestIssue,
  TestResult,
  TestEvent,
  EnrichedTestExecution,
  ArtefactEnvironment,
  RerunRequest,
} from '$lib/types/artefact-page';

export class ArtefactPageStore {
  artefact = $state<Artefact | null>(null);
  builds = $state<ArtefactBuild[]>([]);
  reviews = $state<EnvironmentReview[]>([]);
  versions = $state<ArtefactVersion[]>([]);
  environmentIssues = $state<EnvironmentIssue[]>([]);
  testIssues = $state<TestIssue[]>([]);
  loading = $state(true);

  // Lazy caches keyed by testExecutionId
  private _testResults = $state<Record<number, TestResult[] | 'loading'>>({});
  private _testEvents = $state<Record<number, TestEvent[] | 'loading'>>({});

  // Derived: join builds+reviews into enriched executions
  enrichedExecutions = $derived.by(() => {
    const result: EnrichedTestExecution[] = [];
    for (const build of this.builds) {
      for (const te of build.test_executions) {
        const review = this.reviews.find(
          (r) => r.artefact_build.id === build.id && r.environment.id === te.environment.id,
        );
        if (review) {
          result.push({
            testExecution: { ...te, artefact_build_id: build.id },
            environmentReview: review,
          });
        }
      }
    }
    return result;
  });

  // Group into environments
  allEnvironments = $derived.by(() => {
    const map = new Map<number, ArtefactEnvironment>();
    for (const ee of this.enrichedExecutions) {
      const key = ee.environmentReview.id;
      if (!map.has(key)) {
        map.set(key, {
          review: ee.environmentReview,
          runsDescending: [],
          name: ee.environmentReview.environment.name,
          architecture: ee.environmentReview.environment.architecture,
        });
      }
      map.get(key)!.runsDescending.push(ee.testExecution);
    }
    // Sort runs descending by id
    for (const env of map.values()) {
      env.runsDescending.sort((a, b) => b.id - a.id);
    }
    return Array.from(map.values());
  });

  async init(artefactId: number) {
    this.loading = true;
    // Blocking: fetch artefact
    const artefact = await api<Artefact>(`/artefacts/${artefactId}`);
    this.artefact = artefact;

    // Non-blocking: fire everything in parallel
    const [builds, reviews, versions, envIssues, testIssues] = await Promise.all([
      api<ArtefactBuild[]>(`/artefacts/${artefactId}/builds`),
      api<EnvironmentReview[]>(`/artefacts/${artefactId}/environment-reviews`),
      api<ArtefactVersion[]>(`/artefacts/${artefactId}/versions`),
      api<EnvironmentIssue[]>('/environments/reported-issues'),
      api<TestIssue[]>('/test-cases/reported-issues'),
    ]);
    this.builds = builds ?? [];
    this.reviews = reviews ?? [];
    this.versions = versions ?? [];
    this.environmentIssues = envIssues ?? [];
    this.testIssues = testIssues ?? [];
    this.loading = false;
  }

  // Lazy-load getters
  getTestResults(executionId: number): TestResult[] | 'loading' | undefined {
    return this._testResults[executionId];
  }

  getTestEvents(executionId: number): TestEvent[] | 'loading' | undefined {
    return this._testEvents[executionId];
  }

  async fetchTestResults(executionId: number) {
    if (this._testResults[executionId]) return;
    this._testResults[executionId] = 'loading';
    const data = await api<TestResult[]>(`/test-executions/${executionId}/test-results`);
    this._testResults = { ...this._testResults, [executionId]: data ?? [] };
  }

  async fetchTestEvents(executionId: number) {
    if (this._testEvents[executionId]) return;
    this._testEvents[executionId] = 'loading';
    const data = await api<TestEvent[]>(`/test-executions/${executionId}/status_update`);
    this._testEvents = { ...this._testEvents, [executionId]: data ?? [] };
  }

  // Mutations
  async updateArtefactStatus(artefactId: number, status: string) {
    const updated = await api<Artefact>(`/artefacts/${artefactId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
    if (updated) this.artefact = updated;
  }

  async updateArtefactComment(artefactId: number, comment: string) {
    const updated = await api<Artefact>(`/artefacts/${artefactId}`, {
      method: 'PATCH',
      body: JSON.stringify({ comment }),
    });
    if (updated) this.artefact = updated;
  }

  async submitReview(
    artefactId: number,
    reviewId: number,
    body: { review_decision: string[]; review_comment: string },
  ) {
    const updated = await api<EnvironmentReview>(
      `/artefacts/${artefactId}/environment-reviews/${reviewId}`,
      { method: 'PATCH', body: JSON.stringify(body) },
    );
    if (updated) {
      this.reviews = this.reviews.map((r) => (r.id === reviewId ? updated : r));
      if (this.artefact) {
        const completed = this.reviews.filter((r) => r.review_decision.length > 0).length;
        this.artefact = { ...this.artefact, completed_environment_reviews_count: completed };
      }
    }
  }

  async rerunExecutions(ids: number[]) {
    await api<RerunRequest[]>('/test-executions/reruns', {
      method: 'POST',
      body: JSON.stringify({ test_execution_ids: ids }),
    });
    this.builds = this.builds.map((b) => ({
      ...b,
      test_executions: b.test_executions.map((te) =>
        ids.includes(te.id) ? { ...te, is_rerun_requested: true } : te,
      ),
    }));
  }

  async startManualTest(artefactId: number, body: Record<string, unknown>) {
    await api<void>('/test-executions/start-test', {
      method: 'PUT',
      body: JSON.stringify(body),
    });
    await this.refreshBuilds(artefactId);
  }

  async addTestResult(
    executionId: number,
    artefactId: number,
    body: { name: string; status: string; comment?: string; io_log?: string },
  ) {
    await api<void>(`/test-executions/${executionId}/test-results`, {
      method: 'POST',
      body: JSON.stringify([body]),
    });
    this._testResults = { ...this._testResults };
    delete this._testResults[executionId];
    await this.refreshBuilds(artefactId);
  }

  // Environment issues CRUD
  async createEnvironmentIssue(body: Omit<EnvironmentIssue, 'id'>) {
    const created = await api<EnvironmentIssue>('/environments/reported-issues', {
      method: 'POST',
      body: JSON.stringify(body),
    });
    if (created) this.environmentIssues = [...this.environmentIssues, created];
  }

  async updateEnvironmentIssue(id: number, body: Partial<EnvironmentIssue>) {
    const updated = await api<EnvironmentIssue>(`/environments/reported-issues/${id}`, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
    if (updated) {
      this.environmentIssues = this.environmentIssues.map((i) => (i.id === id ? updated : i));
    }
  }

  async deleteEnvironmentIssue(id: number) {
    await api<void>(`/environments/reported-issues/${id}`, { method: 'DELETE' });
    this.environmentIssues = this.environmentIssues.filter((i) => i.id !== id);
  }

  // Test issues CRUD
  async createTestIssue(body: Omit<TestIssue, 'id'>) {
    const created = await api<TestIssue>('/test-cases/reported-issues', {
      method: 'POST',
      body: JSON.stringify(body),
    });
    if (created) this.testIssues = [...this.testIssues, created];
  }

  async updateTestIssue(id: number, body: Partial<TestIssue>) {
    const updated = await api<TestIssue>(`/test-cases/reported-issues/${id}`, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
    if (updated) this.testIssues = this.testIssues.map((i) => (i.id === id ? updated : i));
  }

  async deleteTestIssue(id: number) {
    await api<void>(`/test-cases/reported-issues/${id}`, { method: 'DELETE' });
    this.testIssues = this.testIssues.filter((i) => i.id !== id);
  }

  private async refreshBuilds(artefactId: number) {
    const [builds, reviews] = await Promise.all([
      api<ArtefactBuild[]>(`/artefacts/${artefactId}/builds`),
      api<EnvironmentReview[]>(`/artefacts/${artefactId}/environment-reviews`),
    ]);
    if (builds) this.builds = builds;
    if (reviews) this.reviews = reviews;
  }
}
