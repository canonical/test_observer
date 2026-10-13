<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import { RESULT_STATUS_COLORS } from '$lib/utils/status-colors';
  import type { PreviousTestResult } from '$lib/types/artefact-page';

  interface Props {
    previousResults: PreviousTestResult[];
    getHref: (previousResult: PreviousTestResult) => string;
  }

  let { previousResults, getHref }: Props = $props();
</script>

{#if previousResults.length > 0}
  <span class="history-dots">
    <!-- eslint-disable svelte/no-navigation-without-resolve -- the route is supplied by the caller. -->
    {#each previousResults as prev (prev.test_result_id)}
      <a
        href={getHref(prev)}
        class="dot"
        style="background: {RESULT_STATUS_COLORS[prev.status] ?? '#999'}"
        title="{prev.status} — {prev.version}"
        aria-label="Test result {prev.test_result_id}, {prev.status}, version {prev.version}"
      ></a>
    {/each}
    <!-- eslint-enable svelte/no-navigation-without-resolve -->
  </span>
{/if}

<style>
  .history-dots {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    flex-shrink: 0;
  }

  .dot {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    text-decoration: none;
    flex-shrink: 0;
    transition: transform 0.1s;
  }

  .dot:hover {
    transform: scale(1.4);
  }
</style>
