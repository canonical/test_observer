<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import { page } from "$app/state";
  import { ArtefactPageStore } from "$lib/stores/artefact-page.svelte";
  import type { ArtefactEnvironment } from "$lib/types/artefact-page";
  import { getApiRoot } from "$lib/config";
  import {
    matchesExecutionStatuses,
    matchesPlanLastRunStatuses,
    matchingLatestPlanRuns,
    decodeFilterValues,
  } from "$lib/utils/artefact-filters";
  import ArtefactPageHeader from "$lib/components/artefact/ArtefactPageHeader.svelte";
  import ArtefactPageSidebar from "$lib/components/artefact/ArtefactPageSidebar.svelte";
  import StatusSummary from "$lib/components/artefact/StatusSummary.svelte";
  import EnvironmentExpandable from "$lib/components/artefact/EnvironmentExpandable.svelte";
  import BulkEnvironmentSelectionControls from "$lib/components/artefact/BulkEnvironmentSelectionControls.svelte";

  let { data } = $props();
  const family = $derived(data.family);
  const artefactId = $derived(data.artefactId);
  const loginUrl = $derived(
    `${getApiRoot()}/v1/auth/saml/login?return_to=${encodeURIComponent(page.url.href)}`,
  );

  function retryLoad() {
    void store.init(artefactId, family.api_name);
  }

  const store = new ArtefactPageStore();

  let sidebarOpen = $state(true);

  $effect(() => {
    store.init(artefactId, family.api_name);
  });

  // Apply all URL-driven filters to the environment list
  const visibleEnvironments = $derived.by((): ArtefactEnvironment[] => {
    const envParam = page.url.searchParams.get("environment");
    const execStatusParam = page.url.searchParams.get("execution_status");
    const reviewStatusParam = page.url.searchParams.get("review_status");
    const plansLastRunParam = page.url.searchParams.get("plans_last_run");
    const triagedParam = page.url.searchParams.get("triaged");

    const selectedEnvs = decodeFilterValues(envParam);
    const selectedExecStatuses = decodeFilterValues(execStatusParam);
    const selectedReviewStatuses = decodeFilterValues(reviewStatusParam);
    const selectedPlansLastRun = decodeFilterValues(plansLastRunParam);

    return store.allEnvironments.filter((env) => {
      // Environment name filter
      if (selectedEnvs.length > 0 && !selectedEnvs.includes(env.name))
        return false;

      // Test execution status filter (any run matching)
      if (selectedExecStatuses.length > 0) {
        if (!matchesExecutionStatuses(env.runsDescending, selectedExecStatuses))
          return false;
      }

      // Review status filter
      if (selectedReviewStatuses.length > 0) {
        if (!env.review) return false;
        const decision = env.review.review_decision;
        let reviewStatus: string;
        if (decision.length === 0) reviewStatus = "Undecided";
        else if (decision.includes("REJECTED")) reviewStatus = "Rejected";
        else reviewStatus = "Approved";
        if (!selectedReviewStatuses.includes(reviewStatus)) return false;
      }

      // Plans whose last run filter (filter by latest run status)
      if (selectedPlansLastRun.length > 0) {
        if (
          !matchesPlanLastRunStatuses(env.runsDescending, selectedPlansLastRun)
        )
          return false;
      }

      // Triaged filter
      if (triagedParam) {
        const isTriaged = env.runsDescending.some((r) => r.is_triaged);
        if (triagedParam === "Yes" && !isTriaged) return false;
        if (triagedParam === "No" && isTriaged) return false;
      }

      return true;
    });
  });

  // Rerun all filtered test plans
  let rerunning = $state(false);

  const rerunCount = $derived.by(() => {
    const decodedStatuses = decodeFilterValues(
      page.url.searchParams.get("plans_last_run"),
    );
    return visibleEnvironments.reduce(
      (count, env) =>
        count +
        matchingLatestPlanRuns(env.runsDescending, decodedStatuses).length,
      0,
    );
  });

  function getRerunIds(): number[] {
    const ids: number[] = [];
    const selectedStatuses = decodeFilterValues(
      page.url.searchParams.get("plans_last_run"),
    );
    for (const env of visibleEnvironments) {
      ids.push(
        ...matchingLatestPlanRuns(env.runsDescending, selectedStatuses).map(
          (run) => run.id,
        ),
      );
    }
    return ids;
  }

  async function handleRerunAll() {
    if (
      !store.canChangeRerun ||
      !store.canChangeRerunBulk
    ) {
      return;
    }
    rerunning = true;
    try {
      await store.rerunExecutions(getRerunIds());
    } catch {
      // The API client reports request failures through the global error UI.
    } finally {
      rerunning = false;
    }
  }
</script>

