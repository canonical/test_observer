<script lang="ts">
  import Expandable from '$lib/components/ui/Expandable.svelte';
  import StatusIcon from '$lib/components/ui/StatusIcon.svelte';
  import { RESULT_STATUS_ICONS } from '$lib/utils/status-icons';
  import TestResultExpandable from './TestResultExpandable.svelte';
  import type { TestResultStatus } from '$lib/types/artefact-page';
  import type { ArtefactPageStore } from '$lib/stores/artefact-page.svelte';
  import { page } from '$app/state';

  interface Props {
    executionId: number;
    status: TestResultStatus;
    store: ArtefactPageStore;
    artefactId: number;
    family: string;
  }

  let { executionId, status, store, artefactId, family }: Props = $props();

  const allResults = $derived(store.getTestResults(executionId));

  const results = $derived.by(() => {
    if (!allResults || allResults === 'loading') return [];
    return allResults.filter((r) => r.status === status);
  });

  const targetResultId = $derived(
    page.url.searchParams.get('testResultId'),
  );

  let open = $state(false);

  // Auto-expand if URL targets a result in this group
  $effect(() => {
    if (targetResultId && results.some((r) => r.id === parseInt(targetResultId, 10))) {
      open = true;
    }
  });

  // Lazy load results when opened
  $effect(() => {
    if (open) {
      store.fetchTestResults(executionId);
    }
  });

  const info = $derived(RESULT_STATUS_ICONS[status]);
</script>

{#if allResults === 'loading'}
  <div class="loading-row">
    <span class="material-symbols-outlined spin" style="font-size:16px">progress_activity</span>
    Loading {info.label.toLowerCase()} results...
  </div>
{:else if results.length > 0}
  <Expandable bind:open>
    {#snippet title()}
      <span class="group-title">
        <StatusIcon {status} size="18px" />
        <span>{info.label} {results.length}</span>
      </span>
    {/snippet}

    <div class="results-list">
      {#each results as result (result.id)}
        <TestResultExpandable {result} {store} {artefactId} {family} />
      {/each}
    </div>
  </Expandable>
{/if}

<style>
  .loading-row {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: #666;
    padding: 4px 0;
  }

  .spin {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  .group-title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    font-weight: 600;
  }

  .results-list {
    display: flex;
    flex-direction: column;
  }
</style>
