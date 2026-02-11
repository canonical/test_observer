<script>
  import { tick } from 'svelte';

  export let title;
  export let placeholder = 'Type 2+ characters to search...';
  export let value = [];
  export let searchFunction;

  let isExpanded = false;
  let searchQuery = '';
  let suggestions = [];
  let isLoading = false;
  let error = null;
  let debounceTimeout = null;
  let searchInputElement;

  $: selectedArtefacts = value;

  // Auto-expand if there are initial selections
  $: if (selectedArtefacts.length > 0 && !isExpanded) {
    isExpanded = true;
  }

  async function toggle() {
    isExpanded = !isExpanded;
    if (isExpanded) {
      // Focus the search input when expanded
      await tick();
      if (searchInputElement) {
        searchInputElement.focus();
      }
    }
  }

  function handleSearchInput() {
    // Clear previous timeout
    if (debounceTimeout) {
      clearTimeout(debounceTimeout);
    }

    // Only search if we have 2+ characters
    if (searchQuery.trim().length < 2) {
      suggestions = [];
      return;
    }

    // Debounce the search
    debounceTimeout = setTimeout(() => {
      performSearch();
    }, 300); // 300ms debounce
  }

  async function performSearch() {
    isLoading = true;
    error = null;

    try {
      const results = await searchFunction(searchQuery.trim());
      suggestions = results || [];
    } catch (e) {
      error = 'Search failed';
      console.error('Search failed:', e);
      suggestions = [];
    } finally {
      isLoading = false;
    }
  }

  function selectArtefact(artefact) {
    if (!selectedArtefacts.includes(artefact)) {
      value = [...selectedArtefacts, artefact];
    }
    // Clear search after selection
    searchQuery = '';
    suggestions = [];
  }

  function deselectArtefact(artefact) {
    value = selectedArtefacts.filter(a => a !== artefact);
  }
</script>

<div class="search-multiselect">
  <!-- Collapsible header -->
  <div class="multiselect-header" on:click={toggle}>
    <span class="header-title">
      {title} ({selectedArtefacts.length} selected)
    </span>
    <span class="expand-icon">{isExpanded ? '▲' : '▼'}</span>
  </div>

  <!-- Expanded content -->
  {#if isExpanded}
    <div class="multiselect-content">
      <!-- Search input -->
      <input
        bind:this={searchInputElement}
        bind:value={searchQuery}
        on:input={handleSearchInput}
        type="text"
        class="search-input"
        placeholder={placeholder}
      />

      <!-- Loading state -->
      {#if isLoading}
        <div class="loading-state">
          <span class="loading-spinner"></span>
          <span>Searching...</span>
        </div>
      {/if}

      <!-- Error state -->
      {#if error}
        <div class="error-state">
          <span>Error loading suggestions</span>
        </div>
      {/if}

      <!-- Search results dropdown -->
      {#if suggestions.length > 0 && !isLoading}
        <div class="suggestions-dropdown">
          {#each suggestions as suggestion (suggestion)}
            <div
              class="suggestion-item"
              on:click={() => selectArtefact(suggestion)}
            >
              {suggestion}
            </div>
          {/each}
        </div>
      {/if}

      <!-- Selected items with checkboxes -->
      {#if selectedArtefacts.length > 0}
        <div class="selected-items">
          {#each selectedArtefacts as artefact (artefact)}
            <div class="selected-item">
              <label class="checkbox-label">
                <input
                  type="checkbox"
                  checked
                  on:change={() => deselectArtefact(artefact)}
                />
                <span class="item-name">{artefact}</span>
              </label>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
.search-multiselect {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.multiselect-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: white;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.multiselect-header:hover {
  background: #f7f7f7;
  border-color: #999;
}

.header-title {
  font-size: 14px;
  color: #111;
}

.expand-icon {
  color: #666;
  font-size: 12px;
}

.multiselect-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px;
  background: white;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
}

.search-input {
  padding: 8px 12px;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
  font-size: 14px;
}

.search-input:focus {
  outline: none;
  border-color: #0E8420;
}

.loading-state,
.error-state {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  font-size: 14px;
  color: #666;
}

.loading-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #0E8420;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-state {
  color: #C7162B;
}

.suggestions-dropdown {
  max-height: 250px;
  overflow-y: auto;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
  background: white;
}

.suggestion-item {
  padding: 8px 12px;
  cursor: pointer;
  font-size: 14px;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.2s;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-item:hover {
  background: #f7f7f7;
}

.selected-items {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.selected-item {
  display: flex;
  align-items: center;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #111;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  cursor: pointer;
}

.item-name {
  user-select: none;
}
</style>
