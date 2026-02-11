<script>
  import { onMount } from 'svelte';
  import { navigate } from 'svelte-routing';
  import { api } from '../services/api';
  import FilterIcon from '../components/FilterIcon.svelte';
  import ArtefactsTableView from '../components/ArtefactsTableView.svelte';
  import ArtefactsGridView from '../components/ArtefactsGridView.svelte';

  export let family;

  let viewMode = localStorage.getItem('viewMode') || 'grid';
  let showFilters = false;
  let searchQuery = '';
  let loading = false;
  let error = null;
  let artefacts = [];
  let selectedFilters = {};
  let expandedFilters = {};

  $: title = family.charAt(0).toUpperCase() + family.slice(1) + ' Update Verification';

  $: filteredArtefacts = (() => {
    let filtered = artefacts;

    // Apply search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(a =>
        a.name.toLowerCase().includes(query) ||
        a.version.toLowerCase().includes(query)
      );
    }

    // Apply selected filters
    for (const [filterName, selectedOptions] of Object.entries(selectedFilters)) {
      if (selectedOptions.length > 0) {
        filtered = filtered.filter(artefact => {
          const value = getArtefactFilterValue(artefact, filterName);
          return selectedOptions.includes(value);
        });
      }
    }

    return filtered;
  })();

  $: availableFilters = (() => {
    if (!artefacts.length) return [];

    const filterDefinitions = {
      snap: ['Assignee', 'Status', 'Due date', 'Risk'],
      deb: ['Assignee', 'Status', 'Due date', 'Series', 'Pocket'],
      charm: ['Assignee', 'Status', 'Due date', 'Risk'],
      image: ['OS type', 'Release', 'Owner', 'Assignee', 'Status', 'Due date']
    };

    const filtersForFamily = filterDefinitions[family] || [];

    return filtersForFamily.map(filterName => ({
      name: filterName,
      options: getFilterOptions(filterName)
    }));
  })();

  $: {
    // Save viewMode to localStorage
    localStorage.setItem('viewMode', viewMode);
  }

  $: {
    // Load artefacts when family changes
    if (family) {
      loadArtefacts();
    }
  }

  function navigateToArtefact(event) {
    const artefactId = event.detail;
    navigate(`/svelte_poc/${family}s/${artefactId}`);
  }

  async function loadArtefacts() {
    loading = true;
    error = null;

    try {
      artefacts = await api.fetchArtefacts(family);
      // Reset filters when family changes
      selectedFilters = {};
      expandedFilters = {};
    } catch (e) {
      error = 'Failed to load artefacts: ' + e.message;
      console.error('Failed to load artefacts:', e);
    } finally {
      loading = false;
    }
  }

  function getFilterOptions(filterName) {
    const options = new Set();
    artefacts.forEach(artefact => {
      const value = getArtefactFilterValue(artefact, filterName);
      if (value) options.add(value);
    });
    return Array.from(options).sort();
  }

  function getArtefactFilterValue(artefact, filterName) {
    switch (filterName) {
      case 'Assignee':
        return artefact.assignee?.name || 'N/A';
      case 'Status':
        return artefact.status === 'APPROVED' ? 'Approved'
             : artefact.status === 'MARKED_AS_FAILED' ? 'Rejected'
             : 'Undecided';
      case 'Due date':
        return getDueDateCategory(artefact.due_date);
      case 'Risk':
      case 'Pocket':
        return artefact.stage ? artefact.stage.charAt(0).toUpperCase() + artefact.stage.slice(1) : '';
      case 'Series':
        return artefact.series;
      case 'OS type':
        return artefact.os;
      case 'Release':
        return artefact.release;
      case 'Owner':
        return artefact.owner;
      default:
        return '';
    }
  }

  function getDueDateCategory(dueDate) {
    if (!dueDate) return 'No due date';

    const now = new Date();
    const due = new Date(dueDate);

    if (due < now) return 'Overdue';

    const daysDiff = Math.ceil((due - now) / (1000 * 60 * 60 * 24));
    if (daysDiff <= 7) return 'Within a week';
    return 'More than a week';
  }

  function toggleFilterOption(filterName, option, isSelected) {
    if (!selectedFilters[filterName]) {
      selectedFilters[filterName] = [];
    }

    if (isSelected) {
      if (!selectedFilters[filterName].includes(option)) {
        selectedFilters[filterName] = [...selectedFilters[filterName], option];
      }
    } else {
      selectedFilters[filterName] = selectedFilters[filterName].filter(o => o !== option);
    }

    // Trigger reactivity
    selectedFilters = { ...selectedFilters };
  }

  function isOptionSelected(filterName, option) {
    return selectedFilters[filterName]?.includes(option) || false;
  }

  function toggleFilterExpanded(filterName) {
    expandedFilters[filterName] = !expandedFilters[filterName];
    expandedFilters = { ...expandedFilters };
  }

  function isFilterExpanded(filterName) {
    // Default to expanded if not set
    return expandedFilters[filterName] !== false;
  }

  onMount(() => {
    loadArtefacts();
  });
