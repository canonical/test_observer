<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import { Badge } from '@canonical/svelte-ds-app-launchpad';
  import ExecutionStatusChip from './ExecutionStatusChip.svelte';
  import type { ArtefactEnvironment } from '$lib/types/artefact-page';
  import type { TestExecutionStatus } from '$lib/types/openapi';

  interface Props {
    environments: ArtefactEnvironment[];
  }

  let { environments }: Props = $props();

  const ORDERED: TestExecutionStatus[] = [
    'NOT_STARTED', 'NOT_TESTED', 'IN_PROGRESS', 'ENDED_PREMATURELY', 'FAILED', 'PASSED',
  ];

  const counts = $derived.by(() => {
    const c: Partial<Record<TestExecutionStatus, number>> = {};
    for (const env of environments) {
      const s = env.runsDescending[0]?.status;
      if (s) c[s] = (c[s] ?? 0) + 1;
    }
    return c;
  });
</script>

<div class="summary">
  {#each ORDERED as status (status)}
    {#if counts[status]}
      <span class="pair">
        <ExecutionStatusChip {status} />
        <Badge value={counts[status] ?? 0} />
      </span>
    {/if}
  {/each}
</div>

<style>
  .summary {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }

  .pair {
    display: flex;
    align-items: center;
    gap: 4px;
  }
</style>
