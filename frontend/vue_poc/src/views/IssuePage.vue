<template>
  <div class="issue-page">
    <div v-if="loading" class="loading">Loading issue...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="issue" class="issue-content">
      <!-- Issue Header -->
      <div class="issue-header">
        <div class="header-row">
          <span class="source-badge" :class="`source-${issue.source}`">{{ formatSource(issue.source) }}</span>
          <span class="project-name">{{ issue.project }}</span>
          <a :href="issue.url" target="_blank" class="issue-key">{{ issue.key }}</a>
          <span :class="['issue-status', `status-${issue.status}`]">{{ formatStatus(issue.status) }}</span>
        </div>
        <h1 class="issue-title">{{ issue.title }}</h1>
      </div>

      <!-- Attachment Rules Section -->
      <div class="section">
        <h2>Attachment Rules</h2>
        <div v-if="issue.attachment_rules.length === 0" class="empty-state">
          No attachment rules defined.
        </div>
        <div v-else class="attachment-rules">
          <div 
            v-for="rule in issue.attachment_rules" 
            :key="rule.id"
            class="attachment-rule"
          >
            <div class="rule-header" @click="toggleRule(rule.id)">
              <span class="rule-title">Attachment Rule #{{ rule.id }}</span>
              <div class="rule-actions">
                <span :class="['rule-status', rule.enabled ? 'enabled' : 'disabled']">
                  {{ rule.enabled ? 'Enabled' : 'Disabled' }}
                </span>
                <span class="expand-icon">{{ isRuleExpanded(rule.id) ? '▼' : '▶' }}</span>
              </div>
            </div>
            <div v-if="isRuleExpanded(rule.id)" class="rule-content">
              <div class="rule-filters">
                <div v-if="rule.families && rule.families.length > 0" class="filter-item">
                  <strong>Families:</strong> {{ rule.families.join(', ') }}
                </div>
                <div v-if="rule.environment_names && rule.environment_names.length > 0" class="filter-item">
                  <strong>Environments:</strong> {{ rule.environment_names.join(', ') }}
                </div>
                <div v-if="rule.test_case_names && rule.test_case_names.length > 0" class="filter-item">
                  <strong>Test Cases:</strong> {{ rule.test_case_names.join(', ') }}
                </div>
                <div v-if="rule.template_ids && rule.template_ids.length > 0" class="filter-item">
                  <strong>Template IDs:</strong> {{ rule.template_ids.join(', ') }}
                </div>
                <div v-if="rule.test_result_statuses && rule.test_result_statuses.length > 0" class="filter-item">
                  <strong>Test Result Statuses:</strong> {{ rule.test_result_statuses.join(', ') }}
                </div>
                <div v-if="rule.execution_metadata && Object.keys(rule.execution_metadata).length > 0" class="filter-item">
                  <strong>Execution Metadata:</strong>
                  <div class="metadata-list">
                    <div v-for="(value, key) in rule.execution_metadata" :key="key" class="metadata-entry">
                      {{ key }}: {{ Array.isArray(value) ? value.join(', ') : value }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Test Results Section -->
      <div class="section">
        <div class="section-header">
          <h2>Test Results</h2>
          <button @click="showFilters = !showFilters" class="filter-toggle-button">
            {{ showFilters ? 'Hide Filters' : 'Show Filters' }}
          </button>
        </div>

        <div v-if="showFilters" class="filters-panel">
          <p class="filters-note">Additional filters can be added here (families, artefacts, environments, test cases, date range, etc.)</p>
        </div>

        <div class="rerun-buttons">
          <button class="action-button secondary" disabled title="Bulk operations not yet implemented">
            Create Rerun Requests
          </button>
          <button class="action-button secondary" disabled title="Bulk operations not yet implemented">
            Delete Rerun Requests
          </button>
        </div>

        <div v-if="loadingTestResults" class="loading-results">Loading test results...</div>
        <div v-else-if="testResultsError" class="error">{{ testResultsError }}</div>
        <div v-else>
          <p class="results-count">
            Found {{ testResultsCount }} results (showing {{ testResults.length }})
          </p>

          <div v-if="testResults.length === 0" class="empty-state">
            No test results found for this issue.
          </div>

          <div v-else class="test-results-table-container">
            <table class="test-results-table">
              <thead>
                <tr>
                  <th>Artefact</th>
                  <th>Test Case</th>
                  <th>Test Execution ID</th>
                  <th>Status</th>
                  <th>Track</th>
                  <th>Version</th>
                  <th>Environment</th>
                  <th>Test Plan</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="result in testResults" :key="`${result.test_execution.id}-${result.test_result.id}`">
                  <td>{{ result.artefact.name }}</td>
                  <td>{{ result.test_result.name }}</td>
                  <td>{{ result.test_execution.id }}</td>
                  <td>
                    <span :class="['status-badge', `status-${result.test_result.status}`]">
                      {{ result.test_result.status }}
                    </span>
                  </td>
                  <td>{{ result.artefact.track || '-' }}</td>
                  <td>{{ result.artefact.version }}</td>
                  <td>{{ result.test_execution.environment.name }}</td>
                  <td>{{ result.test_execution.test_plan }}</td>
                  <td class="actions-cell">
                    <button 
                      @click="showResultDetails(result)" 
                      class="action-link"
                    >
                      details
                    </button>
                    <button 
                      @click="viewRun(result)" 
                      class="action-link"
                    >
                      view run
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Result Details Modal -->
    <div v-if="selectedResult" class="modal-overlay" @click="closeResultDetails">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Test Result Details</h3>
          <button @click="closeResultDetails" class="close-button">×</button>
        </div>
        <div class="modal-body">
          <div class="detail-row">
            <strong>Test Case:</strong> {{ selectedResult.test_result.name }}
          </div>
          <div class="detail-row">
            <strong>Status:</strong> 
            <span :class="['status-badge', `status-${selectedResult.test_result.status}`]">
              {{ selectedResult.test_result.status }}
            </span>
          </div>
          <div class="detail-row">
            <strong>Artefact:</strong> {{ selectedResult.artefact.name }}
          </div>
          <div class="detail-row">
            <strong>Version:</strong> {{ selectedResult.artefact.version }}
          </div>
          <div class="detail-row">
            <strong>Environment:</strong> {{ selectedResult.test_execution.environment.name }}
          </div>
          <div class="detail-row">
            <strong>Test Plan:</strong> {{ selectedResult.test_execution.test_plan }}
          </div>
          <div class="detail-row">
            <strong>Test Execution ID:</strong> {{ selectedResult.test_execution.id }}
          </div>
          <div v-if="selectedResult.test_result.template_id" class="detail-row">
            <strong>Template ID:</strong> {{ selectedResult.test_result.template_id }}
          </div>
          <div v-if="selectedResult.test_result.category" class="detail-row">
            <strong>Category:</strong> {{ selectedResult.test_result.category }}
          </div>
          <div v-if="selectedResult.test_result.comment" class="detail-row">
            <strong>Comment:</strong> {{ selectedResult.test_result.comment }}
          </div>
          <div v-if="selectedResult.test_result.io_log" class="detail-row">
            <strong>I/O Log:</strong>
            <pre class="io-log">{{ selectedResult.test_result.io_log }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from '../services/api'

export default {
  name: 'IssuePage',
  data() {
    return {
      loading: false,
      error: null,
      issue: null,
      expandedRules: new Set(),
      showFilters: false,
      loadingTestResults: false,
      testResultsError: null,
      testResults: [],
      testResultsCount: 0,
      selectedResult: null
    }
  },
  computed: {
    issueId() {
      return parseInt(this.$route.params.issueId)
    }
  },
  methods: {
    async loadIssue() {
      this.loading = true
      this.error = null

      try {
        this.issue = await api.fetchIssue(this.issueId)
        // Load test results after issue loads
        await this.loadTestResults()
      } catch (e) {
        this.error = 'Failed to load issue: ' + e.message
        console.error('Failed to load issue:', e)
      } finally {
        this.loading = false
      }
    },
    async loadTestResults() {
      this.loadingTestResults = true
      this.testResultsError = null

      try {
        const response = await api.searchTestResults({
          issues: [this.issueId],
          limit: 100
        })
        this.testResults = response.test_results || []
        this.testResultsCount = response.count || this.testResults.length
      } catch (e) {
        this.testResultsError = 'Failed to load test results: ' + e.message
        console.error('Failed to load test results:', e)
      } finally {
        this.loadingTestResults = false
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
    toggleRule(ruleId) {
      if (this.expandedRules.has(ruleId)) {
        this.expandedRules.delete(ruleId)
      } else {
        this.expandedRules.add(ruleId)
      }
      // Trigger reactivity
      this.expandedRules = new Set(this.expandedRules)
    },
    isRuleExpanded(ruleId) {
      return this.expandedRules.has(ruleId)
    },
    showResultDetails(result) {
      this.selectedResult = result
    },
    closeResultDetails() {
      this.selectedResult = null
    },
    viewRun(result) {
      // Navigate to artefact page with query parameters
      const family = result.artefact.family + 's' // API returns 'snap', 'deb', etc., routes need plural
      const path = `/${family}/${result.artefact.id}`
      const query = {
        testExecutionId: result.test_execution.id,
        testResultId: result.test_result.id
      }
      this.$router.push({ path, query })
    }
  },
  mounted() {
    this.loadIssue()
  }
}
</script>

<style scoped>
.issue-page {
  padding: 24px 0;
}

.loading,
.error {
  padding: 32px;
  text-align: center;
}

.error {
  color: #C7162B;
}

.issue-content {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.issue-header {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.header-row {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.source-badge {
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 14px;
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
  font-size: 18px;
  font-weight: 500;
  color: #111;
}

.issue-key {
  color: #0E8420;
  text-decoration: none;
  font-weight: 500;
  font-size: 18px;
}

.issue-key:hover {
  text-decoration: underline;
}

.issue-status {
  padding: 4px 10px;
  border-radius: 3px;
  font-size: 12px;
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
  font-size: 24px;
  font-weight: 400;
  color: #111;
  margin: 0;
}

.section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section h2 {
  font-size: 22px;
  font-weight: 400;
  color: #111;
  margin: 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-toggle-button {
  padding: 8px 16px;
  background: white;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.filter-toggle-button:hover {
  background: #f7f7f7;
  border-color: #999;
}

.filters-panel {
  background: #f7f7f7;
  padding: 16px;
  border-radius: 4px;
}

.filters-note {
  color: #666;
  font-size: 14px;
  font-style: italic;
  margin: 0;
}

.empty-state {
  padding: 24px;
  text-align: center;
  color: #666;
  background: #f7f7f7;
  border-radius: 4px;
}

.attachment-rules {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.attachment-rule {
  border: 1px solid #CDCDCD;
  border-radius: 4px;
  background: white;
  overflow: hidden;
}

.rule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  background: #f7f7f7;
  border-bottom: 1px solid #CDCDCD;
  transition: background 0.2s;
}

.rule-header:hover {
  background: #eeeeee;
}

.rule-title {
  font-weight: 500;
  color: #111;
}

.rule-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rule-status {
  padding: 3px 8px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
}

.rule-status.enabled {
  background: #E5F5E7;
  color: #0E8420;
}

.rule-status.disabled {
  background: #f0f0f0;
  color: #666;
}

.expand-icon {
  color: #666;
  font-size: 12px;
}

.rule-content {
  padding: 16px;
}

.rule-filters {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-item {
  font-size: 14px;
  line-height: 1.6;
}

.filter-item strong {
  color: #111;
}

.metadata-list {
  margin-top: 4px;
  padding-left: 16px;
}

.metadata-entry {
  font-size: 13px;
  color: #666;
}

.rerun-buttons {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
}

.action-button {
  padding: 8px 16px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.action-button.primary {
  background: #0E8420;
  color: white;
}

.action-button.primary:hover:not(:disabled) {
  background: #0a6518;
}

.action-button.secondary {
  background: white;
  color: #111;
  border: 1px solid #CDCDCD;
}

.action-button.secondary:hover:not(:disabled) {
  background: #f7f7f7;
  border-color: #999;
}

.action-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading-results {
  padding: 24px;
  text-align: center;
  color: #666;
}

.results-count {
  font-size: 14px;
  color: #666;
  margin-bottom: 12px;
}

.test-results-table-container {
  overflow-x: auto;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
}

.test-results-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  font-size: 14px;
}

.test-results-table th {
  background: #f7f7f7;
  padding: 12px 16px;
  text-align: left;
  font-weight: 500;
  color: #111;
  border-bottom: 2px solid #CDCDCD;
}

.test-results-table td {
  padding: 12px 16px;
  border-bottom: 1px solid #e7e7e7;
}

.test-results-table tbody tr:hover {
  background: #f9f9f9;
}

.test-results-table tbody tr:last-child td {
  border-bottom: none;
}

.status-badge {
  padding: 3px 8px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  white-space: nowrap;
}

.status-badge.status-PASSED {
  background: #E5F5E7;
  color: #0E8420;
}

.status-badge.status-FAILED {
  background: #FDECEA;
  color: #C7162B;
}

.status-badge.status-SKIPPED {
  background: #FFF4E5;
  color: #F99B11;
}

.actions-cell {
  display: flex;
  gap: 8px;
}

.action-link {
  background: none;
  border: none;
  color: #0E8420;
  cursor: pointer;
  text-decoration: underline;
  font-size: 13px;
  padding: 0;
}

.action-link:hover {
  color: #0a6518;
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
  max-width: 800px;
  max-height: 80vh;
  width: 90%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #CDCDCD;
}

.modal-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
}

.close-button {
  background: none;
  border: none;
  font-size: 32px;
  color: #666;
  cursor: pointer;
  line-height: 1;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-button:hover {
  color: #111;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
}

.detail-row {
  margin-bottom: 16px;
}

.detail-row strong {
  display: block;
  margin-bottom: 4px;
  color: #111;
}

.io-log {
  background: #f7f7f7;
  padding: 12px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  overflow-x: auto;
  margin-top: 8px;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
