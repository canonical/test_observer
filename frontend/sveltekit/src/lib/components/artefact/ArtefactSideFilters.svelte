<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import { goto } from "$app/navigation";
  import { page } from "$app/state";
  import { Checkbox } from "@canonical/svelte-ds-app-launchpad";
  import type { ArtefactPageStore } from "$lib/stores/artefact-page.svelte";
  import {
    decodeFilterValues,
    latestPlanStatuses,
  } from "$lib/utils/artefact-filters";

  interface Props {
    store: ArtefactPageStore;
  }

  let { store }: Props = $props();

  function getParam(key: string): string[] {
    return decodeFilterValues(page.url.searchParams.get(key));
  }

  const selectedEnvironments = $derived(getParam("environment"));
  const selectedExecStatuses = $derived(getParam("execution_status"));
  const selectedReviewStatuses = $derived(getParam("review_status"));
  const selectedPlansLastRun = $derived(getParam("plans_last_run"));

  const environmentOptions = $derived(
    [...new Set(store.allEnvironments.map((e) => e.name))].sort(),
  );

  const execStatusOptions = $derived.by(() => {
    return [
      ...new Set(
        store.allEnvironments.flatMap((env) =>
          env.runsDescending.map((run) => run.status),
        ),
      ),
    ].sort();
  });

  const reviewStatusOptions = $derived.by(() => {
    const statuses = store.allEnvironments.flatMap((env) => {
      if (!env.review) return [];
      const d = env.review.review_decision;
      if (d.length === 0) return ["Undecided"];
      if (d.includes("REJECTED")) return ["Rejected"];
      return ["Approved"];
    });
    return [...new Set(statuses)].sort();
  });

  const plansLastRunOptions = $derived.by(() => {
    return [
      ...new Set(
        store.allEnvironments.flatMap((env) =>
          latestPlanStatuses(env.runsDescending),
        ),
      ),
    ].sort();
  });

  function navigateToSearch(url: URL) {
    goto(url, {
      replace: true,
      reset: false,
    });
  }

  function updateFilter(key: string, values: string[]) {
    const url = new URL(page.url.href);
    if (values.length === 0) {
      url.searchParams.delete(key);
    } else {
      url.searchParams.set(key, values.map(encodeURIComponent).join(","));
    }
    navigateToSearch(url);
  }

  function toggle(key: string, value: string, current: string[]) {
    const next = current.includes(value)
      ? current.filter((v) => v !== value)
      : [...current, value];
    updateFilter(key, next);
  }

  function toggleTriaged(value: string) {
    const url = new URL(page.url.href);
    if (url.searchParams.get("triaged") === value)
      url.searchParams.delete("triaged");
    else url.searchParams.set("triaged", value);
    navigateToSearch(url);
  }

  function clearAll() {
    const url = new URL(page.url.href);
    [
      "environment",
      "execution_status",
      "review_status",
      "plans_last_run",
      "triaged",
    ].forEach((k) => url.searchParams.delete(k));
    navigateToSearch(url);
  }

  const hasFilters = $derived(
    selectedEnvironments.length +
      selectedExecStatuses.length +
      selectedReviewStatuses.length +
      selectedPlansLastRun.length +
      (page.url.searchParams.has("triaged") ? 1 : 0) >
      0,
  );
</script>

<div class="side-filters">
  <div class="filters-header">
    <span class="filters-title">Filters</span>
    {#if hasFilters}
      <button class="clear-btn" onclick={clearAll}>Clear all</button>
    {/if}
  </div>

  {#if environmentOptions.length > 1}
    <fieldset class="filter-group">
      <legend class="filter-legend">Environment</legend>
      {#each environmentOptions as env (env)}
        <label class="filter-option">
          <Checkbox
            checked={selectedEnvironments.includes(env)}
            onchange={() => toggle("environment", env, selectedEnvironments)}
          />
          <span class="option-label">{env}</span>
        </label>
      {/each}
    </fieldset>
  {/if}

  {#if reviewStatusOptions.length > 1}
    <fieldset class="filter-group">
      <legend class="filter-legend">Review status</legend>
      {#each reviewStatusOptions as opt (opt)}
        <label class="filter-option">
          <Checkbox
            checked={selectedReviewStatuses.includes(opt)}
            onchange={() =>
              toggle("review_status", opt, selectedReviewStatuses)}
          />
          <span class="option-label">{opt}</span>
        </label>
      {/each}
    </fieldset>
  {/if}

  {#if plansLastRunOptions.length > 1}
    <fieldset class="filter-group">
      <legend class="filter-legend">Plans whose last run</legend>
      {#each plansLastRunOptions as opt (opt)}
        <label class="filter-option">
          <Checkbox
            checked={selectedPlansLastRun.includes(opt)}
            onchange={() => toggle("plans_last_run", opt, selectedPlansLastRun)}
          />
          <span class="option-label"
            >{opt.toLowerCase().replace(/_/g, " ")}</span
          >
        </label>
      {/each}
    </fieldset>
  {/if}

  {#if execStatusOptions.length > 1}
    <fieldset class="filter-group">
      <legend class="filter-legend">Test Execution Status</legend>
      {#each execStatusOptions as opt (opt)}
        <label class="filter-option">
          <Checkbox
            checked={selectedExecStatuses.includes(opt)}
            onchange={() =>
              toggle("execution_status", opt, selectedExecStatuses)}
          />
          <span class="option-label"
            >{opt.toLowerCase().replace(/_/g, " ")}</span
          >
        </label>
      {/each}
    </fieldset>
  {/if}

  <fieldset class="filter-group">
    <legend class="filter-legend">Test Execution Triaged</legend>
    {#each ["Yes", "No"] as val (val)}
      <label class="filter-option">
        <Checkbox
          checked={page.url.searchParams.get("triaged") === val}
          onchange={() => toggleTriaged(val)}
        />
        <span class="option-label">{val}</span>
      </label>
    {/each}
  </fieldset>
</div>

<style>
  .side-filters {
    display: flex;
    flex-direction: column;
    gap: 12px;
    color: var(--lp-color-text-default);
  }

  .filters-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .filters-title {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--lp-color-text-muted);
  }

  .clear-btn {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 0.75rem;
    color: var(--lp-color-brand-default);
    font-family: inherit;
    padding: 0;
  }

  .filter-group {
    border: none;
    padding: 0;
    margin: 0;
  }

  .filter-legend {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--lp-color-text-default);
    margin-bottom: 6px;
  }

  .filter-option {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.85rem;
    cursor: pointer;
    padding: 2px 0;
  }

  .option-label {
    color: var(--lp-color-text-default);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
</style>
