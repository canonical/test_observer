<template>
  <div class="artefact-page">
    <div class="page-header">
      <button @click="$router.back()" class="back-button">← Back</button>
      <h1>{{ artefact?.name || `Artefact #${artefactId}` }}</h1>
    </div>

    <div v-if="loading" class="loading">Loading artefact details...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="artefact-content">
      <div class="content-row">
        <!-- Filter Toggle Button -->
        <div class="filters-toggle">
          <button @click="showFilters = !showFilters" class="filter-button">
            ⚙
          </button>
        </div>

        <!-- Left Sidebar - Info & Filters -->
        <div v-if="showFilters" class="info-sidebar">
          <!-- Artefact Info Section -->
          <div class="info-section">
            <div class="info-item" v-if="artefact?.stage">
              <span class="label">Stage:</span>
              <span class="value stage-badge">{{ artefact.stage }}</span>
            </div>
            <div class="info-item">
              <span class="label">Version:</span>
              <span class="value">{{ artefact?.version }}</span>
            </div>
            <div class="info-item" v-if="artefact?.track">
              <span class="label">Track:</span>
              <span class="value">{{ artefact.track }}</span>
            </div>
            <div class="info-item" v-if="artefact?.store">
              <span class="label">Store:</span>
              <span class="value">{{ artefact.store }}</span>
            </div>
            <div class="info-item" v-if="artefact?.branch">
              <span class="label">Branch:</span>
              <span class="value">{{ artefact.branch }}</span>
            </div>
            <div class="info-item" v-if="artefact?.series">
              <span class="label">Series:</span>
              <span class="value">{{ artefact.series }}</span>
            </div>
            <div class="info-item" v-if="artefact?.repo">
              <span class="label">Repo:</span>
              <span class="value">{{ artefact.repo }}</span>
            </div>
            <div class="info-item" v-if="artefact?.source">
              <span class="label">Source:</span>
              <span class="value">{{ artefact.source }}</span>
            </div>
            <div class="info-item" v-if="artefact?.os">
              <span class="label">OS:</span>
              <span class="value">{{ artefact.os }}</span>
            </div>
            <div class="info-item" v-if="artefact?.release">
              <span class="label">Release:</span>
              <span class="value">{{ artefact.release }}</span>
            </div>
            <div class="info-item" v-if="artefact?.owner">
              <span class="label">Owner:</span>
              <span class="value">{{ artefact.owner }}</span>
            </div>
            <div class="info-item" v-if="artefact?.bug_link">
              <span class="label">Bug Link:</span>
              <a :href="artefact.bug_link" target="_blank" class="value link">{{ artefact.bug_link }}</a>
            </div>
            <div class="info-item">
              <span class="label">Comment:</span>
              <span class="value">{{ artefact?.comment || 'None' }}</span>
            </div>
          </div>

          <!-- Filters Section -->
          <div class="filters-section">
            <h3>Filters</h3>

            <div class="filter-group">
              <div class="filter-header" @click="toggleFilter('environment')">
                <span>Environment</span>
                <span class="expand-icon">{{ isFilterExpanded('environment') ? '▼' : '▶' }}</span>
              </div>
              <div v-if="isFilterExpanded('environment')" class="filter-options">
                <label v-for="env in availableEnvironments" :key="env" class="filter-option">
                  <input
                    type="checkbox"
                    :checked="selectedFilters.environments.includes(env)"
                    @change="toggleFilterOption('environments', env, $event.target.checked)"
                  />
                  <span>{{ env }}</span>
                </label>
              </div>
            </div>

            <div class="filter-group">
              <div class="filter-header" @click="toggleFilter('architecture')">
                <span>Architecture</span>
                <span class="expand-icon">{{ isFilterExpanded('architecture') ? '▼' : '▶' }}</span>
              </div>
              <div v-if="isFilterExpanded('architecture')" class="filter-options">
                <label v-for="arch in availableArchitectures" :key="arch" class="filter-option">
                  <input
                    type="checkbox"
                    :checked="selectedFilters.architectures.includes(arch)"
                    @change="toggleFilterOption('architectures', arch, $event.target.checked)"
                  />
                  <span>{{ arch }}</span>
                </label>
              </div>
            </div>

            <div class="filter-group">
              <div class="filter-header" @click="toggleFilter('status')">
                <span>Status</span>
                <span class="expand-icon">{{ isFilterExpanded('status') ? '▼' : '▶' }}</span>
              </div>
              <div v-if="isFilterExpanded('status')" class="filter-options">
                <label v-for="status in ['PASSED', 'FAILED', 'IN_PROGRESS', 'NOT_STARTED']" :key="status" class="filter-option">
                  <input
                    type="checkbox"
                    :checked="selectedFilters.statuses.includes(status)"
                    @change="toggleFilterOption('statuses', status, $event.target.checked)"
                  />
                  <span>{{ formatStatus(status) }}</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        <!-- Main Content - Environments List -->
        <div class="environments-container">
          <div class="environments-header">
            <h2>Environments</h2>
            <div class="status-summary">
              {{ passedCount }} passed, {{ failedCount }} failed, {{ inProgressCount }} in progress
            </div>
          </div>

          <div v-if="filteredEnvironments.length === 0" class="empty-state">
            No environments match the current filters.
          </div>

          <div v-else class="environments-list">
            <div
              v-for="env in filteredEnvironments"
              :key="env.id"
              class="environment-item"
            >
              <!-- Environment Header -->
              <div class="environment-header" @click="toggleEnvironment(env.id)">
                <div class="environment-title">
                  <span :class="['status-icon', getStatusClass(env.status)]">{{ getStatusIcon(env.status) }}</span>
                  <span class="architecture">{{ env.architecture }}</span>
                  <span class="name">{{ env.name }}</span>
                </div>
                <div class="environment-actions">
                  <span class="expand-icon">{{ isEnvironmentExpanded(env.id) ? '▼' : '▶' }}</span>
                </div>
              </div>

              <!-- Environment Content (Collapsed by default) -->
              <div v-if="isEnvironmentExpanded(env.id)" class="environment-content">
                <!-- Test Plans -->
                <div class="test-plans-section">
                  <div class="section-header" @click="toggleSection(env.id, 'testPlans')">
                    <span>Test Plans</span>
                    <span class="expand-icon">{{ isSectionExpanded(env.id, 'testPlans') ? '▼' : '▶' }}</span>
                  </div>

                  <div v-if="isSectionExpanded(env.id, 'testPlans')" class="test-plans-list">
                    <div
                      v-for="(executions, planName) in groupTestExecutionsByPlan(env.testExecutions)"
                      :key="planName"
                      class="test-plan-item"
                    >
                      <!-- Test Plan Header -->
                      <div class="test-plan-header" @click="toggleTestPlan(env.id, planName)">
                        <span class="plan-name">{{ planName || 'Unknown Plan' }}</span>
                        <span class="expand-icon">{{ isTestPlanExpanded(env.id, planName) ? '▼' : '▶' }}</span>
                      </div>

                      <!-- Test Executions for this plan -->
                      <div v-if="isTestPlanExpanded(env.id, planName)" class="test-executions-list">
                        <div
                          v-for="(execution, index) in executions"
                          :key="execution.id"
                          class="test-execution-item"
                        >
                          <div class="execution-header" @click="toggleTestExecution(execution.id)">
                            <div class="execution-title">
                              <span :class="['status-icon', getStatusClass(execution.status)]">
                                {{ getStatusIcon(execution.status) }}
                              </span>
                              <span class="run-number">Run #{{ executions.length - index }}</span>
                              <span class="execution-date">{{ formatDate(execution.created_at) }}</span>
                            </div>
                            <span class="expand-icon">{{ isTestExecutionExpanded(execution.id) ? '▼' : '▶' }}</span>
                          </div>

                          <!-- Test Execution Details -->
                          <div v-if="isTestExecutionExpanded(execution.id)" class="execution-details">
                            <!-- Event Log -->
                            <div class="detail-section">
                              <div class="detail-section-header" @click="toggleExecutionSection(execution.id, 'eventLog')">
                                <span class="section-title">Event Log</span>
                                <span class="expand-icon">{{ isExecutionSectionExpanded(execution.id, 'eventLog') ? '▼' : '▶' }}</span>
                              </div>
                              <div v-if="isExecutionSectionExpanded(execution.id, 'eventLog')" class="event-log">
                                <div v-if="loadingTestEvents[execution.id]" class="loading-small">Loading events...</div>
                                <div v-else-if="testEvents[execution.id] && testEvents[execution.id].length > 0" class="events-table">
                                  <table>
                                    <thead>
                                      <tr>
                                        <th>Event Name</th>
                                        <th>Timestamp</th>
                                        <th>Detail</th>
                                      </tr>
                                    </thead>
                                    <tbody>
                                      <tr v-for="event in testEvents[execution.id]" :key="event.event_name + event.timestamp">
                                        <td>{{ event.event_name }}</td>
                                        <td>{{ event.timestamp }}</td>
                                        <td class="detail-cell" :title="event.detail">{{ event.detail }}</td>
                                      </tr>
                                    </tbody>
                                  </table>
                                </div>
                                <div v-else class="empty-state-small">No events recorded</div>
                              </div>
                            </div>

                            <!-- Execution Metadata -->
                            <div class="detail-section">
                              <div class="detail-section-header" @click="toggleExecutionSection(execution.id, 'metadata')">
                                <span class="section-title">Execution Metadata</span>
                                <span class="expand-icon">{{ isExecutionSectionExpanded(execution.id, 'metadata') ? '▼' : '▶' }}</span>
                              </div>
                              <div v-if="isExecutionSectionExpanded(execution.id, 'metadata')" class="metadata-content">
                                <div v-if="execution.execution_metadata && Object.keys(execution.execution_metadata).length > 0" class="metadata-table">
                                  <table>
                                    <tbody>
                                      <tr v-for="(value, key) in execution.execution_metadata" :key="key">
                                        <td class="metadata-key">{{ key }}</td>
                                        <td class="metadata-value">{{ Array.isArray(value) ? value.join(', ') : value }}</td>
                                      </tr>
                                    </tbody>
                                  </table>
                                </div>
                                <div v-else class="empty-state-small">No metadata available</div>
                              </div>
                            </div>

                            <!-- Test Results (only if execution is completed) -->
                            <div v-if="isExecutionCompleted(execution.status)" class="detail-section">
                              <div class="detail-section-header" @click="toggleExecutionSection(execution.id, 'results')">
                                <span class="section-title">Test Results</span>
                                <span class="expand-icon">{{ isExecutionSectionExpanded(execution.id, 'results') ? '▼' : '▶' }}</span>
                              </div>
                              <div v-if="isExecutionSectionExpanded(execution.id, 'results')" class="test-results">
                                <div v-if="loadingTestResults[execution.id]" class="loading-small">Loading test results...</div>
                                <div v-else-if="testResults[execution.id]">
                                  <!-- Grouped by status -->
                                  <div v-for="status in ['PASSED', 'FAILED', 'SKIPPED']" :key="status" class="results-group">
                                    <div
                                      class="results-group-header"
                                      @click="toggleResultsGroup(execution.id, status)"
                                      v-if="getTestResultsByStatus(execution.id, status).length > 0"
                                    >
                                      <span :class="['status-icon', getStatusClass(status)]">{{ getStatusIcon(status) }}</span>
                                      <span class="status-label">{{ formatStatus(status) }}</span>
                                      <span class="count">{{ getTestResultsByStatus(execution.id, status).length }}</span>
                                      <span class="expand-icon">{{ isResultsGroupExpanded(execution.id, status) ? '▼' : '▶' }}</span>
                                    </div>
                                    <div v-if="isResultsGroupExpanded(execution.id, status)" class="results-list">
                                      <div
                                        v-for="result in getTestResultsByStatus(execution.id, status)"
                                        :key="result.id"
                                        :data-result-id="result.id"
                                        class="result-item"
                                      >
                                        <div class="result-header" @click="toggleResult(result.id)">
                                          <span class="result-name">{{ result.name }}</span>
                                          <span v-if="result.issues && result.issues.length > 0" class="issues-count">
                                            ({{ result.issues.length }} {{ result.issues.length === 1 ? 'issue' : 'issues' }})
                                          </span>
                                          <span class="expand-icon">{{ isResultExpanded(result.id) ? '▼' : '▶' }}</span>
                                        </div>
                                        <div v-if="isResultExpanded(result.id)" class="result-details">
                                          <div class="result-detail-item" v-if="result.category">
                                            <span class="label">Category:</span>
                                            <span>{{ result.category }}</span>
                                          </div>
                                          <div class="result-detail-item" v-if="result.comment">
                                            <span class="label">Comment:</span>
                                            <span>{{ result.comment }}</span>
                                          </div>
                                          <div class="result-detail-item" v-if="result.io_log">
                                            <span class="label">IO Log:</span>
                                            <pre class="io-log">{{ result.io_log }}</pre>
                                          </div>
                                          <div class="result-detail-item" v-if="result.issues && result.issues.length > 0">
                                            <span class="label">Related Issues:</span>
                                            <ul class="issues-list">
                                              <li v-for="issueAttachment in result.issues" :key="issueAttachment.issue.id">
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
                                </div>
                                <div v-else class="empty-state-small">No test results available</div>
                              </div>
                            </div>

                            <!-- Basic Info -->
                            <div class="basic-info">
                              <div class="detail-item" v-if="execution.ci_link">
                                <span class="label">CI Link:</span>
                                <a :href="execution.ci_link" target="_blank" class="link">{{ execution.ci_link }}</a>
                              </div>
                              <div class="detail-item" v-if="execution.c3_link">
                                <span class="label">C3 Link:</span>
                                <a :href="execution.c3_link" target="_blank" class="link">{{ execution.c3_link }}</a>
                              </div>
                              <div class="detail-item">
                                <span class="label">Created:</span>
                                <span>{{ formatDateTime(execution.created_at) }}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
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

