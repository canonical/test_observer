<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: GPL-3.0-only
-->
<script lang="ts">
  import { page } from '$app/state';
  import { goto } from '$app/navigation';
  import { Button } from '@canonical/svelte-ds-app-launchpad';
  import { ChevronLeftIcon, ChevronRightIcon } from '@canonical/svelte-icons';

  let {
    currentPage,
    totalPages,
    totalItems,
    pageSize,
  }: {
    currentPage: number;
    totalPages: number;
    totalItems: number;
    pageSize: number;
  } = $props();

  const firstItem = $derived(totalItems === 0 ? 0 : (currentPage - 1) * pageSize + 1);
  const lastItem = $derived(Math.min(currentPage * pageSize, totalItems));

  // Mirror the active page so the number input's up/down spinners step from it,
  // and re-sync whenever navigation changes the current page.
  let jumpValue = $derived<number | null>(currentPage);

  function goToPage(target: number) {
    const url = new URL(page.url);
    if (target <= 1) {
      url.searchParams.delete('page');
    } else {
      url.searchParams.set('page', String(target));
    }
    // Derived from page.url, so the base path is already applied.
    // eslint-disable-next-line svelte/no-navigation-without-resolve
    goto(url, { replaceState: true, noScroll: true });
  }

  function submitJump(event: SubmitEvent) {
    event.preventDefault();
    if (jumpValue === null || !Number.isFinite(jumpValue)) return;
    goToPage(Math.min(Math.max(1, Math.trunc(jumpValue)), totalPages));
  }

  // Build a compact list of page numbers with gaps ('…') for large ranges.
  const pageItems = $derived.by<(number | 'gap')[]>(() => {
    if (totalPages <= 7) {
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }
    const items: (number | 'gap')[] = [1];
    const start = Math.max(2, currentPage - 1);
    const end = Math.min(totalPages - 1, currentPage + 1);
    if (start > 2) items.push('gap');
    for (let i = start; i <= end; i++) items.push(i);
    if (end < totalPages - 1) items.push('gap');
    items.push(totalPages);
    return items;
  });
</script>

{#if totalPages > 1}
  <nav class="pagination" aria-label="Pagination">
    <span class="range" aria-live="polite">
      Showing {firstItem}–{lastItem} of {totalItems}
    </span>
    <div class="controls">
      <Button
        density="dense"
        severity="base"
        disabled={currentPage <= 1}
        aria-label="Previous page"
        onclick={() => goToPage(currentPage - 1)}
      >
        {#snippet iconLeft()}<ChevronLeftIcon />{/snippet}
        Previous
      </Button>

      <ul class="pages">
        {#each pageItems as item, i (i)}
          {#if item === 'gap'}
            <li class="gap" aria-hidden="true">…</li>
          {:else}
            <li>
              <Button
                density="dense"
                severity={item === currentPage ? 'brand' : 'base'}
                aria-label="Page {item}"
                aria-current={item === currentPage ? 'page' : undefined}
                onclick={() => goToPage(item)}
              >
                {item}
              </Button>
            </li>
          {/if}
        {/each}
      </ul>

      <Button
        density="dense"
        severity="base"
        disabled={currentPage >= totalPages}
        aria-label="Next page"
        onclick={() => goToPage(currentPage + 1)}
      >
        {#snippet iconRight()}<ChevronRightIcon />{/snippet}
        Next
      </Button>
    </div>

    <form class="jump" onsubmit={submitJump}>
      <label for="pagination-jump">Go to page</label>
      <input
        id="pagination-jump"
        class="jump-input"
        type="number"
        min="1"
        max={totalPages}
        inputmode="numeric"
        bind:value={jumpValue}
      />
      <span class="jump-total">of {totalPages}</span>
      <Button
        type="submit"
        density="dense"
        severity="base"
        disabled={jumpValue === null || jumpValue === currentPage}
      >
        Go
      </Button>
    </form>
  </nav>
{/if}

<style>
  .pagination {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 0.75rem;
    padding: 0.75rem 0;
  }

  .range {
    font-size: 0.875rem;
    color: var(--lp-color-text-muted);
  }

  .controls {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .pages {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .gap {
    padding: 0 0.25rem;
    color: var(--lp-color-text-muted);
  }

  .jump {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    color: var(--lp-color-text-muted);
  }

  .jump-input {
    width: 4rem;
    padding: 0.25rem 0.5rem;
    font: inherit;
    color: var(--lp-color-text-default);
    background: var(--lp-color-background-default);
    border: 1px solid var(--lp-color-border-default, #ccc);
    border-radius: 0.25rem;
  }

  .jump-input:focus-visible {
    outline: 2px solid var(--lp-color-brand-default);
    outline-offset: 1px;
  }

  .jump-total {
    white-space: nowrap;
  }
</style>
