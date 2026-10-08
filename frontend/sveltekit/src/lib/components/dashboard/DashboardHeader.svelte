<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: GPL-3.0-only
-->
<script lang="ts">
  import type { Family } from '$lib/types';
  import { Button } from '@canonical/svelte-ds-app-launchpad';
  import { CheckmarkIcon, CloseIcon, ShareIcon } from '@canonical/svelte-icons';
  import { errorStore } from '$lib/stores/error.svelte';

  let {
    family,
    count,
    filtered,
    onClear,
    onShare,
  }: {
    family: Family;
    count: number;
    filtered: boolean;
    onClear: () => void;
    onShare: () => string;
  } = $props();

  const title = $derived(family.friendly_name);
  const countText = $derived(`${count} artifacts`);

  let copied = $state(false);
  let copiedTimer: ReturnType<typeof setTimeout> | undefined;

  async function share() {
    const url = onShare();
    try {
      await navigator.clipboard.writeText(url);
    } catch {
      // Clipboard access needs a secure context and user permission; neither is
      // guaranteed, so say so rather than silently doing nothing.
      errorStore.set(`Could not copy the link. You can copy it from the address bar: ${url}`);
      return;
    }
    copied = true;
    clearTimeout(copiedTimer);
    copiedTimer = setTimeout(() => (copied = false), 2000);
  }

  $effect(() => () => {
    clearTimeout(copiedTimer);
  });
</script>

<header class="dashboard-header">
  <div class="title-group">
    <h1>{title}</h1>
    <span class="count">{countText}</span>
  </div>

  <div class="actions">
    <Button
      density="dense"
      severity="base"
      disabled={!filtered}
      onclick={onClear}
      aria-label="Clear all filters and sorting"
    >
      {#snippet iconLeft()}<CloseIcon />{/snippet}
      Clear filters
    </Button>
    <Button density="dense" severity="base" onclick={share} aria-label="Copy a link to this view">
      {#snippet iconLeft()}{#if copied}<CheckmarkIcon />{:else}<ShareIcon />{/if}{/snippet}
      {copied ? 'Link copied' : 'Share'}
    </Button>
  </div>
</header>

<style>
  .dashboard-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .title-group {
    display: flex;
    align-items: baseline;
    gap: 0.75rem;
  }

  h1 {
    font-size: 1.5rem;
    font-weight: 400;
    margin: 0;
  }

  .count {
    font-size: 0.875rem;
    color: var(--lp-color-text-muted);
  }

  .actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-shrink: 0;
  }
</style>