export default {
  name: 'ArtefactPage',
  data() {
    return {
      loading: false,
      error: null,
      artefact: null,
      builds: [],
      environmentReviews: [],
      showFilters: true,
      selectedFilters: {
        environments: [],
        architectures: [],
        statuses: []
      },
      expandedFilters: {
        environment: true,
        architecture: true,
        status: true
      },
      expandedEnvironments: {},
      expandedSections: {},
      expandedTestPlans: {},
      expandedTestExecutions: {},
      expandedExecutionSections: {},
      expandedResultsGroups: {},
      expandedResults: {},
      testEvents: {},
      testResults: {},
      loadingTestEvents: {},
      loadingTestResults: {}
    }
  },
  computed: {
    artefactId() {
      return parseInt(this.$route.params.artefactId)
    },
    family() {
      return this.$route.meta.family
    },
    // Transform builds data to environment-centric structure
    environments() {
      if (!this.builds || this.builds.length === 0) return []

      // Group test executions by environment
      const envMap = new Map()

      this.builds.forEach(build => {
        build.test_executions.forEach(execution => {
          const envKey = `${execution.environment.name}-${execution.environment.architecture}`

          if (!envMap.has(envKey)) {
            envMap.set(envKey, {
              id: execution.environment.id,
              name: execution.environment.name,
              architecture: execution.environment.architecture,
              testExecutions: [],
              status: 'NOT_STARTED'
            })
          }

          envMap.get(envKey).testExecutions.push(execution)
        })
      })

      // Calculate overall status for each environment
      const environments = Array.from(envMap.values())
      environments.forEach(env => {
        // Sort executions by creation date descending
        env.testExecutions.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))

        // Determine overall status (use the most recent execution's status)
        if (env.testExecutions.length > 0) {
          env.status = env.testExecutions[0].status
        }
      })

      return environments
    },
    filteredEnvironments() {
      let filtered = this.environments

      // Filter by environment names
      if (this.selectedFilters.environments.length > 0) {
        filtered = filtered.filter(env =>
          this.selectedFilters.environments.includes(env.name)
        )
      }

      // Filter by architectures
      if (this.selectedFilters.architectures.length > 0) {
        filtered = filtered.filter(env =>
          this.selectedFilters.architectures.includes(env.architecture)
        )
      }

      // Filter by test execution status
      if (this.selectedFilters.statuses.length > 0) {
        filtered = filtered.filter(env =>
          env.testExecutions.some(te =>
            this.selectedFilters.statuses.includes(te.status)
          )
        )
      }

      return filtered
    },
    availableEnvironments() {
      return [...new Set(this.environments.map(e => e.name))].sort()
    },
    availableArchitectures() {
      return [...new Set(this.environments.map(e => e.architecture))].sort()
    },
    passedCount() {
      return this.environments.filter(e => e.status === 'PASSED').length
    },
    failedCount() {
      return this.environments.filter(e => e.status === 'FAILED').length
    },
    inProgressCount() {
      return this.environments.filter(e => e.status === 'IN_PROGRESS').length
    }
  },
  methods: {
    async loadData() {
      this.loading = true
      this.error = null

      try {
        // Load all data in parallel
        const [artefactData, buildsData, reviewsData] = await Promise.all([
          api.fetchArtefact(this.artefactId),
          api.fetchArtefactBuilds(this.artefactId),
          api.fetchEnvironmentReviews(this.artefactId)
        ])

        this.artefact = artefactData
        this.builds = buildsData
        this.environmentReviews = reviewsData
      } catch (e) {
        this.error = 'Failed to load artefact details: ' + e.message
        console.error('Failed to load artefact details:', e)
      } finally {
        this.loading = false
      }
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
    toggleEnvironment(envId) {
      this.expandedEnvironments[envId] = !this.expandedEnvironments[envId]
      this.expandedEnvironments = { ...this.expandedEnvironments }
    },
    isEnvironmentExpanded(envId) {
      return this.expandedEnvironments[envId] || false
    },
    toggleSection(envId, sectionName) {
      const key = `${envId}-${sectionName}`
      this.expandedSections[key] = !this.expandedSections[key]
      this.expandedSections = { ...this.expandedSections }
    },
    isSectionExpanded(envId, sectionName) {
      const key = `${envId}-${sectionName}`
      return this.expandedSections[key] !== false
    },
    toggleTestPlan(envId, planName) {
      const key = `${envId}-${planName}`
      this.expandedTestPlans[key] = !this.expandedTestPlans[key]
      this.expandedTestPlans = { ...this.expandedTestPlans }
    },
    isTestPlanExpanded(envId, planName) {
      const key = `${envId}-${planName}`
      // Expand first test plan by default
      return this.expandedTestPlans[key] !== false
    },
    toggleTestExecution(executionId) {
      this.expandedTestExecutions[executionId] = !this.expandedTestExecutions[executionId]
      this.expandedTestExecutions = { ...this.expandedTestExecutions }

      // Load test events and results when expanding (if not already loaded)
      if (this.expandedTestExecutions[executionId]) {
        this.loadTestExecutionDetails(executionId)
      }
    },
    isTestExecutionExpanded(executionId) {
      return this.expandedTestExecutions[executionId] || false
    },
    async loadTestExecutionDetails(executionId) {
      // Load test events
      if (!this.testEvents[executionId] && !this.loadingTestEvents[executionId]) {
        this.loadingTestEvents[executionId] = true
        try {
          const events = await api.fetchTestEvents(executionId)
          this.testEvents[executionId] = events
        } catch (e) {
          console.error('Failed to load test events:', e)
          this.testEvents[executionId] = []
        } finally {
          this.loadingTestEvents[executionId] = false
          this.loadingTestEvents = { ...this.loadingTestEvents }
        }
      }

      // Load test results
      if (!this.testResults[executionId] && !this.loadingTestResults[executionId]) {
        this.loadingTestResults[executionId] = true
        try {
          const results = await api.fetchTestResults(executionId)
          this.testResults[executionId] = Array.isArray(results) ? results : []
        } catch (e) {
          console.error('Failed to load test results:', e)
          this.testResults[executionId] = []
        } finally {
          this.loadingTestResults[executionId] = false
          this.loadingTestResults = { ...this.loadingTestResults }
        }
      }
    },
    toggleExecutionSection(executionId, sectionName) {
      const key = `${executionId}-${sectionName}`
      this.expandedExecutionSections[key] = !this.expandedExecutionSections[key]
      this.expandedExecutionSections = { ...this.expandedExecutionSections }
    },
    isExecutionSectionExpanded(executionId, sectionName) {
      const key = `${executionId}-${sectionName}`
      // Default expanded state: eventLog (for in-progress), results (for completed)
      if (this.expandedExecutionSections[key] === undefined) {
        return sectionName === 'eventLog' || sectionName === 'results'
      }
      return this.expandedExecutionSections[key]
    },
    toggleResultsGroup(executionId, status) {
      const key = `${executionId}-${status}`
      this.expandedResultsGroups[key] = !this.expandedResultsGroups[key]
      this.expandedResultsGroups = { ...this.expandedResultsGroups }
    },
    isResultsGroupExpanded(executionId, status) {
      const key = `${executionId}-${status}`
      // Default: expand failed results
      if (this.expandedResultsGroups[key] === undefined) {
        return status === 'FAILED'
      }
      return this.expandedResultsGroups[key]
    },
    toggleResult(resultId) {
      this.expandedResults[resultId] = !this.expandedResults[resultId]
      this.expandedResults = { ...this.expandedResults }
    },
    isResultExpanded(resultId) {
      return this.expandedResults[resultId] || false
    },
    getTestResultsByStatus(executionId, status) {
      const results = this.testResults[executionId]
      if (!results || results.length === 0) return []
      return results.filter(r => r.status === status)
    },
    isExecutionCompleted(status) {
      return status === 'PASSED' || status === 'FAILED'
    },
    groupTestExecutionsByPlan(testExecutions) {
      const grouped = {}
      testExecutions.forEach(execution => {
        const planName = execution.test_plan || 'Unknown Plan'
        if (!grouped[planName]) {
          grouped[planName] = []
        }
        grouped[planName].push(execution)
      })
      return grouped
    },
    getStatusClass(status) {
      switch (status) {
        case 'PASSED': return 'status-passed'
        case 'FAILED': return 'status-failed'
        case 'IN_PROGRESS': return 'status-in-progress'
        case 'NOT_STARTED': return 'status-not-started'
        default: return 'status-unknown'
      }
    },
    getStatusIcon(status) {
      switch (status) {
        case 'PASSED': return '✓'
        case 'FAILED': return '✗'
        case 'IN_PROGRESS': return '⟳'
        case 'NOT_STARTED': return '○'
        default: return '?'
      }
    },
    formatStatus(status) {
      return status.replace(/_/g, ' ').toLowerCase()
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')
    },
    formatDate(dateString) {
      const date = new Date(dateString)
      return date.toLocaleDateString()
    },
    formatDateTime(dateString) {
      const date = new Date(dateString)
      return date.toLocaleString()
    },
    async handleQueryParameters() {
      const { testExecutionId, testResultId } = this.$route.query

      if (!testExecutionId) return

      const executionId = parseInt(testExecutionId)

      // Find the execution in the environments
      let foundExecution = null
      let foundEnvironment = null
      let foundTestPlan = null

      for (const env of this.environments) {
        for (const execution of env.testExecutions) {
          if (execution.id === executionId) {
            foundExecution = execution
            foundEnvironment = env
            foundTestPlan = execution.test_plan || 'Unknown Plan'
            break
          }
        }
        if (foundExecution) break
      }

      if (!foundExecution || !foundEnvironment) {
        console.warn('Test execution not found:', executionId)
        return
      }

      // Expand the hierarchy: environment -> test plans section -> specific plan -> execution
      this.expandedEnvironments[foundEnvironment.id] = true
      this.expandedSections[`${foundEnvironment.id}-testPlans`] = true
      this.expandedTestPlans[`${foundEnvironment.id}-${foundTestPlan}`] = true
      this.expandedTestExecutions[executionId] = true

      // Trigger reactivity
      this.expandedEnvironments = { ...this.expandedEnvironments }
      this.expandedSections = { ...this.expandedSections }
      this.expandedTestPlans = { ...this.expandedTestPlans }
      this.expandedTestExecutions = { ...this.expandedTestExecutions }

      // Load the execution details
      await this.loadTestExecutionDetails(executionId)

      // If testResultId is provided, expand to that specific result
      if (testResultId) {
        const resultId = parseInt(testResultId)

        // Expand the results section
        this.expandedExecutionSections[`${executionId}-results`] = true
        this.expandedExecutionSections = { ...this.expandedExecutionSections }

        // Find the result and its status group
        const results = this.testResults[executionId] || []
        const result = results.find(r => r.id === resultId)

        if (result) {
          // Expand the status group containing this result
          this.expandedResultsGroups[`${executionId}-${result.status}`] = true
          this.expandedResultsGroups = { ...this.expandedResultsGroups }

          // Wait for next tick to ensure DOM is updated
          await this.$nextTick()

          // Scroll to the result
          const resultElement = document.querySelector(`[data-result-id="${resultId}"]`)
          if (resultElement) {
            resultElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
          }
        }
      }
    }
  },
  async mounted() {
    await this.loadData()
    // Handle query parameters after data is loaded
    await this.handleQueryParameters()
  },
  watch: {
    artefactId() {
      this.loadData()
    }
  }
}
</script>

