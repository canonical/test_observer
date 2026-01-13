<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1>{{ title }}</h1>
      <div class="view-toggle">
        <button
          @click="viewMode = 'list'"
          :class="['toggle-button', { active: viewMode === 'list' }]"
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
          @click="viewMode = 'grid'"
          :class="['toggle-button', { active: viewMode === 'grid' }]"
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
        <button @click="showFilters = !showFilters" class="filter-button">
          <svg class="filter-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
          </svg>
        </button>
      </div>

      <div v-if="showFilters" class="filters-panel">
        <h3>Filters</h3>

        <div class="filter-section">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search by name"
            class="search-input"
          />
        </div>

        <div v-for="filter in availableFilters" :key="filter.name" class="filter-section">
          <div class="filter-header" @click="toggleFilterExpanded(filter.name)">
            <span class="filter-title">{{ filter.name }}</span>
            <span class="expand-icon">{{ isFilterExpanded(filter.name) ? '▼' : '▶' }}</span>
          </div>
          <div v-if="isFilterExpanded(filter.name)" class="filter-options">
            <label
              v-for="option in filter.options"
              :key="option"
              class="filter-option"
            >
              <input
                type="checkbox"
                :checked="isOptionSelected(filter.name, option)"
                @change="toggleFilterOption(filter.name, option, $event.target.checked)"
              />
              <span>{{ option }}</span>
            </label>
          </div>
        </div>
      </div>

      <div class="content-area">
        <div v-if="loading" class="loading">Loading artefacts...</div>
        <div v-else-if="error" class="error">{{ error }}</div>
        <ArtefactsTableView
          v-else-if="viewMode === 'list'"
          :artefacts="filteredArtefacts"
          :family="family"
          @artefact-click="navigateToArtefact"
        />
        <ArtefactsGridView
          v-else
          :artefacts="filteredArtefacts"
          :family="family"
          @artefact-click="navigateToArtefact"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { api } from '../services/api'
import ArtefactsTableView from '../components/ArtefactsTableView.vue'
import ArtefactsGridView from '../components/ArtefactsGridView.vue'

export default {
  name: 'Dashboard',
  components: {
    ArtefactsTableView,
    ArtefactsGridView
  },
  data() {
    return {
      viewMode: localStorage.getItem('viewMode') || 'grid', // 'grid' or 'list'
      showFilters: false,
      searchQuery: '',
      loading: false,
      error: null,
      artefacts: [],
      selectedFilters: {},
      expandedFilters: {}
    }
  },
  computed: {
    family() {
      return this.$route.meta.family
    },
    title() {
      const familyName = this.family.charAt(0).toUpperCase() + this.family.slice(1)
      return `${familyName} Update Verification`
    },
    filteredArtefacts() {
      let filtered = this.artefacts

      // Apply search query
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase()
        filtered = filtered.filter(a =>
          a.name.toLowerCase().includes(query) ||
          a.version.toLowerCase().includes(query)
        )
      }

      // Apply selected filters
      for (const [filterName, selectedOptions] of Object.entries(this.selectedFilters)) {
        if (selectedOptions.length > 0) {
          filtered = filtered.filter(artefact => {
            const value = this.getArtefactFilterValue(artefact, filterName)
            return selectedOptions.includes(value)
          })
        }
      }

      return filtered
    },
    availableFilters() {
      if (!this.artefacts.length) return []

      const filterDefinitions = {
        snap: ['Assignee', 'Status', 'Due date', 'Risk'],
        deb: ['Assignee', 'Status', 'Due date', 'Series', 'Pocket'],
        charm: ['Assignee', 'Status', 'Due date', 'Risk'],
        image: ['OS type', 'Release', 'Owner', 'Assignee', 'Status', 'Due date']
      }

      const filtersForFamily = filterDefinitions[this.family] || []

      return filtersForFamily.map(filterName => ({
        name: filterName,
        options: this.getFilterOptions(filterName)
      }))
    }
  },
  methods: {
    navigateToArtefact(artefactId) {
      this.$router.push(`/${this.family}s/${artefactId}`)
    },
    async loadArtefacts() {
      this.loading = true
      this.error = null

      try {
        this.artefacts = await api.fetchArtefacts(this.family)
        // Reset filters when family changes
        this.selectedFilters = {}
        this.expandedFilters = {}
      } catch (e) {
        this.error = 'Failed to load artefacts: ' + e.message
        console.error('Failed to load artefacts:', e)
      } finally {
        this.loading = false
      }
    },
    getFilterOptions(filterName) {
      const options = new Set()
      this.artefacts.forEach(artefact => {
        const value = this.getArtefactFilterValue(artefact, filterName)
        if (value) options.add(value)
      })
      return Array.from(options).sort()
    },
    getArtefactFilterValue(artefact, filterName) {
      switch (filterName) {
        case 'Assignee':
          return artefact.assignee?.name || 'N/A'
        case 'Status':
          return artefact.status === 'APPROVED' ? 'Approved'
               : artefact.status === 'MARKED_AS_FAILED' ? 'Rejected'
               : 'Undecided'
        case 'Due date':
          return this.getDueDateCategory(artefact.due_date)
        case 'Risk':
        case 'Pocket':
          return artefact.stage ? artefact.stage.charAt(0).toUpperCase() + artefact.stage.slice(1) : ''
        case 'Series':
          return artefact.series
        case 'OS type':
          return artefact.os
        case 'Release':
          return artefact.release
        case 'Owner':
          return artefact.owner
        default:
          return ''
      }
    },
    getDueDateCategory(dueDate) {
      if (!dueDate) return 'No due date'

      const now = new Date()
      const due = new Date(dueDate)

      if (due < now) return 'Overdue'

      const daysDiff = Math.ceil((due - now) / (1000 * 60 * 60 * 24))
      if (daysDiff <= 7) return 'Within a week'
      return 'More than a week'
    },
    toggleFilterOption(filterName, option, isSelected) {
      if (!this.selectedFilters[filterName]) {
        this.selectedFilters[filterName] = []
      }

      if (isSelected) {
        if (!this.selectedFilters[filterName].includes(option)) {
          this.selectedFilters[filterName].push(option)
        }
      } else {
        this.selectedFilters[filterName] = this.selectedFilters[filterName].filter(o => o !== option)
      }

      // Trigger reactivity
      this.selectedFilters = { ...this.selectedFilters }
    },
    isOptionSelected(filterName, option) {
      return this.selectedFilters[filterName]?.includes(option) || false
    },
    toggleFilterExpanded(filterName) {
      this.expandedFilters[filterName] = !this.expandedFilters[filterName]
      // Trigger reactivity
      this.expandedFilters = { ...this.expandedFilters }
    },
    isFilterExpanded(filterName) {
      // Default to expanded if not set
      return this.expandedFilters[filterName] !== false
    }
  },
  watch: {
    viewMode(newMode) {
      localStorage.setItem('viewMode', newMode)
    },
    family: {
      immediate: true,
      handler() {
        this.loadArtefacts()
      }
    }
  }
}
</script>

<style scoped>
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
  font-size: 28px;
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
