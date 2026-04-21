<script lang="ts">
  import { page } from '$app/state';
  import Expandable from '$lib/components/ui/Expandable.svelte';
  import TestExecutionExpandable from './TestExecutionExpandable.svelte';
  import type { TestExecution } from '$lib/types/artefact-page';
  import type { ArtefactPageStore } from '$lib/stores/artefact-page.svelte';

  interface Props {
    planName: string;
    runs: TestExecution[];
    store: ArtefactPageStore;
    artefactId: number;
    family: string;
    isOnlyPlan: boolean;
  }

  let { planName, runs, store, artefactId, family, isOnlyPlan }: Props = $props();

  const targetExecutionId = $derived(
    page.url.searchParams.get('testExecutionId'),
  );

  let open = $state(false);

  // Auto-expand if only plan in env, or URL targets a run here
  $effect(() => {
    if (isOnlyPlan) {
      open = true;
    } else if (targetExecutionId && runs.some((r) => r.id === parseInt(targetExecutionId, 10))) {
      open = true;
    }
  });

  // Sorted descending by id (newest first)
  const sortedRuns = $derived([...runs].sort((a, b) => b.id - a.id));

  const latestRun = $derived(sortedRuns[0]);

  async function handleRerun() {
    if (latestRun) {
      await store.rerunExecutions([latestRun.id]);
    }
  }
</script>

<Expandable bind:open>
  {#snippet title()}
    <span class="plan-title">
      <span class="plan-name">{planName}</span>
      <span class="run-count">({sortedRuns.length} run{sortedRuns.length !== 1 ? 's' : ''})</span>
      <span class="spacer"></span>
      <button
        class="rerun-btn"
        onclick={(e) => { e.stopPropagation(); e.preventDefault(); handleRerun(); }}
        disabled={latestRun?.is_rerun_requested}
        title={latestRun?.is_rerun_requested ? 'Rerun already requested' : 'Rerun latest'}
      >
        <span class="material-symbols-outlined" style="font-size:16px">replay</span>
        {latestRun?.is_rerun_requested ? 'Rerun Requested' : 'Rerun'}
      </button>
    </span>
  {/snippet}

  <div class="runs-list">
    {#each sortedRuns as run, i (run.id)}
      <TestExecutionExpandable
        {run}
        runNumber={sortedRuns.length - i}
        isNewest={i === 0}
        {store}
        {artefactId}
        {family}
      />
    {/each}
  </div>
</Expandable>

<style>
  .plan-title {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
    min-width: 0;
  }

  .plan-name {
    font-size: 13px;
    font-weight: 600;
  }

  .run-count {
    font-size: 12px;
    color: #999;
  }

  .spacer {
    flex: 1;
  }

  .rerun-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    background: #fff;
    cursor: pointer;
    font-size: 12px;
    color: #555;
    font-family: inherit;
    white-space: nowrap;
  }

  .rerun-btn:hover:not(:disabled) {
    background: #f5f5f5;
    border-color: #999;
  }

  .rerun-btn:disabled {
    opacity: 0.5;
    cursor: default;
  }

  .runs-list {
    display: flex;
    flex-direction: column;
  }
</style>
