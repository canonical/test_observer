<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import type { Snippet } from 'svelte';

  interface Props {
    open?: boolean;
    title?: Snippet;
    children: Snippet;
    titleText?: string;
  }

  let { open = $bindable(false), title, children, titleText = '' }: Props = $props();
</script>

<details bind:open class="expandable">
  <summary class="expandable-summary">
    {#if title}
      {@render title()}
    {:else}
      <span class="expandable-title">{titleText}</span>
    {/if}
    <span class="expandable-chevron" class:open>&#9656;</span>
  </summary>
  <div class="expandable-content">
    {@render children()}
  </div>
</details>

<style>
  .expandable {
    border-bottom: 1px solid var(--lp-color-border-low-contrast);
  }

  .expandable-summary {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 8px;
    cursor: pointer;
    list-style: none;
    user-select: none;
    font-size: 0.875rem;
    font-weight: 500;
    color: inherit;
  }

  .expandable-summary::-webkit-details-marker {
    display: none;
  }

  .expandable-title {
    flex: 1;
  }

  .expandable-chevron {
    margin-left: auto;
    transition: transform 0.2s ease;
    color: var(--lp-color-text-muted);
    font-size: 14px;
    flex-shrink: 0;
  }

  .expandable-chevron.open {
    transform: rotate(90deg);
  }

  .expandable-content {
    padding: 0 8px 12px 24px;
  }
</style>