<style scoped>
.artefact-page {
  padding: 24px 0;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.back-button {
  padding: 8px 16px;
  background: white;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  transition: all 0.2s;
}

.back-button:hover {
  background: #f7f7f7;
  border-color: #999;
}

.page-header h1 {
  font-size: 28px;
  font-weight: 300;
  color: #111;
  margin: 0;
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

.artefact-content {
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

.info-sidebar {
  width: 300px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.info-section {
  background: #f7f7f7;
  padding: 16px;
  border-radius: 4px;
}

.info-item {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 14px;
}

.info-item:last-child {
  margin-bottom: 0;
}

.info-item .label {
  font-weight: 500;
  color: #666;
  min-width: 80px;
}

.info-item .value {
  color: #111;
  word-break: break-word;
}

.info-item .link {
  color: #0E8420;
  text-decoration: none;
}

.info-item .link:hover {
  text-decoration: underline;
}

.stage-badge {
  background: #E95420;
  color: white;
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 12px;
  text-transform: capitalize;
}

.filters-section {
  background: #f7f7f7;
  padding: 16px;
  border-radius: 4px;
}

.filters-section h3 {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 12px;
}

.filter-group {
  margin-bottom: 16px;
  border-top: 1px solid #CDCDCD;
  padding-top: 12px;
}

.filter-group:first-child {
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

.environments-container {
  flex: 1;
  min-width: 0;
}

.environments-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.environments-header h2 {
  font-size: 20px;
  font-weight: 500;
  margin: 0;
}

.status-summary {
  font-size: 14px;
  color: #666;
}

.empty-state {
  padding: 32px;
  text-align: center;
  color: #666;
  background: #f7f7f7;
  border-radius: 4px;
}

.environments-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.environment-item {
  border: 1px solid #CDCDCD;
  border-radius: 4px;
  background: white;
}

.environment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  user-select: none;
  background: #f7f7f7;
  border-bottom: 1px solid #CDCDCD;
}

.environment-header:hover {
  background: #e7e7e7;
}

.environment-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
  font-weight: 500;
}

.architecture {
  color: #E95420;
}

.environment-content {
  padding: 16px;
}

.test-plans-section {
  margin-top: 8px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f7f7f7;
  border-radius: 4px;
  cursor: pointer;
  user-select: none;
  font-weight: 500;
  margin-bottom: 8px;
}

.section-header:hover {
  background: #e7e7e7;
}

.test-plans-list {
  padding-left: 16px;
}

.test-plan-item {
  margin-bottom: 12px;
  border-left: 2px solid #CDCDCD;
  padding-left: 12px;
}

.test-plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  background: #f7f7f7;
  border-radius: 4px;
  cursor: pointer;
  user-select: none;
}

.test-plan-header:hover {
  background: #e7e7e7;
}

.plan-name {
  font-weight: 500;
}

.test-executions-list {
  margin-top: 8px;
  padding-left: 12px;
}

.test-execution-item {
  margin-bottom: 8px;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
  background: white;
}

.execution-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  user-select: none;
  background: #f9f9f9;
}

.execution-header:hover {
  background: #f0f0f0;
}

.execution-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
}

