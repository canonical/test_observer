<script lang="ts">
  import { page } from '$app/state';
  import Expandable from '$lib/components/ui/Expandable.svelte';
  import StatusIcon from '$lib/components/ui/StatusIcon.svelte';
  import EventLogExpandable from './EventLogExpandable.svelte';
  import ExecutionMetadataExpandable from './ExecutionMetadataExpandable.svelte';
  import TestResultsGroup from './TestResultsGroup.svelte';
  import AddTestResultDialog from './AddTestResultDialog.svelte';
  import type { TestExecution } from '$lib/types/artefact-page';
  import type { ArtefactPageStore } from '$lib/stores/artefact-page.svelte';
  import { userStore } from '$lib/stores/user.svelte';

  interface Props {
    run: TestExecution;
    runNumber: number;
    isNewest: boolean;
    store: ArtefactPageStore;
    artefactId: number;
    family: string;
  }

  let { run, runNumber, isNewest, store, artefactId, family }: Props = $props();

  const targetExecutionId = $derived(
    page.url.searchParams.get('testExecutionId'),
  );

  let open = $state(false);

  // Auto-expand newest run or URL match
  $effect(() => {
    if (isNewest || (targetExecutionId && parseInt(targetExecutionId, 10) === run.id)) {
      open = true;
    }
  });

  const isManualTesting = $derived(run.test_plan === 'Manual Testing');
  const isCompleted = $derived(run.status === 'PASSED' || run.status === 'FAILED');
  const showResults = $derived(isCompleted || isManualTesting);

  let addResultOpen = $state(false);

  // Lazy load when opened and showing results
  $effect(() => {
    if (open && showResults) {
      store.fetchTestResults(run.id);
    }
  });
</script>

<Expandable bind:open>
  {#snippet title()}
    <span class="exec-title">
      <StatusIcon status={run.status} size="18px" />
      <span class="run-label">Run {runNumber}</span>
      <span class="spacer"></span>
      {#if run.ci_link}
        <a href={run.ci_link} target="_blank" rel="noopener" class="link-chip" onclick={(e) => e.stopPropagation()}>
          CI
        </a>
      {/if}
      {#if run.c3_link}
        <a href={run.c3_link} target="_blank" rel="noopener" class="link-chip" onclick={(e) => e.stopPropagation()}>
          C3
        </a>
      {/if}
      {#each run.relevant_links as rl (rl.id)}
        <a href={rl.url} target="_blank" rel="noopener" class="link-chip" onclick={(e) => e.stopPropagation()}>
          {rl.label}
        </a>
      {/each}
      {#if isManualTesting && userStore.isLoggedIn}
        <button
          class="add-result-btn"
          onclick={(e) => { e.stopPropagation(); e.preventDefault(); addResultOpen = true; }}
        >
          <span class="material-symbols-outlined" style="font-size:16px">add</span>
          Add Test Result
        </button>
      {/if}
    </span>
  {/snippet}

  <div class="exec-content">
    {#if !isManualTesting}
      <EventLogExpandable executionId={run.id} {store} {isCompleted} />
      <ExecutionMetadataExpandable metadata={run.execution_metadata} />
    {/if}

    {#if showResults}
      <TestResultsGroup executionId={run.id} status="FAILED" {store} {artefactId} {family} />
      <TestResultsGroup executionId={run.id} status="PASSED" {store} {artefactId} {family} />
      <TestResultsGroup executionId={run.id} status="SKIPPED" {store} {artefactId} {family} />
    {/if}
  </div>
</Expandable>

<AddTestResultDialog
  executionId={run.id}
  {artefactId}
  {store}
  open={addResultOpen}
  onclose={() => (addResultOpen = false)}
/>

<style>
  .exec-title {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
    min-width: 0;
  }

  .run-label {
    font-size: 13px;
    font-weight: 600;
    white-space: nowrap;
  }

  .spacer {
    flex: 1;
  }

  .link-chip {
    display: inline-flex;
    align-items: center;
    padding: 1px 8px;
    border: 1px solid #ddd;
    border-radius: 10px;
    font-size: 11px;
    color: #0066cc;
    text-decoration: none;
    white-space: nowrap;
  }

  .link-chip:hover {
    background: #f0f7ff;
    border-color: #0066cc;
  }

  .add-result-btn {
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

  .add-result-btn:hover {
    background: #f5f5f5;
    border-color: #999;
  }

  .exec-content {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
</style>
