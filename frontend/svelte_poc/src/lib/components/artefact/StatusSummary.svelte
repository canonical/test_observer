<script lang="ts">
  import StatusIcon from '$lib/components/ui/StatusIcon.svelte';
  import { EXECUTION_STATUS_ICONS } from '$lib/utils/status-icons';
  import type { ArtefactEnvironment, TestExecutionStatus } from '$lib/types/artefact-page';

  interface Props {
    environments: ArtefactEnvironment[];
  }

  let { environments }: Props = $props();

  const statusCounts = $derived.by(() => {
    const counts: Partial<Record<TestExecutionStatus, number>> = {};
    for (const env of environments) {
      const newest = env.runsDescending[0];
      if (newest) {
        counts[newest.status] = (counts[newest.status] ?? 0) + 1;
      }
    }
    return counts;
  });

  const orderedStatuses: TestExecutionStatus[] = [
    'NOT_STARTED',
    'NOT_TESTED',
    'IN_PROGRESS',
    'ENDED_PREMATURELY',
    'FAILED',
    'PASSED',
  ];
</script>

<div class="status-summary">
  {#each orderedStatuses as status (status)}
    <span class="status-pair">
      <StatusIcon {status} size="18px" />
      <span class="count">{statusCounts[status]}</span>
    </span>
  {/each}
</div>

<style>
  .status-summary {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .status-pair {
    display: flex;
    align-items: center;
    gap: 3px;
  }

  .count {
    font-size: 13px;
    font-weight: 600;
    color: #333;
  }
</style>
