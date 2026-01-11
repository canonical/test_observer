<template>
  <div class="issue-page">
    <div class="page-header">
      <button @click="$router.push('/issues')" class="back-button">← Back to Issues</button>
      <h1>Issue #{{ issueId }}</h1>
    </div>

    <div v-if="loading" class="loading">Loading issue...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="issue-content">
      <div class="issue-card">
        <div class="issue-header">
          <h2>{{ issue.title }}</h2>
          <span :class="['issue-status', issue.open ? 'status-open' : 'status-closed']">
            {{ issue.open ? 'Open' : 'Closed' }}
          </span>
        </div>
        <p class="issue-description">{{ issue.description }}</p>
      </div>

      <div class="section">
        <h3>Comments</h3>
        <p class="placeholder">Comments would appear here.</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'IssuePage',
  data() {
    return {
      loading: false,
      error: null,
      issue: null
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
        await new Promise(resolve => setTimeout(resolve, 300))

        // Mock data
        const issues = [
          { id: 1, title: 'Test failure in snap-example-1', description: 'Intermittent test failure observed in the latest build.', open: true },
          { id: 2, title: 'Missing test coverage', description: 'Need to add tests for new features introduced in version 2.0.', open: true },
          { id: 3, title: 'Performance regression', description: 'Tests taking longer than expected after recent changes.', open: false }
        ]

        this.issue = issues.find(i => i.id === this.issueId) || {
          id: this.issueId,
          title: `Issue ${this.issueId}`,
          description: 'Issue details not available.',
          open: true
        }
      } catch (e) {
        this.error = 'Failed to load issue: ' + e.message
      } finally {
        this.loading = false
      }
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
}

.back-button:hover {
  background: #f7f7f7;
  border-color: #999;
}

.page-header h1 {
  font-size: 28px;
  font-weight: 300;
}

.loading,
.error {
  padding: 32px;
  text-align: center;
}

.error {
  color: #C7162B;
}

.issue-card {
  background: white;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
  padding: 24px;
  margin-bottom: 24px;
}

.issue-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.issue-header h2 {
  font-size: 20px;
  font-weight: 500;
}

.issue-status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
}

.status-open {
  background: #0E8420;
  color: white;
}

.status-closed {
  background: #666;
  color: white;
}

.issue-description {
  font-size: 16px;
  color: #111;
  line-height: 1.6;
}

.section {
  background: white;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
  padding: 24px;
}

.section h3 {
  font-size: 18px;
  font-weight: 500;
  margin-bottom: 12px;
}

.placeholder {
  color: #666;
  font-style: italic;
}
</style>
