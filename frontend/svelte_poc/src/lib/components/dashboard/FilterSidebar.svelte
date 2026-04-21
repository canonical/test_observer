<script lang="ts">
  import type { Artefact, Family } from '$lib/types';
  import { FAMILY_FILTERS, type FilterKey } from '$lib/types/filters';
  import { page } from '$app/state';
  import { goto } from '$app/navigation';
  import { fly } from 'svelte/transition';

  let { artefacts, family, visible }: {
    artefacts: Artefact[];
    family: Family;
    visible: boolean;
  } = $props();

  const filterDefs = $derived(FAMILY_FILTERS[family]);

  const availableOptions = $derived.by(() => {
    const result: Record<string, string[]> = {};
    for (const def of filterDefs) {
      const values = new Set<string>();
      for (const a of artefacts) {
        values.add(def.extract(a));
      }
      result[def.key] = [...values].sort();
    }
    return result;
  });

  let searchInput = $state(page.url.searchParams.get('q') ?? '');
  let pendingFilters = $state<Record<string, Set<string>>>({});

  $effect(() => {
    const filters: Record<string, Set<string>> = {};
    for (const def of filterDefs) {
      const vals = page.url.searchParams.getAll(def.key);
      filters[def.key] = new Set(vals);
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
    // Clear existing filter params
    for (const def of filterDefs) {
      url.searchParams.delete(def.key);
    }
    url.searchParams.delete('q');
    // Set search
    if (searchInput.trim()) {
      url.searchParams.set('q', searchInput.trim());
    }
    // Set filters
    for (const [key, values] of Object.entries(pendingFilters)) {
      for (const v of values) {
        url.searchParams.append(key, v);
      }
    }
    goto(url.toString(), { replaceState: true, noScroll: true });
  }

  // Expandable sections
  let expanded = $state<Record<string, boolean>>(
    Object.fromEntries(filterDefs.map(d => [d.key, true]))
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
      <input
        type="search"
        placeholder="Search by name"
        bind:value={searchInput}
        class="search-input"
      />
    </div>

    {#each filterDefs as def (def.key)}
      <fieldset class="filter-group">
        <legend>
          <button class="expand-toggle" onclick={() => toggleExpand(def.key)}>
            <span class="arrow" class:collapsed={!expanded[def.key]}>▾</span>
            {def.key}
          </button>
        </legend>
        {#if expanded[def.key]}
          <div class="options">
            {#each availableOptions[def.key] ?? [] as option}
              <label class="option-row" title={option}>
                <input
                  type="checkbox"
                  checked={isChecked(def.key, option)}
                  onchange={() => toggleOption(def.key, option)}
                />
                <span class="option-label">{optionLabel(option)}</span>
              </label>
            {/each}
          </div>
        {/if}
      </fieldset>
    {/each}

    <button class="apply-btn" onclick={apply}>Apply</button>
  </aside>
{/if}

<style>
  .filter-sidebar {
    width: 300px;
    flex-shrink: 0;
    padding: 16px;
    overflow-y: auto;
    border-right: 1px solid #e0e0e0;
  }

  .search-wrapper {
    margin-bottom: 16px;
  }

  .search-input {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 0.9rem;
    font-family: inherit;
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

  .option-row {
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

  .apply-btn {
    display: block;
    width: 100%;
    padding: 10px;
    background: #333;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 0.95rem;
    font-weight: 500;
    cursor: pointer;
    font-family: inherit;
    margin-top: 8px;
  }

  .apply-btn:hover {
    background: #444;
  }
</style>
