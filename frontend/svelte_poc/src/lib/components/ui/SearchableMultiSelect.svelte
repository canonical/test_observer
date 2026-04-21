<script lang="ts">
  interface Props {
    options: string[];
    selected: string[];
    onchange: (selected: string[]) => void;
    placeholder?: string;
  }

  let { options, selected, onchange, placeholder = 'Search...' }: Props = $props();

  let search = $state('');

  const filtered = $derived(
    options.filter((o) => o.toLowerCase().includes(search.toLowerCase())),
  );

  function toggle(option: string) {
    if (selected.includes(option)) {
      onchange(selected.filter((s) => s !== option));
    } else {
      onchange([...selected, option]);
    }
  }
</script>

<div class="searchable-multi-select">
  <input
    type="text"
    bind:value={search}
    {placeholder}
    class="search-input"
  />
  <div class="options-list">
    {#each filtered as option (option)}
      <label class="option-row">
        <input
          type="checkbox"
          checked={selected.includes(option)}
          onchange={() => toggle(option)}
        />
        <span class="option-label">{option}</span>
      </label>
    {/each}
    {#if filtered.length === 0}
      <span class="no-results">No matches</span>
    {/if}
  </div>
</div>

<style>
  .searchable-multi-select {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .search-input {
    padding: 6px 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 13px;
    outline: none;
  }

  .search-input:focus {
    border-color: #E95420;
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
    padding: 4px 4px;
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

  .no-results {
    color: #999;
    font-size: 12px;
    padding: 4px;
  }
</style>
