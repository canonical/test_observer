<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import { DescriptionList } from '@canonical/svelte-ds-app-launchpad';
  import Expandable from './Expandable.svelte';

  interface Props {
    metadata: Record<string, string[]>;
  }

  let { metadata }: Props = $props();

  const entries = $derived(Object.entries(metadata));
  let open = $state(false);
</script>

{#if entries.length > 0}
  <Expandable bind:open>
    {#snippet title()}
      <span class="section-title">Execution Metadata</span>
    {/snippet}

    <DescriptionList layout="list">
      {#each entries as [key, values] (key)}
        <DescriptionList.Item name={key}>{values.join(', ')}</DescriptionList.Item>
      {/each}
    </DescriptionList>
  </Expandable>
{/if}

<style>
  .section-title {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--lp-color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }
</style>