.run-number {
  font-weight: 500;
}

.execution-date {
  color: #666;
  font-size: 13px;
}

.execution-details {
  padding: 12px;
  border-top: 1px solid #CDCDCD;
}

.detail-section {
  margin-bottom: 16px;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
  background: white;
}

.detail-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: #f7f7f7;
  cursor: pointer;
  user-select: none;
  font-weight: 500;
  border-radius: 4px 4px 0 0;
}

.detail-section-header:hover {
  background: #e7e7e7;
}

.section-title {
  font-size: 14px;
}

.loading-small {
  padding: 16px;
  text-align: center;
  color: #666;
  font-size: 13px;
}

.empty-state-small {
  padding: 16px;
  text-align: center;
  color: #999;
  font-size: 13px;
  font-style: italic;
}

.event-log,
.metadata-content,
.test-results {
  padding: 12px;
}

.events-table table,
.metadata-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.events-table th {
  text-align: left;
  padding: 8px;
  background: #f7f7f7;
  border-bottom: 2px solid #CDCDCD;
  font-weight: 500;
}

.events-table td {
  padding: 6px 8px;
  border-bottom: 1px solid #e7e7e7;
}

.detail-cell {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.metadata-table td {
  padding: 6px 8px;
  border-bottom: 1px solid #e7e7e7;
}

.metadata-key {
  font-weight: 500;
  color: #666;
  width: 40%;
}

.metadata-value {
  color: #111;
}

.results-group {
  margin-bottom: 12px;
}

.results-group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f7f7f7;
  border-radius: 4px;
  cursor: pointer;
  user-select: none;
}

