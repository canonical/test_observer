// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { api, FetchError, silentApi } from "$lib/api/client";
import { SvelteMap, SvelteSet } from "svelte/reactivity";
import { userStore } from "$lib/stores/user.svelte";
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
  reviewsAvailable = $state(true);
  versions = $state<ArtefactVersionResponse[]>([]);
  environmentIssues = $state<EnvironmentReportedIssueResponse[]>([]);
  testIssues = $state<TestReportedIssueResponse[]>([]);
  loading = $state(true);
  accessError = $state<
    | "requiresLogin"
    | "forbidden"
    | "sessionCheckFailed"
    | "familyMismatch"
    | null
  >(null);

  get canChangeArtefact() {
    // Matching-rule grants are not included in /users/me, so they cannot be
    // established client-side. Administrators are the only users whose
    // artefact write access can be confirmed from the existing user response.
    return userStore.isConfirmedAdmin;
  }

  get canChangeRerun() {
    // Rerun access is also granted by artefact matching rules, which /me does
    // not expose. Fail closed except for administrators, who bypass that check.
    return userStore.isConfirmedAdmin;
  }

  get canChangeRerunBulk() {
    // The bulk permission alone does not establish the required matching-rule
    // grant for this artefact. Administrators bypass both backend checks.
    return userStore.isConfirmedAdmin;
  }

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
    Record<number, TestEvent[] | "loading" | "error" | undefined>
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
        // Separate requests can observe different snapshots; a missing review
        // must not hide an execution or imply a synthetic review exists.
        result.push({
          testExecution: { ...te, artefact_build_id: build.id },
          environmentReview: review ?? null,
        });
      }
    }
    return result;
  });

  // Match Flutter: each row groups runs for one build/environment review.
  allEnvironments = $derived.by(() => {
    const map = new SvelteMap<string, ArtefactEnvironment>();
    for (const ee of this.enrichedExecutions) {
      const key = ee.environmentReview
        ? `review:${ee.environmentReview.id}`
        : `build:${ee.testExecution.artefact_build_id}:environment:${ee.testExecution.environment.id}`;
      let environment = map.get(key);
      if (environment === undefined) {
        environment = {
          key,
          review: ee.environmentReview,
          runsDescending: [],
          name: ee.testExecution.environment.name,
          architecture: ee.testExecution.environment.architecture,
        };
        map.set(key, environment);
      }
      environment.runsDescending.push(ee.testExecution);
    }
    for (const env of map.values()) {
      env.runsDescending.sort((a, b) => b.id - a.id);
    }
    return Array.from(map.values());
  });

  async init(artefactId: number, expectedFamily?: string) {
    // Capture this call's generation so results from a superseded init() are
    // discarded instead of clobbering data loaded by a newer one.
    const generation = ++this._initGeneration;
    this._activeArtefactId = artefactId;
    this.loading = true;
    this.accessError = null;
    this.artefact = null;
    this.builds = [];
    this.reviews = [];
    this.reviewsAvailable = true;
    this.versions = [];
    this.environmentIssues = [];
    this.testIssues = [];
    this._testResults = {};
    this._testEvents = {};
    this.selectedEnvironmentIds = new SvelteSet();

    try {
      const artefact = await api<Artefact>(
        `/artefacts/${artefactId}`,
        {},
        { ignoreForbidden: true },
      );
      if (generation !== this._initGeneration) return;
      if (expectedFamily && artefact?.family !== expectedFamily) {
        this.accessError = "familyMismatch";
        return;
      }
      this.artefact = artefact;

      const [builds, reviews, versions, envIssues, testIssues] =
        await Promise.all([
          api<ArtefactBuildResponse[]>(
            `/artefacts/${artefactId}/builds`,
            {},
            { ignoreForbidden: true },
          ),
          api<ArtefactBuildEnvironmentReviewResponse[]>(
            `/artefacts/${artefactId}/environment-reviews`,
            {},
            { ignoreForbidden: true },
          ).catch((err: unknown) => {
            if (err instanceof FetchError && err.status === 403) return null;
            throw err;
          }),
          api<ArtefactVersionResponse[]>(
            `/artefacts/${artefactId}/versions`,
            {},
            { ignoreForbidden: true },
          ),
          this.loadEnvironmentIssues(),
          api<TestReportedIssueResponse[]>(
            "/test-cases/reported-issues",
            {},
            { ignoreForbidden: true },
          ).catch(() => null),
        ]);
      if (generation !== this._initGeneration) return;

      this.builds = builds ?? [];
      this.reviews = reviews ?? [];
      this.reviewsAvailable = reviews !== null;
      this.versions = versions ?? [];
      this.environmentIssues = envIssues ?? [];
      this.testIssues = testIssues ?? [];
    } catch (err) {
      if (generation !== this._initGeneration) return;
      // api already surfaced the error to the UI; leave the cleared state
      // in place so the page shows an empty/error view rather than stale data.
      this.artefact = null;
      if (
        err instanceof FetchError &&
        (err.status === 401 || err.status === 403)
      ) {
        const authStatus = await userStore.refresh(fetch);
        if (generation !== this._initGeneration) return;
        if (err.status === 403 && authStatus === "authenticated") {
          this.accessError = "forbidden";
        } else if (authStatus === "unknown") {
          this.accessError = "sessionCheckFailed";
        } else {
          this.accessError = "requiresLogin";
        }
      }
    } finally {
      // Only the most recent init() owns the loading flag.
      if (generation === this._initGeneration) this.loading = false;
    }
  }

  private async loadEnvironmentIssues() {
    try {
      const issues = await api<EnvironmentReportedIssueResponse[]>(
        "/environments/reported-issues",
        {},
        { ignoreForbidden: true },
      );
      return issues;
    } catch {
      return null;
    }
  }

  getTestResults(executionId: number): TestResult[] | "loading" | undefined {
    return this._testResults[executionId];
  }

  getTestEvents(
    executionId: number,
  ): TestEvent[] | "loading" | "error" | undefined {
    return this._testEvents[executionId];
  }

  async fetchTestResults(executionId: number) {
    if (this._testResults[executionId]) return;
    const generation = this._initGeneration;
    this._testResults[executionId] = "loading";
    try {
      const data = await silentApi<TestResult[]>(
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
    const cachedEvents = this._testEvents[executionId];
    if (cachedEvents && cachedEvents !== "error") return;
    const generation = this._initGeneration;
    this._testEvents[executionId] = "loading";
    try {
      const data = await silentApi<TestEvent[]>(
        `/test-executions/${executionId}/status_update`,
      );
      if (generation !== this._initGeneration) return;
      this._testEvents = { ...this._testEvents, [executionId]: data ?? [] };
    } catch {
      if (generation !== this._initGeneration) return;
      // Preserve a retryable local failure state without opening the global
      // error popup for this lazy, recoverable request.
      this._testEvents = { ...this._testEvents, [executionId]: "error" };
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
  private async requireEnvironmentIssueMutationAccess() {
    const authStatus = await userStore.refresh(fetch);
    if (authStatus !== "authenticated") {
      throw new Error("An authenticated session is required to mutate issues");
    }
    if (!userStore.hasPermission("change_environment_reported_issue")) {
      throw new Error("Environment issue mutations are not permitted");
    }
  }

  async createEnvironmentIssue(
    body: Omit<
      EnvironmentReportedIssueResponse,
      "id" | "created_at" | "updated_at"
    >,
  ) {
    await this.requireEnvironmentIssueMutationAccess();
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
    await this.requireEnvironmentIssueMutationAccess();
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
    await this.requireEnvironmentIssueMutationAccess();
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
