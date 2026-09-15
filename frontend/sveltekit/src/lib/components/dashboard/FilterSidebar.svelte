<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: GPL-3.0-only
-->
<script lang="ts">
  import type { Artefact, Family } from '$lib/types';
  import { filterValue } from '$lib/artefactMetadata';
  import { page } from '$app/state';
  import { goto } from '$app/navigation';
  import { fly } from 'svelte/transition';
  import { SearchBox, Checkbox, Button } from '@canonical/svelte-ds-app-launchpad';

  let {
    artefacts,
    family,
    visible,
  }: {
    artefacts: Artefact[];
    family: Family;
    visible: boolean;
  } = $props();

  const filterDefs = $derived(family.filters);

  const availableOptions = $derived.by(() => {
    const result: Record<string, string[]> = {};
    for (const def of filterDefs) {
      const values = new Set<string>();
      for (const a of artefacts) {
        values.add(filterValue(a, def));
      }
      result[def.label] = [...values].sort();
    }
    return result;
  });

  let searchInput = $state(page.url.searchParams.get('q') ?? '');
  let pendingFilters = $state<Record<string, Set<string>>>({});

  $effect(() => {
    const filters: Record<string, Set<string>> = {};
    for (const def of filterDefs) {
      const vals = page.url.searchParams.getAll(def.label);
      filters[def.label] = new Set(vals);
    }
    pendingFilters = filters;
    searchInput = page.url.searchParams.get('q') ?? '';
  });

  function toggleOption(key: string, value: string) {
    const set = pendingFilters[key] ?? new Set();
    if (set.has(value)) {
      set.delete(value);
    } else {
      set.add(value);
    }
    pendingFilters = { ...pendingFilters, [key]: set };
  }

  function isChecked(key: string, value: string): boolean {
    return pendingFilters[key]?.has(value) ?? false;
  }

  function apply() {
    const url = new URL(page.url);
    for (const def of filterDefs) {
      url.searchParams.delete(def.label);
    }
    url.searchParams.delete('q');
    if (searchInput.trim()) {
      url.searchParams.set('q', searchInput.trim());
    }
    for (const [key, values] of Object.entries(pendingFilters)) {
      for (const v of values) {
        url.searchParams.append(key, v);
      }
    }
    goto(url.toString(), { replaceState: true, noScroll: true });
  }

  let expanded = $state<Record<string, boolean>>(
    Object.fromEntries(filterDefs.map((d) => [d.label, true]))
  );

  function toggleExpand(key: string) {
    expanded = { ...expanded, [key]: !expanded[key] };
  }

  function optionLabel(value: string): string {
    if (value.includes('::')) {
      return value.split('::').pop() ?? value;
    }
    return value;
  }
</script>

{#if visible}
  <aside class="filter-sidebar" transition:fly={{ x: -300, duration: 200 }}>
    <div class="search-wrapper">
      <SearchBox aria-label="Search by name" bind:value={searchInput} />
    </div>

    {#each filterDefs as def (def.label)}
      <fieldset class="filter-group">
        <legend>
          <button class="expand-toggle" onclick={() => toggleExpand(def.label)}>
            <span class="arrow" class:collapsed={!expanded[def.label]}>▾</span>
            {def.label}
          </button>
        </legend>
        {#if expanded[def.label]}
          <div class="options">
            {#each availableOptions[def.label] ?? [] as option}
              <label class="filter-option">
                <Checkbox
                  checked={isChecked(def.label, option)}
                  onchange={() => toggleOption(def.label, option)}
                />
                <span class="option-label">{optionLabel(option)}</span>
              </label>
            {/each}
          </div>
        {/if}
      </fieldset>
    {/each}

    <Button severity="brand" onclick={apply}>Apply</Button>
  </aside>
{/if}

<style>
  .filter-sidebar {
    width: 300px;
    flex-shrink: 0;
    padding: 16px;
    overflow-y: auto;
    overflow-x: hidden;
    border-right: 1px solid var(--lp-color-border-low-contrast);
  }

  .search-wrapper {
    margin-bottom: 16px;
  }

  /* The SearchBox component does not constrain its internal <input> to the parent
     width by default. Force it to fill the sidebar so it does not overflow. */
  .search-wrapper :global(input) {
    width: 100%;
    box-sizing: border-box;
  }

  .filter-group {
    border: none;
    padding: 0;
    margin: 0 0 16px;
  }

  .filter-group legend {
    padding: 0;
    width: 100%;
  }

  .expand-toggle {
    display: flex;
    align-items: center;
    gap: 4px;
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1rem;
    font-weight: 600;
    font-family: inherit;
    padding: 4px 0;
    width: 100%;
    text-align: left;
    /* UA stylesheet sets `color: buttontext` on <button> which overrides inherited
       values. An explicit `color: inherit` in the author stylesheet allows our
       color scheme to supercede the UA rule. */
    color: inherit;
  }

  .arrow {
    transition: transform 0.15s;
    font-size: 0.8rem;
  }

  .arrow.collapsed {
    transform: rotate(-90deg);
  }

  .options {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 8px 0 0 4px;
  }

  .filter-option {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.85rem;
    cursor: pointer;
  }

  .option-label {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
</style>