.results-group-header:hover {
  background: #e7e7e7;
}

.status-label {
  font-weight: 500;
}

.count {
  color: #666;
  font-size: 13px;
}

.results-list {
  padding: 8px 0;
}

.result-item {
  margin-bottom: 8px;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
  background: white;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  user-select: none;
  background: #fafafa;
}

.result-header:hover {
  background: #f0f0f0;
}

.result-name {
  flex: 1;
  font-size: 13px;
  font-weight: 500;
}

.issues-count {
  color: #C7162B;
  font-size: 12px;
}

.result-details {
  padding: 12px;
  border-top: 1px solid #CDCDCD;
}

.result-detail-item {
  margin-bottom: 12px;
  font-size: 13px;
}

.result-detail-item:last-child {
  margin-bottom: 0;
}

.result-detail-item .label {
  font-weight: 500;
  color: #666;
  display: block;
  margin-bottom: 4px;
}

.io-log {
  background: #f7f7f7;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
  padding: 12px;
  font-family: 'Ubuntu Mono', 'Courier New', monospace;
  font-size: 12px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.issues-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.issues-list li {
  margin-bottom: 4px;
}

.issue-link {
  color: #0E8420;
  text-decoration: none;
  font-size: 13px;
}

.issue-link:hover {
  text-decoration: underline;
}

.basic-info {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e7e7e7;
}

.detail-item {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 14px;
}

.detail-item:last-child {
  margin-bottom: 0;
}

.detail-item .label {
  font-weight: 500;
  color: #666;
  min-width: 80px;
}

.detail-item .link {
  color: #0E8420;
  text-decoration: none;
  word-break: break-all;
}

.detail-item .link:hover {
  text-decoration: underline;
}

.status-icon {
  font-size: 16px;
  font-weight: bold;
}

.status-icon.status-passed {
  color: #0E8420;
}

.status-icon.status-failed {
  color: #C7162B;
}

.status-icon.status-in-progress {
  color: #0073E6;
}

.status-icon.status-not-started {
  color: #999;
}

.status-badge {
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 12px;
  font-weight: 500;
  text-transform: capitalize;
}

.status-badge.status-passed {
  background: #E5F5E7;
  color: #0E8420;
}

.status-badge.status-failed {
  background: #FDEAEA;
  color: #C7162B;
}

.status-badge.status-in-progress {
  background: #E5F2FA;
  color: #0073E6;
}

.status-badge.status-not-started {
  background: #f0f0f0;
  color: #666;
}
</style>
