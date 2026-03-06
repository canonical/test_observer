<template>
  <div class="test-results-search-page">
    <div class="page-header">
      <h1>Search Test Results</h1>
      <button @click="showFilters = !showFilters" class="filter-toggle-button">
        {{ showFilters ? 'Hide' : 'Show' }} Filters
      </button>
    </div>

    <div class="page-content">
      <!-- Filters Sidebar -->
      <div v-if="showFilters" class="filters-sidebar">
        <div class="filters-header">
          <h2>Filters</h2>
          <button @click="clearFilters" class="clear-button">Clear All</button>
        </div>

        <div class="filters-content">
          <!-- Family Filter -->
          <div class="filter-group">
            <label class="filter-label">Family</label>
            <select v-model="filters.family" class="filter-select">
              <option value="">All Families</option>
              <option value="snap">Snap</option>
              <option value="deb">Deb</option>
              <option value="image">Image</option>
              <option value="charm">Charm</option>
            </select>
          </div>

          <!-- Status Filter -->
          <div class="filter-group">
            <label class="filter-label">Status</label>
            <div class="checkbox-group">
              <label class="checkbox-label">
                <input type="checkbox" value="PASSED" v-model="filters.statuses" />
                <span>Passed</span>
              </label>
              <label class="checkbox-label">
                <input type="checkbox" value="FAILED" v-model="filters.statuses" />
                <span>Failed</span>
              </label>
              <label class="checkbox-label">
                <input type="checkbox" value="SKIPPED" v-model="filters.statuses" />
                <span>Skipped</span>
              </label>
            </div>
          </div>

          <!-- Artefact Filter -->
          <div class="filter-group">
            <label class="filter-label">Artefact</label>
            <input
              v-model="filters.artefact"
              type="text"
              placeholder="Filter by artefact name"
              class="filter-input"
            />
          </div>

          <!-- Environment Filter -->
          <div class="filter-group">
            <label class="filter-label">Environment</label>
            <input
              v-model="filters.environment"
              type="text"
              placeholder="Filter by environment"
              class="filter-input"
            />
          </div>

          <!-- Test Case Filter -->
          <div class="filter-group">
            <label class="filter-label">Test Case</label>
            <input
              v-model="filters.testCase"
              type="text"
              placeholder="Filter by test case"
              class="filter-input"
            />
          </div>

          <!-- Date Range -->
          <div class="filter-group">
            <label class="filter-label">From Date</label>
            <input v-model="filters.fromDate" type="date" class="filter-input" />
          </div>

          <div class="filter-group">
            <label class="filter-label">To Date</label>
            <input v-model="filters.toDate" type="date" class="filter-input" />
          </div>

          <button @click="applyFilters" class="apply-button">Apply Filters</button>
        </div>
      </div>

      <!-- Main Content -->
      <div class="main-content">
        <!-- Empty State -->
        <div v-if="!hasAppliedFilters" class="empty-state">
          <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"></circle>
            <path d="m21 21-4.35-4.35"></path>
          </svg>
          <h2>Search for test results</h2>
          <p>Use the filters and click Apply Filters to search for test results.</p>
        </div>

        <!-- Loading State -->
        <div v-else-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>Loading test results...</p>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="error-state">
          <p>{{ error }}</p>
        </div>

        <!-- Results -->
        <div v-else-if="results.length > 0" class="results-section">
          <div class="results-header">
            <p class="results-count">
              Found {{ totalCount }} results (showing {{ results.length }})
            </p>
            <button v-if="hasMore" @click="loadMore" :disabled="loadingMore" class="load-more-button">
              {{ loadingMore ? 'Loading...' : 'Load More' }}
            </button>
          </div>

          <div class="results-table-container">
            <table class="results-table">
              <thead>
                <tr>
                  <th>Artefact</th>
                  <th>Version</th>
                  <th>Test Case</th>
                  <th>Environment</th>
                  <th>Status</th>
                  <th>Test Plan</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="result in results" :key="result.test_result.id" class="result-row">
                  <td>
                    <a :href="`/${result.artefact.family}s/${result.artefact.id}`" class="artefact-link">
                      {{ result.artefact.name }}
                    </a>
                  </td>
                  <td>{{ result.artefact.version }}</td>
                  <td>{{ result.test_result.name }}</td>
                  <td>{{ result.test_execution.environment.name }}</td>
                  <td>
                    <span :class="['status-badge', getStatusClass(result.test_result.status)]">
                      {{ formatStatus(result.test_result.status) }}
                    </span>
                  </td>
                  <td>{{ result.test_execution.test_plan || 'N/A' }}</td>
                  <td>{{ formatDateTime(result.test_result.created_at) }}</td>
                  <td>
                    <button @click="showDetails(result)" class="action-button">Details</button>
                    <button @click="viewRun(result)" class="action-button">View Run</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- No Results -->
        <div v-else class="no-results-state">
          <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"></circle>
            <path d="m21 21-4.35-4.35"></path>
            <line x1="11" y1="8" x2="11" y2="14"></line>
            <line x1="11" y1="16" x2="11.01" y2="16"></line>
          </svg>
          <h2>No results found</h2>
          <p>Try adjusting your filters or search criteria.</p>
        </div>
      </div>
    </div>

    <!-- Details Modal -->
    <div v-if="selectedResult" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>Test Result Details</h2>
          <button @click="closeModal" class="close-button">×</button>
        </div>
        <div class="modal-body">
          <div class="detail-row">
            <span class="detail-label">Test Case:</span>
            <span>{{ selectedResult.test_result.name }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Status:</span>
            <span :class="['status-badge', getStatusClass(selectedResult.test_result.status)]">
              {{ formatStatus(selectedResult.test_result.status) }}
            </span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Category:</span>
            <span>{{ selectedResult.test_result.category || 'N/A' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Template ID:</span>
            <span>{{ selectedResult.test_result.template_id || 'N/A' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Comment:</span>
            <span>{{ selectedResult.test_result.comment || 'N/A' }}</span>
          </div>
          <div v-if="selectedResult.test_result.io_log" class="detail-row">
            <span class="detail-label">IO Log:</span>
            <pre class="io-log">{{ selectedResult.test_result.io_log }}</pre>
          </div>
          <div class="detail-row">
            <span class="detail-label">Artefact:</span>
            <span>{{ selectedResult.artefact.name }} ({{ selectedResult.artefact.version }})</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Environment:</span>
            <span>{{ selectedResult.test_execution.environment.name }} ({{ selectedResult.test_execution.environment.architecture }})</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Test Plan:</span>
            <span>{{ selectedResult.test_execution.test_plan || 'N/A' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Created:</span>
            <span>{{ formatDateTime(selectedResult.test_result.created_at) }}</span>
          </div>
          <div v-if="selectedResult.test_result.issues && selectedResult.test_result.issues.length > 0" class="detail-row">
            <span class="detail-label">Related Issues:</span>
            <ul class="issues-list">
              <li v-for="issueAttachment in selectedResult.test_result.issues" :key="issueAttachment.issue.id">
                <a :href="issueAttachment.issue.url" target="_blank" class="issue-link">
                  {{ issueAttachment.issue.key }}: {{ issueAttachment.issue.title }}
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from '../services/api'

export default {
  name: 'TestResultsSearchPage',
  data() {
    return {
      showFilters: true,
      filters: {
        family: '',
        statuses: [],
        artefact: '',
        environment: '',
        testCase: '',
        fromDate: '',
        toDate: ''
      },
      appliedFilters: {},
      hasAppliedFilters: false,
      loading: false,
      loadingMore: false,
      error: null,
      results: [],
      totalCount: 0,
      selectedResult: null
    }
  },
  computed: {
    hasMore() {
      return this.results.length < this.totalCount
    }
  },
  methods: {
    clearFilters() {
      this.filters = {
        family: '',
        statuses: [],
        artefact: '',
        environment: '',
        testCase: '',
        fromDate: '',
        toDate: ''
      }
    },
    async applyFilters() {
      this.appliedFilters = { ...this.filters }
      this.hasAppliedFilters = true
      this.results = []
      this.totalCount = 0
      await this.search()
    },
    async search() {
      this.loading = true
      this.error = null

      try {
        const params = {
          limit: 100,
          offset: 0
        }

        if (this.appliedFilters.family) {
          params.families = [this.appliedFilters.family]
        }
        if (this.appliedFilters.statuses && this.appliedFilters.statuses.length > 0) {
          params.test_result_statuses = this.appliedFilters.statuses
        }
        if (this.appliedFilters.artefact) {
          params.artefacts = [this.appliedFilters.artefact]
        }
        if (this.appliedFilters.environment) {
          params.environments = [this.appliedFilters.environment]
        }
        if (this.appliedFilters.testCase) {
          params.test_cases = [this.appliedFilters.testCase]
        }
        if (this.appliedFilters.fromDate) {
          params.from_date = this.appliedFilters.fromDate
        }
        if (this.appliedFilters.toDate) {
          params.to_date = this.appliedFilters.toDate
        }

        const response = await api.searchTestResults(params)
        this.results = response.test_results || []
        this.totalCount = response.count || 0
      } catch (e) {
        this.error = 'Failed to search test results: ' + e.message
        console.error('Failed to search test results:', e)
      } finally {
        this.loading = false
      }
    },
    async loadMore() {
      if (this.loadingMore || !this.hasMore) return

      this.loadingMore = true

      try {
        const params = {
          limit: 100,
          offset: this.results.length
        }

        if (this.appliedFilters.family) {
          params.families = [this.appliedFilters.family]
        }
        if (this.appliedFilters.statuses && this.appliedFilters.statuses.length > 0) {
          params.test_result_statuses = this.appliedFilters.statuses
        }
        if (this.appliedFilters.artefact) {
          params.artefacts = [this.appliedFilters.artefact]
        }
        if (this.appliedFilters.environment) {
          params.environments = [this.appliedFilters.environment]
        }
        if (this.appliedFilters.testCase) {
          params.test_cases = [this.appliedFilters.testCase]
        }
        if (this.appliedFilters.fromDate) {
          params.from_date = this.appliedFilters.fromDate
        }
        if (this.appliedFilters.toDate) {
          params.to_date = this.appliedFilters.toDate
        }

        const response = await api.searchTestResults(params)
        this.results.push(...(response.test_results || []))
      } catch (e) {
        console.error('Failed to load more results:', e)
      } finally {
        this.loadingMore = false
      }
    },
    showDetails(result) {
      this.selectedResult = result
    },
    closeModal() {
      this.selectedResult = null
    },
    viewRun(result) {
      const family = result.artefact.family
      const artefactId = result.artefact.id
      const testExecutionId = result.test_execution.id
      const testResultId = result.test_result.id

      this.$router.push({
        path: `/${family}s/${artefactId}`,
        query: {
          testExecutionId: testExecutionId,
          testResultId: testResultId
        }
      })
    },
    getStatusClass(status) {
      return status.toLowerCase()
    },
    formatStatus(status) {
      return status.charAt(0) + status.slice(1).toLowerCase()
    },
    formatDateTime(dateString) {
      if (!dateString) return 'N/A'
      return new Date(dateString).toLocaleString()
    }
  }
}
</script>

<style scoped>
.test-results-search-page {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

h1 {
  font-size: 28px;
  font-weight: 300;
  margin: 0;
}

.filter-toggle-button {
  padding: 8px 16px;
  background: #0E8420;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.filter-toggle-button:hover {
  background: #0C6D1A;
}

.page-content {
  display: flex;
  gap: 24px;
}

.filters-sidebar {
  width: 300px;
  flex-shrink: 0;
  background: #F7F7F7;
  border-radius: 8px;
  padding: 20px;
}

.filters-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.filters-header h2 {
  font-size: 18px;
  font-weight: 400;
  margin: 0;
}

.clear-button {
  padding: 4px 12px;
  background: transparent;
  color: #0E8420;
  border: 1px solid #0E8420;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.clear-button:hover {
  background: #0E8420;
  color: white;
}

.filters-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-label {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.filter-select,
.filter-input {
  padding: 8px 12px;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
  font-size: 14px;
}

.filter-select:focus,
.filter-input:focus {
  outline: none;
  border-color: #0E8420;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  cursor: pointer;
}

.apply-button {
  padding: 10px 16px;
  background: #0E8420;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  margin-top: 8px;
}

.apply-button:hover {
  background: #0C6D1A;
}

.main-content {
  flex: 1;
  min-width: 0;
}

.empty-state,
.loading-state,
.error-state,
.no-results-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
  color: #666;
}

.empty-state svg,
.no-results-state svg {
  color: #999;
  margin-bottom: 16px;
}

.empty-state h2,
.no-results-state h2 {
  font-size: 24px;
  font-weight: 400;
  margin: 0 0 8px 0;
}

.empty-state p,
.no-results-state p {
  font-size: 14px;
  margin: 0;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #0E8420;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-state p {
  font-size: 14px;
}

.error-state {
  color: #C7162B;
}

.results-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
}

.results-count {
  font-size: 16px;
  font-weight: 500;
  margin: 0;
}

.load-more-button {
  padding: 8px 16px;
  background: #0E8420;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.load-more-button:hover:not(:disabled) {
  background: #0C6D1A;
}

.load-more-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.results-table-container {
  overflow-x: auto;
  border: 1px solid #E0E0E0;
  border-radius: 8px;
}

.results-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
}

.results-table thead {
  background: #F7F7F7;
  border-bottom: 2px solid #E0E0E0;
}

.results-table th {
  padding: 12px 16px;
  text-align: left;
  font-weight: 500;
  font-size: 14px;
  color: #333;
}

.results-table tbody tr {
  border-bottom: 1px solid #E0E0E0;
}

.results-table tbody tr:hover {
  background: #F9F9F9;
}

.results-table td {
  padding: 12px 16px;
  font-size: 14px;
}

.artefact-link {
  color: #0E8420;
  text-decoration: none;
}

.artefact-link:hover {
  text-decoration: underline;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  display: inline-block;
}

.status-badge.passed {
  background: #E6F4EA;
  color: #0E8420;
}

.status-badge.failed {
  background: #FCEAE9;
  color: #C7162B;
}

.status-badge.skipped {
  background: #FFF3E0;
  color: #F57C00;
}

.action-button {
  padding: 4px 12px;
  background: transparent;
  color: #0E8420;
  border: 1px solid #0E8420;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  margin-right: 4px;
}

.action-button:hover {
  background: #0E8420;
  color: white;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  max-width: 700px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #E0E0E0;
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 400;
}

.close-button {
  background: none;
  border: none;
  font-size: 32px;
  line-height: 1;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-button:hover {
  color: #333;
}

.modal-body {
  padding: 24px;
}

.detail-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.detail-label {
  font-weight: 500;
  min-width: 140px;
  color: #666;
}

.io-log {
  background: #F7F7F7;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  font-family: monospace;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
}

.issues-list {
  margin: 0;
  padding-left: 20px;
}

.issues-list li {
  margin-bottom: 4px;
}

.issue-link {
  color: #0E8420;
  text-decoration: none;
}

.issue-link:hover {
  text-decoration: underline;
}
</style>
