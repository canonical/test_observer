<script lang="ts">
  import { base } from '$app/paths';
  import { RESULT_STATUS_ICONS } from '$lib/utils/status-icons';
  import type { PreviousTestResult } from '$lib/types/artefact-page';

  interface Props {
    previousResults: PreviousTestResult[];
    family: string;
  }

  let { previousResults, family }: Props = $props();
</script>

{#if previousResults.length > 0}
  <span class="history-dots">
    {#each previousResults as prev (prev.test_result_id)}
      <a
        href="{base}/{family}/{prev.artefact_id}?testExecutionId={prev.test_execution_id}&testResultId={prev.test_result_id}"
        class="dot"
        style="background: {RESULT_STATUS_ICONS[prev.status]?.color ?? '#999'}"
        title="{prev.status} — {prev.version}"
      ></a>
    {/each}
  </span>
{/if}

<style>
  .history-dots {
    display: inline-flex;
    align-items: center;
    gap: 3px;
  }

  .dot {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    text-decoration: none;
    flex-shrink: 0;
  }

  .dot:hover {
    transform: scale(1.3);
  }
</style>
