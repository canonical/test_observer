// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { api } from "$lib/api/client";
import { SvelteMap, SvelteSet } from "svelte/reactivity";
import type { Artefact, ArtefactStatus } from "$lib/types";
import type {
  ArtefactBuildResponse,
  ArtefactBuildEnvironmentReviewResponse,
  ArtefactBuildEnvironmentReviewDecision,
  ArtefactVersionResponse,
  EnvironmentReportedIssueResponse,
  PendingRerunResponse,
  TestReportedIssueResponse,
} from "$lib/types/openapi";
import type {
  TestResult,
  TestEvent,
  RerunExecutionsRequest,
  EnrichedTestExecution,
  ArtefactEnvironment,
} from "$lib/types/artefact-page";

export class ArtefactPageStore {
  artefact = $state<Artefact | null>(null);
  builds = $state<ArtefactBuildResponse[]>([]);
  reviews = $state<ArtefactBuildEnvironmentReviewResponse[]>([]);
  versions = $state<ArtefactVersionResponse[]>([]);
  environmentIssues = $state<EnvironmentReportedIssueResponse[]>([]);
  testIssues = $state<TestReportedIssueResponse[]>([]);
  loading = $state(true);

  // Monotonic counter guarding against a stale init() overwriting newer data.
  private _initGeneration = 0;
  // Identity of the resource requested by the current init(), including while
  // that request is still loading.
  private _activeArtefactId: number | null = null;
  // Per-resource counters prevent an older mutation response from replacing a
  // newer response for the same page state.
  private _mutationGenerations = new SvelteMap<string, number>();

  private beginMutation(
    key: string,
    artefactId: number | null = this._activeArtefactId,
  ) {
    const generation = (this._mutationGenerations.get(key) ?? 0) + 1;
    this._mutationGenerations.set(key, generation);
    return { page: this._initGeneration, generation, artefactId };
  }

  private isCurrentMutation(
    key: string,
    mutation: { page: number; generation: number; artefactId: number | null },
  ) {
    return (
      mutation.page === this._initGeneration &&
      mutation.artefactId === this._activeArtefactId &&
      mutation.generation === this._mutationGenerations.get(key)
    );
  }

  // Bulk selection state
  selectedEnvironmentIds = $state(new SvelteSet<number>());

  toggleSelection(envId: number) {
    const next = new SvelteSet(this.selectedEnvironmentIds);
    if (next.has(envId)) next.delete(envId);
    else next.add(envId);
    this.selectedEnvironmentIds = next;
  }

  selectAll(envIds: number[]) {
    this.selectedEnvironmentIds = new SvelteSet(envIds);
  }

  deselectAll() {
    this.selectedEnvironmentIds = new SvelteSet();
  }

  isSelected(envId: number): boolean {
    return this.selectedEnvironmentIds.has(envId);
  }

  // Lazy caches keyed by testExecutionId
  private _testResults = $state<
    Record<number, TestResult[] | "loading" | undefined>
  >({});
  private _testEvents = $state<
    Record<number, TestEvent[] | "loading" | undefined>
  >({});