</script>

<div class="dashboard">
  <div class="dashboard-header">
    <h1>{title}</h1>
    <div class="view-toggle">
      <button
        on:click={() => viewMode = 'list'}
        class="toggle-button"
        class:active={viewMode === 'list'}
        title="List view"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="8" y1="6" x2="21" y2="6"></line>
          <line x1="8" y1="12" x2="21" y2="12"></line>
          <line x1="8" y1="18" x2="21" y2="18"></line>
          <line x1="3" y1="6" x2="3.01" y2="6"></line>
          <line x1="3" y1="12" x2="3.01" y2="12"></line>
          <line x1="3" y1="18" x2="3.01" y2="18"></line>
        </svg>
      </button>
      <button
        on:click={() => viewMode = 'grid'}
        class="toggle-button"
        class:active={viewMode === 'grid'}
        title="Dashboard view"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="7" height="7"></rect>
          <rect x="14" y="3" width="7" height="7"></rect>
          <rect x="14" y="14" width="7" height="7"></rect>
          <rect x="3" y="14" width="7" height="7"></rect>
        </svg>
      </button>
    </div>
  </div>

  <div class="dashboard-body">
    <div class="filters-toggle">
      <button on:click={() => showFilters = !showFilters} class="filter-button">
        <FilterIcon />
      </button>
    </div>

    {#if showFilters}
      <div class="filters-panel">
        <h3>Filters</h3>

        <div class="filter-section">
          <input
            bind:value={searchQuery}
            type="text"
            placeholder="Search by name"
            class="search-input"
          />
        </div>

        {#each availableFilters as filter (filter.name)}
          <div class="filter-section">
            <div class="filter-header" on:click={() => toggleFilterExpanded(filter.name)}>
              <span class="filter-title">{filter.name}</span>
              <span class="expand-icon">{isFilterExpanded(filter.name) ? '▼' : '▶'}</span>
            </div>
            {#if isFilterExpanded(filter.name)}
              <div class="filter-options">
                {#each filter.options as option (option)}
                  <label class="filter-option">
                    <input
                      type="checkbox"
                      checked={isOptionSelected(filter.name, option)}
                      on:change={(e) => toggleFilterOption(filter.name, option, e.target.checked)}
                    />
                    <span>{option}</span>
                  </label>
                {/each}
              </div>
            {/if}
          </div>
        {/each}
      </div>
    {/if}

    <div class="content-area">
      {#if loading}
        <div class="loading">Loading artefacts...</div>
      {:else if error}
        <div class="error">{error}</div>
      {:else if viewMode === 'list'}
        <ArtefactsTableView
          artefacts={filteredArtefacts}
          {family}
          on:artefact-click={navigateToArtefact}
        />
      {:else}
        <ArtefactsGridView
          artefacts={filteredArtefacts}
          {family}
          on:artefact-click={navigateToArtefact}
        />
      {/if}
    </div>
  </div>
</div>

<style>
.dashboard {
  padding: 24px 0;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.dashboard-header h1 {
  font-size: 2.5em;
  font-weight: 300;
  color: #111;
}

.view-toggle {
  display: flex;
  gap: 0;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
  overflow: hidden;
}

.toggle-button {
  padding: 8px 12px;
  background: white;
  border: none;
  border-right: 1px solid #CDCDCD;
  cursor: pointer;
  color: #666;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.toggle-button:last-child {
  border-right: none;
}

.toggle-button:hover {
  background: #f7f7f7;
}

.toggle-button.active {
  background: transparent;
  color: #E95420;
  border-color: #E95420;
}

.dashboard-body {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.filters-toggle {
  flex-shrink: 0;
}

.filter-button {
  width: 40px;
  height: 40px;
  border: 1px solid #CDCDCD;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  transition: all 0.2s;
}

.filter-button:hover {
  background: #f7f7f7;
  border-color: #999;
}

.filters-panel {
  width: 280px;
  flex-shrink: 0;
  padding: 16px;
  background: #f7f7f7;
  border-radius: 4px;
}

.filters-panel h3 {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 12px;
}

.search-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
  font-size: 14px;
}

.search-input:focus {
  outline: none;
  border-color: #0E8420;
}

.filter-section {
  margin-top: 16px;
  border-top: 1px solid #CDCDCD;
  padding-top: 12px;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  padding: 4px 0;
  user-select: none;
}

.filter-header:hover {
  color: #0E8420;
}

.filter-header h4 {
  font-size: 14px;
  font-weight: 500;
  margin: 0;
}

.expand-icon {
  transition: transform 0.2s;
  color: #666;
}

.expand-icon.expanded {
  transform: rotate(90deg);
}

.filter-options {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filter-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-option input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.filter-option label {
  font-size: 13px;
  cursor: pointer;
  flex: 1;
}

.content-area {
  flex: 1;
  min-width: 0;
}

.loading,
.error {
  padding: 32px;
  text-align: center;
  color: #666;
}

.error {
  color: #C7162B;
}
</style>