{#if store.loading && !store.artefact}
  <div class="loading-page">
    <div class="spinner"></div>
    <span>Loading artefact…</span>
  </div>
{:else if store.accessError === "requiresLogin"}
  <div class="error-state" role="status">
    <p>You need to be logged in to view this artefact.</p>
    <!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
    <a href={loginUrl}>Log in</a>
  </div>
{:else if store.accessError === "forbidden"}
  <div class="error-state" role="alert">
    <p>You don't have permission to view this artefact.</p>
  </div>
{:else if store.accessError === "sessionCheckFailed"}
  <div class="error-state" role="alert">
    <p>We couldn't verify your session. Please try again.</p>
    <button onclick={retryLoad}>Retry</button>
  </div>
{:else if store.accessError === "familyMismatch"}
  <div class="error-state" role="alert">
    <p>Artefact not found in this family.</p>
  </div>
{:else if store.artefact}
  <div class="artefact-page">
    <ArtefactPageHeader
      artefact={store.artefact}
      {family}
      versions={store.versions}
      {store}
    />

    <div class="page-body">
      <button
        class="sidebar-toggle"
        title={sidebarOpen ? "Hide sidebar" : "Show sidebar"}
        aria-label={sidebarOpen ? "Hide sidebar" : "Show sidebar"}
        onclick={() => (sidebarOpen = !sidebarOpen)}
        aria-pressed={sidebarOpen}
      >
        &#9776;
      </button>

      <div class="content-area">
        {#if sidebarOpen}
          <ArtefactPageSidebar artefact={store.artefact} {store} />
        {/if}

        <div class="main-content">
          {#if store.loading}
            <div class="loading-inline">
              <div class="spinner-sm"></div>
              Loading test data…
            </div>
          {:else if store.allEnvironments.length === 0}
            <div class="empty-state">
              <p>No test executions found for this artefact.</p>
            </div>
          {:else}
            <div class="environments-header">
              <h2 class="environments-title">Environments</h2>
              <StatusSummary environments={visibleEnvironments} />
              <span class="header-spacer"></span>
              {#if store.canChangeRerun && store.canChangeRerunBulk}
                <button
                  class="action-btn"
                  onclick={handleRerunAll}
                  disabled={rerunning || rerunCount === 0}
                >
                  ↺ Rerun {rerunCount} Filtered Test Plan{rerunCount !== 1
                    ? "s"
                    : ""}
                </button>
              {/if}
              {#if visibleEnvironments.length !== store.allEnvironments.length}
                <span class="filter-note">
                  Showing {visibleEnvironments.length} of {store.allEnvironments
                    .length}
                </span>
              {/if}
            </div>

            <div class="environment-list">
              {#if store.reviewsAvailable}
                <BulkEnvironmentSelectionControls
                  environments={visibleEnvironments}
                  {artefactId}
                  {store}
                />
              {/if}
              {#each visibleEnvironments as env (env.key)}
                <EnvironmentExpandable {env} {store} {artefactId} />
              {/each}
            </div>
          {/if}
        </div>
      </div>
    </div>
  </div>
{:else}
  <div class="error-state">
    <p>Failed to load artefact.</p>
  </div>
{/if}

<style>
  .artefact-page {
    display: flex;
    flex-direction: column;
  }

  /* ---- Loading / error ---- */
  .loading-page,
  .loading-inline,
  .empty-state,
  .error-state {
    display: flex;
    align-items: center;
    gap: 12px;
    color: var(--lp-color-text-muted);
    font-size: 0.875rem;
  }

  .loading-page {
    justify-content: center;
    padding: 64px 0;
    font-size: 1rem;
  }

  .loading-inline {
    padding: 24px 0;
  }

  .empty-state,
  .error-state {
    padding: 48px 0;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .spinner,
  .spinner-sm {
    border: 2px solid var(--lp-color-border-low-contrast);
    border-top-color: var(--lp-color-brand-default);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    flex-shrink: 0;
  }

  .spinner {
    width: 24px;
    height: 24px;
  }
  .spinner-sm {
    width: 16px;
    height: 16px;
  }

  /* ---- Layout ---- */
  .page-body {
    display: flex;
    flex-direction: column;
    gap: 0;
  }

  .sidebar-toggle {
    align-self: flex-start;
    background: none;
    border: 1px solid var(--lp-color-border-low-contrast);
    border-radius: 4px;
    padding: 4px 8px;
    cursor: pointer;
    color: var(--lp-color-text-muted);
    font-size: 1rem;
    margin-bottom: 8px;
  }

  .sidebar-toggle:hover {
    color: var(--lp-color-text-default);
    background: var(--lp-color-background-hover);
  }

  .content-area {
    display: flex;
    min-height: 0;
    gap: 0;
  }

  .main-content {
    flex: 1;
    min-width: 0;
    padding: 0 0 0 16px;
  }

  /* ---- Environments section ---- */
  .environments-header {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 8px;
  }

  .environments-title {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--lp-color-text-default);
  }

  .header-spacer {
    flex: 1;
  }

  .action-btn {
    background: none;
    border: 1px solid var(--lp-color-border-low-contrast);
    border-radius: 4px;
    padding: 4px 12px;
    font-size: 0.8rem;
    cursor: pointer;
    color: var(--lp-color-text-default);
    font-family: inherit;
  }

  .action-btn:hover {
    background: var(--lp-color-background-hover);
  }

  .action-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .filter-note {
    font-size: 0.8rem;
    color: var(--lp-color-text-muted);
  }

  .environment-list {
    display: flex;
    flex-direction: column;
    border-top: 1px solid var(--lp-color-border-low-contrast);
  }
</style>