  // Join builds + reviews into enriched executions
  enrichedExecutions = $derived.by(() => {
    const result: EnrichedTestExecution[] = [];
    for (const build of this.builds) {
      for (const te of build.test_executions) {
        const review = this.reviews.find(
          (r) =>
            r.artefact_build.id === build.id &&
            r.environment.id === te.environment.id,
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

  // Group enriched executions into per-environment buckets
  allEnvironments = $derived.by(() => {
    const map = new SvelteMap<number, ArtefactEnvironment>();
    for (const ee of this.enrichedExecutions) {
      const key = ee.testExecution.environment.id;
      let environment = map.get(key);
      if (environment === undefined) {
        environment = {
          reviews: [],
          runsDescending: [],
          name: ee.environmentReview.environment.name,
          architecture: ee.environmentReview.environment.architecture,
        };
        map.set(key, environment);
      }
      if (
        !environment.reviews.some(
          (review) => review.id === ee.environmentReview.id,
        )
      ) {
        environment.reviews.push(ee.environmentReview);
      }
      environment.runsDescending.push(ee.testExecution);
    }
    for (const env of map.values()) {
      env.runsDescending.sort((a, b) => b.id - a.id);
    }
    return Array.from(map.values());
  });

  async init(artefactId: number) {
    // Capture this call's generation so results from a superseded init() are
    // discarded instead of clobbering data loaded by a newer one.
    const generation = ++this._initGeneration;
    this._activeArtefactId = artefactId;
    this.loading = true;
    this.artefact = null;
    this.builds = [];
    this.reviews = [];
    this.versions = [];
    this.environmentIssues = [];
    this.testIssues = [];
    this._testResults = {};
    this._testEvents = {};
    this.selectedEnvironmentIds = new SvelteSet();

    try {
      const artefact = await api<Artefact>(`/artefacts/${artefactId}`);
      if (generation !== this._initGeneration) return;
      this.artefact = artefact;

      const [builds, reviews, versions, envIssues, testIssues] =
        await Promise.all([
          api<ArtefactBuildResponse[]>(`/artefacts/${artefactId}/builds`),
          api<ArtefactBuildEnvironmentReviewResponse[]>(
            `/artefacts/${artefactId}/environment-reviews`,
          ),
          api<ArtefactVersionResponse[]>(`/artefacts/${artefactId}/versions`),
          api<EnvironmentReportedIssueResponse[]>(
            "/environments/reported-issues",
            {},
            { ignoreForbidden: true },
          ).catch(() => null),
          api<TestReportedIssueResponse[]>(
            "/test-cases/reported-issues",
            {},
            { ignoreForbidden: true },
          ).catch(() => null),
        ]);
      if (generation !== this._initGeneration) return;

      this.builds = builds ?? [];
      this.reviews = reviews ?? [];
      this.versions = versions ?? [];
      this.environmentIssues = envIssues ?? [];
      this.testIssues = testIssues ?? [];
    } catch {
      // api already surfaced the error to the UI; leave the cleared state
      // in place so the page shows an empty/error view rather than stale data.
    } finally {
      // Only the most recent init() owns the loading flag.
      if (generation === this._initGeneration) this.loading = false;
    }
  }

  getTestResults(executionId: number): TestResult[] | "loading" | undefined {
    return this._testResults[executionId];
  }

  getTestEvents(executionId: number): TestEvent[] | "loading" | undefined {
    return this._testEvents[executionId];
  }

  async fetchTestResults(executionId: number) {
    if (this._testResults[executionId]) return;
    const generation = this._initGeneration;
    this._testResults[executionId] = "loading";
    try {
      const data = await api<TestResult[]>(
        `/test-executions/${executionId}/test-results`,
      );
      if (generation !== this._initGeneration) return;
      this._testResults = { ...this._testResults, [executionId]: data ?? [] };
    } catch {
      if (generation !== this._initGeneration) return;
      // Drop the "loading" marker so a later call retries instead of caching
      // the failure as an empty result set.
      this._testResults = { ...this._testResults, [executionId]: undefined };
    }
  }

  async fetchTestEvents(executionId: number) {
    if (this._testEvents[executionId]) return;
    const generation = this._initGeneration;
    this._testEvents[executionId] = "loading";
    try {
      const data = await api<TestEvent[]>(
        `/test-executions/${executionId}/status_update`,
      );
      if (generation !== this._initGeneration) return;
      this._testEvents = { ...this._testEvents, [executionId]: data ?? [] };
    } catch {
      if (generation !== this._initGeneration) return;
      // Drop the "loading" marker so a later call retries instead of caching
      // the failure as an empty event list.
      this._testEvents = { ...this._testEvents, [executionId]: undefined };
    }
  }

  async updateArtefactStatus(artefactId: number, status: ArtefactStatus) {
    const mutation = this.beginMutation(`artefact:${artefactId}`, artefactId);
    const updated = await api<Artefact>(`/artefacts/${artefactId}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
    if (updated && this.isCurrentMutation(`artefact:${artefactId}`, mutation)) {
      this.artefact = updated;
    }
  }

  async updateArtefactComment(artefactId: number, comment: string) {
    const mutation = this.beginMutation(`artefact:${artefactId}`, artefactId);
    const updated = await api<Artefact>(`/artefacts/${artefactId}`, {
      method: "PATCH",
      body: JSON.stringify({ comment }),
    });
    if (updated && this.isCurrentMutation(`artefact:${artefactId}`, mutation)) {
      this.artefact = updated;
    }
  }

  async submitReview(
    artefactId: number,
    reviewId: number,
    body: {
      review_decision: ArtefactBuildEnvironmentReviewDecision[];
      review_comment: string;
    },
  ) {
    const key = `review:${artefactId}:${reviewId}`;
    const mutation = this.beginMutation(key, artefactId);
    const updated = await api<ArtefactBuildEnvironmentReviewResponse>(
      `/artefacts/${artefactId}/environment-reviews/${reviewId}`,
      { method: "PATCH", body: JSON.stringify(body) },
    );
    if (updated && this.isCurrentMutation(key, mutation)) {
      this.reviews = this.reviews.map((r) => (r.id === reviewId ? updated : r));
      if (this.artefact) {
        const completed = this.reviews.filter(
          (r) => r.review_decision.length > 0,
        ).length;
        this.artefact = {
          ...this.artefact,
          completed_environment_reviews_count: completed,
        };
      }
    }
  }

  async bulkUpdateEnvironmentReviews(
    artefactId: number,
    reviews: {
      id: number;
      review_decision: ArtefactBuildEnvironmentReviewDecision[];
      review_comment: string;
    }[],
  ) {
    const mutations = reviews.map(({ id }) => {
      const key = `review:${artefactId}:${id}`;
      return { id, key, mutation: this.beginMutation(key, artefactId) };
    });
    const updated = await api<ArtefactBuildEnvironmentReviewResponse[]>(
      `/artefacts/${artefactId}/environment-reviews`,
      { method: "PATCH", body: JSON.stringify(reviews) },
    );
    if (
      updated &&
      mutations.some(({ mutation }) => this.isCurrentResource(mutation))
    ) {
      const currentIds = new SvelteSet(
        mutations
          .filter(({ key, mutation }) => this.isCurrentMutation(key, mutation))
          .map(({ id }) => id),
      );
      const updatedMap = new SvelteMap(
        updated
          .filter((review) => currentIds.has(review.id))
          .map((review) => [review.id, review]),
      );
      this.reviews = this.reviews.map((r) => updatedMap.get(r.id) ?? r);
      if (this.artefact) {
        const completed = this.reviews.filter(
          (r) => r.review_decision.length > 0,
        ).length;
        this.artefact = {
          ...this.artefact,
          completed_environment_reviews_count: completed,
        };
      }
    }
  }

  async rerunExecutions(ids: number[]) {
    const mutation = this.beginMutation("builds");
    const reruns = await api<PendingRerunResponse[]>(
      "/test-executions/reruns",
      {
        method: "POST",
        body: JSON.stringify({
          test_execution_ids: ids,
        } satisfies RerunExecutionsRequest),
      },
    );
    if (!this.isCurrentMutation("builds", mutation)) return;
    const rerunIds = new SvelteSet(
      (reruns ?? []).map((rerun) => rerun.test_execution_id),
    );
    this.builds = this.builds.map((b) => ({
      ...b,
      test_executions: b.test_executions.map((te) =>
        rerunIds.has(te.id) ? { ...te, is_rerun_requested: true } : te,
      ),
    }));
  }

  // Environment issues CRUD
  async createEnvironmentIssue(
    body: Omit<
      EnvironmentReportedIssueResponse,
      "id" | "created_at" | "updated_at"
    >,
  ) {
    const mutation = {
      page: this._initGeneration,
      generation: 0,
      artefactId: this._activeArtefactId,
    };
    const created = await api<EnvironmentReportedIssueResponse>(
      "/environments/reported-issues",
      {
        method: "POST",
        body: JSON.stringify(body),
      },
    );
    if (
      created &&
      mutation.page === this._initGeneration &&
      mutation.artefactId === this._activeArtefactId
    ) {
      this.environmentIssues = [...this.environmentIssues, created];
    }
  }

  async updateEnvironmentIssue(
    id: number,
    body: Partial<EnvironmentReportedIssueResponse>,
  ) {
    const current = this.environmentIssues.find((i) => i.id === id);
    if (!current) return;
    const mutation = this.beginMutation(`environment-issue:${id}`);
    // The backend PUT replaces the whole record, so send a complete payload
    // built from the current issue merged with the requested changes.
    const merged = { ...current, ...body };
    const updated = await api<EnvironmentReportedIssueResponse>(
      `/environments/reported-issues/${id}`,
      {
        method: "PUT",
        body: JSON.stringify({
          environment_name: merged.environment_name,
          description: merged.description,
          url: merged.url,
          is_confirmed: merged.is_confirmed,
        }),
      },
    );
    if (
      updated &&
      this.isCurrentMutation(`environment-issue:${id}`, mutation)
    ) {
      this.environmentIssues = this.environmentIssues.map((i) =>
        i.id === id ? updated : i,
      );
    }
  }

  async deleteEnvironmentIssue(id: number) {
    const mutation = this.beginMutation(`environment-issue:${id}`);
    await api<null>(`/environments/reported-issues/${id}`, {
      method: "DELETE",
    });
    if (!this.isCurrentMutation(`environment-issue:${id}`, mutation)) return;
    // Only reached on success (api throws on failure), so the item is never
    // removed locally when the delete request fails.
    this.environmentIssues = this.environmentIssues.filter((i) => i.id !== id);
  }

  private async refreshBuilds(artefactId: number) {
    const mutation = this.beginMutation(`builds:${artefactId}`, artefactId);
    const [builds, reviews] = await Promise.all([
      api<ArtefactBuildResponse[]>(`/artefacts/${artefactId}/builds`),
      api<ArtefactBuildEnvironmentReviewResponse[]>(
        `/artefacts/${artefactId}/environment-reviews`,
      ),
    ]);
    if (!this.isCurrentMutation(`builds:${artefactId}`, mutation)) return;
    if (builds) this.builds = builds;
    if (reviews) this.reviews = reviews;
  }

  private isCurrentResource(mutation: {
    page: number;
    artefactId: number | null;
  }) {
    return (
      mutation.page === this._initGeneration &&
      mutation.artefactId === this._activeArtefactId
    );
  }
}
