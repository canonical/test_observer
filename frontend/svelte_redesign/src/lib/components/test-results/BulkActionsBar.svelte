<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">


  interface Props {
    selectedCount: number;
    onattachissue: () => void;
    onrequestreruns: () => void;
    ondeselectall: () => void;
  }

  const { selectedCount, onattachissue, onrequestreruns, ondeselectall }: Props = $props();
</script>

{#if selectedCount > 0}
  <div class="ds bulk-actions-bar" role="toolbar" aria-label="Bulk actions">
    <span class="ds bulk-actions-bar__count">
      {selectedCount} item{selectedCount === 1 ? "" : "s"} selected
    </span>
    <div class="ds bulk-actions-bar__actions" role="group" aria-label="Bulk action buttons">
      <button type="button" onclick={onattachissue}>Attach Issue</button>
      <button type="button" onclick={onrequestreruns}>Request Rerun</button>
      <button type="button" onclick={ondeselectall}>Deselect All</button>
    </div>
  </div>
{/if}

<style>
  .ds.bulk-actions-bar {
    position: sticky;
    bottom: 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 0.75rem 1rem;
    background: var(--color-background-alt, #f7f7f7);
    border-top: 2px solid var(--color-border, #d9d9d9);
    z-index: 10;
  }

  .ds.bulk-actions-bar__count {
    font-weight: 600;
    font-size: 0.875rem;
  }

  .ds.bulk-actions-bar__actions {
    display: flex;
    gap: 0.5rem;
  }
</style>
