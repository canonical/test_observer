<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: GPL-3.0-only
-->
<script lang="ts">
  import type { Family } from '$lib/types';

  let {
    family,
    filteredCount,
    totalCount,
  }: {
    family: Family;
    filteredCount: number;
    totalCount: number;
  } = $props();

  const title = $derived(family.friendly_name);
  const countText = $derived(
    filteredCount === totalCount
      ? `${totalCount} artifacts`
      : `${filteredCount} of ${totalCount} artifacts`
  );
</script>

<header class="dashboard-header">
  <div class="title-group">
    <h1>{title}</h1>
    <span class="count">{countText}</span>
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
</style>
