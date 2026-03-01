<template>
  <div class="issues-page">
    <div class="page-header">
      <h1>Linked External Issues</h1>
      <button class="add-issue-button">add issue</button>
    </div>

    <div v-if="loading" class="loading">Loading issues...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="issues-content">
      <div class="content-row">
        <!-- Filter Toggle Button -->
        <div class="filters-toggle">
          <button @click="showFilters = !showFilters" class="filter-button">
            <FilterIcon />
          </button>
        </div>

        <!-- Left Sidebar - Filters -->
        <div v-if="showFilters" class="filters-sidebar">
          <!-- Search -->
          <div class="search-section">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search issues..."
              class="search-input"
              @keyup.enter="applyFilters"
            />
          </div>

          <!-- Source Filter -->
          <div class="filter-group">
            <div class="filter-header" @click="toggleFilter('source')">
              <span>Source</span>
              <span class="expand-icon">{{ isFilterExpanded('source') ? '▼' : '▶' }}</span>
            </div>
            <div v-if="isFilterExpanded('source')" class="filter-options">
              <label v-for="source in availableSources" :key="source" class="filter-option">
                <input
                  type="checkbox"
                  :checked="selectedFilters.sources.includes(source)"
                  @change="toggleFilterOption('sources', source, $event.target.checked)"
                />
                <span>{{ formatSource(source) }}</span>
              </label>
            </div>
          </div>

          <!-- Status Filter -->
          <div class="filter-group">
            <div class="filter-header" @click="toggleFilter('status')">
              <span>Status</span>
              <span class="expand-icon">{{ isFilterExpanded('status') ? '▼' : '▶' }}</span>
            </div>
            <div v-if="isFilterExpanded('status')" class="filter-options">
              <label v-for="status in availableStatuses" :key="status" class="filter-option">
                <input
                  type="checkbox"
                  :checked="selectedFilters.statuses.includes(status)"
                  @change="toggleFilterOption('statuses', status, $event.target.checked)"
                />
                <span>{{ formatStatus(status) }}</span>
              </label>
            </div>
          </div>

          <!-- Project Filter -->
          <div class="filter-group">
            <div class="filter-header" @click="toggleFilter('project')">
              <span>Project</span>
              <span class="expand-icon">{{ isFilterExpanded('project') ? '▼' : '▶' }}</span>
            </div>
            <div v-if="isFilterExpanded('project')" class="filter-options">
              <label v-for="project in availableProjects" :key="project" class="filter-option">
                <input
                  type="checkbox"
                  :checked="selectedFilters.projects.includes(project)"
                  @change="toggleFilterOption('projects', project, $event.target.checked)"
                />
                <span>{{ project }}</span>
              </label>
            </div>
          </div>
        </div>

        <!-- Main Content - Issues List -->
        <div class="issues-container">
          <div v-if="filteredIssues.length === 0" class="empty-state">
            No issues found.
          </div>

          <div v-else class="issues-list">
            <!-- Group by source and project -->
            <div v-for="group in groupedIssues" :key="`${group.source}-${group.project}`" class="issue-group">
              <div class="group-header">
                <span class="source-badge" :class="`source-${group.source}`">{{ formatSource(group.source) }}</span>
                <span class="project-name">{{ group.project }}</span>
              </div>

              <div class="group-issues">
                <div
                  v-for="issue in group.issues"
                  :key="issue.id"
                  class="issue-item"
                  @click="navigateToIssue(issue.id)"
                >
                  <div class="issue-header">
                    <a :href="issue.url" target="_blank" class="issue-key" @click.stop>{{ issue.key }}</a>
                    <span :class="['issue-status', `status-${issue.status}`]">{{ formatStatus(issue.status) }}</span>
                  </div>
                  <div class="issue-title">{{ issue.title }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from '../services/api'
import FilterIcon from '../components/FilterIcon.vue'

export default {
  name: 'IssuesPage',
  components: {
    FilterIcon
  },
  data() {
    return {
      loading: false,
      error: null,
      issues: [],
      showFilters: true,
      searchQuery: '',
      selectedFilters: {
        sources: [],
        statuses: [],
        projects: []
      },
      expandedFilters: {
        source: true,
        status: true,
        project: true
      }
    }
  },
  computed: {
    filteredIssues() {
      let filtered = this.issues

      // Apply search filter
      if (this.searchQuery.trim()) {
        const query = this.searchQuery.toLowerCase()
        filtered = filtered.filter(issue =>
          issue.key.toLowerCase().includes(query) ||
          issue.title.toLowerCase().includes(query) ||
          issue.project.toLowerCase().includes(query)
        )
      }

      // Apply source filter
      if (this.selectedFilters.sources.length > 0) {
        filtered = filtered.filter(issue =>
          this.selectedFilters.sources.includes(issue.source)
        )
      }

      // Apply status filter
      if (this.selectedFilters.statuses.length > 0) {
        filtered = filtered.filter(issue =>
          this.selectedFilters.statuses.includes(issue.status)
        )
      }

      // Apply project filter
      if (this.selectedFilters.projects.length > 0) {
        filtered = filtered.filter(issue =>
          this.selectedFilters.projects.includes(issue.project)
        )
      }

      return filtered
    },
    groupedIssues() {
      const groups = new Map()

      this.filteredIssues.forEach(issue => {
        const key = `${issue.source}:${issue.project}`
        if (!groups.has(key)) {
          groups.set(key, {
            source: issue.source,
            project: issue.project,
            issues: []
          })
        }
        groups.get(key).issues.push(issue)
      })

      return Array.from(groups.values())
    },
    availableSources() {
      return [...new Set(this.issues.map(i => i.source))].sort()
    },
    availableStatuses() {
      return [...new Set(this.issues.map(i => i.status))].sort()
    },
    availableProjects() {
      return [...new Set(this.issues.map(i => i.project))].sort()
    }
  },
  methods: {
    async loadIssues() {
      this.loading = true
      this.error = null

      try {
        const response = await api.fetchIssues({ limit: 1000 })
        this.issues = response.issues || []
      } catch (e) {
        this.error = 'Failed to load issues: ' + e.message
        console.error('Failed to load issues:', e)
      } finally {
        this.loading = false
      }
    },
    applyFilters() {
      // Filters are applied reactively via computed properties
      // This method exists for the Enter key on search
    },
    toggleFilter(filterName) {
      this.expandedFilters[filterName] = !this.expandedFilters[filterName]
    },
    isFilterExpanded(filterName) {
      return this.expandedFilters[filterName] !== false
    },
    toggleFilterOption(filterKey, value, isSelected) {
      if (isSelected) {
        if (!this.selectedFilters[filterKey].includes(value)) {
          this.selectedFilters[filterKey].push(value)
        }
      } else {
        this.selectedFilters[filterKey] = this.selectedFilters[filterKey].filter(v => v !== value)
      }
    },
    formatSource(source) {
      const sourceMap = {
        'github': 'GitHub',
        'jira': 'JIRA',
        'launchpad': 'Launchpad'
      }
      return sourceMap[source] || source
    },
    formatStatus(status) {
      return status.charAt(0).toUpperCase() + status.slice(1).toLowerCase()
    },
    navigateToIssue(issueId) {
      this.$router.push(`/issues/${issueId}`)
    }
  },
  mounted() {
    this.loadIssues()
  }
}
</script>

<style scoped>
.issues-page {
  padding: 24px 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 28px;
  font-weight: 300;
  color: #111;
  margin: 0;
}

.add-issue-button {
  padding: 8px 16px;
  background: #0E8420;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.add-issue-button:hover {
  background: #0a6518;
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

.issues-content {
  display: flex;
  flex-direction: column;
}

.content-row {
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

.filters-sidebar {
  width: 300px;
  flex-shrink: 0;
  background: #f7f7f7;
  padding: 16px;
  border-radius: 4px;
}

.search-section {
  margin-bottom: 16px;
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

.filter-group {
  margin-bottom: 16px;
  border-top: 1px solid #CDCDCD;
  padding-top: 12px;
}

.filter-group:first-of-type {
  border-top: none;
  padding-top: 0;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  padding: 4px 0;
  user-select: none;
  font-size: 14px;
  font-weight: 500;
}

.filter-header:hover {
  color: #0E8420;
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
  cursor: pointer;
  font-size: 13px;
}

.filter-option input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.expand-icon {
  transition: transform 0.2s;
  color: #666;
  font-size: 12px;
}

.issues-container {
  flex: 1;
  min-width: 0;
}

.empty-state {
  padding: 32px;
  text-align: center;
  color: #666;
  background: #f7f7f7;
  border-radius: 4px;
}

.issues-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.issue-group {
  background: white;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
  overflow: hidden;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f7f7f7;
  border-bottom: 1px solid #CDCDCD;
}

.source-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  color: white;
}

.source-badge.source-github {
  background: #24292e;
}

.source-badge.source-jira {
  background: #0052CC;
}

.source-badge.source-launchpad {
  background: #E95420;
}

.project-name {
  font-size: 16px;
  font-weight: 500;
  color: #111;
}

.group-issues {
  display: flex;
  flex-direction: column;
}

.issue-item {
  padding: 12px 16px;
  border-bottom: 1px solid #e7e7e7;
  cursor: pointer;
  transition: background 0.2s;
}

.issue-item:last-child {
  border-bottom: none;
}

.issue-item:hover {
  background: #f9f9f9;
}

.issue-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 6px;
}

.issue-key {
  color: #0E8420;
  text-decoration: none;
  font-weight: 500;
  font-size: 14px;
}

.issue-key:hover {
  text-decoration: underline;
}

.issue-status {
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
}

.issue-status.status-open {
  background: #E5F5E7;
  color: #0E8420;
}

.issue-status.status-closed {
  background: #f0f0f0;
  color: #666;
}

.issue-status.status-unknown {
  background: #FFF4E5;
  color: #F99B11;
}

.issue-title {
  color: #111;
  font-size: 14px;
  line-height: 1.4;
}
</style>
