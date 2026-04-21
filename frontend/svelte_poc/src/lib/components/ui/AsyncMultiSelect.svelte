<script lang="ts">
  interface Option {
    label: string;
    value: string;
  }

  interface Props {
    fetchOptions: (query: string) => Promise<Option[]>;
    selected: string[];
    onchange: (selected: string[]) => void;
    minChars?: number;
    placeholder?: string;
    debounceMs?: number;
  }

  let {
    fetchOptions,
    selected,
    onchange,
    minChars = 2,
    placeholder = 'Type to search...',
    debounceMs = 300,
  }: Props = $props();

  let query = $state('');
  let options = $state<Option[]>([]);
  let loading = $state(false);
  let debounceTimer: ReturnType<typeof setTimeout> | null = null;

  function scheduleSearch(q: string) {
    if (debounceTimer) clearTimeout(debounceTimer);
    if (q.length < minChars) {
      options = [];
      return;
    }
    loading = true;
    debounceTimer = setTimeout(async () => {
      try {
        options = await fetchOptions(q);
      } catch {
        options = [];
      }
      loading = false;
    }, debounceMs);
  }

  function toggle(value: string) {
    if (selected.includes(value)) {
      onchange(selected.filter((s) => s !== value));
    } else {
      onchange([...selected, value]);
    }
  }

  function removeChip(value: string) {
    onchange(selected.filter((s) => s !== value));
  }

  const selectedLabels = $derived.by(() => {
    const map = new Map<string, string>();
    for (const opt of options) map.set(opt.value, opt.label);
    return map;
  });
</script>

<div class="async-multi-select">
  {#if selected.length > 0}
    <div class="chips">
      {#each selected as val (val)}
        <span class="chip">
          <span class="chip-text">{selectedLabels.get(val) ?? val}</span>
          <button class="chip-remove" onclick={() => removeChip(val)} title="Remove">×</button>
        </span>
      {/each}
    </div>
  {/if}

  <input
    type="text"
    bind:value={query}
    oninput={() => scheduleSearch(query)}
    {placeholder}
    class="search-input"
  />

  {#if loading}
    <div class="status">Loading...</div>
  {:else if query.length >= minChars && options.length === 0}
    <div class="status">No matches</div>
  {/if}

  {#if options.length > 0}
    <div class="options-list">
      {#each options as opt (opt.value)}
        <label class="option-row">
          <input
            type="checkbox"
            checked={selected.includes(opt.value)}
            onchange={() => toggle(opt.value)}
          />
          <span class="option-label">{opt.label}</span>
        </label>
      {/each}
    </div>
  {/if}
</div>

<style>
  .async-multi-select {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-bottom: 2px;
  }

  .chip {
    display: inline-flex;
    align-items: center;
    gap: 2px;
    background: #f0f0f0;
    border: 1px solid #ddd;
    border-radius: 12px;
    padding: 2px 8px;
    font-size: 12px;
    max-width: 200px;
  }

  .chip-text {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .chip-remove {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 14px;
    color: #888;
    padding: 0 2px;
    line-height: 1;
  }

  .chip-remove:hover {
    color: #333;
  }

  .search-input {
    padding: 6px 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 13px;
    outline: none;
    width: 100%;
    box-sizing: border-box;
  }

  .search-input:focus {
    border-color: #E95420;
  }

  .status {
    font-size: 12px;
    color: #999;
    padding: 4px;
  }

  .options-list {
    max-height: 180px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .option-row {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 4px;
    cursor: pointer;
    border-radius: 3px;
    font-size: 13px;
  }

  .option-row:hover {
    background: #f5f5f5;
  }

  .option-label {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
</style>
