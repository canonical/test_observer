<template>
  <div class="issues-page">
    <h1>Issues</h1>
    
    <div class="issues-toolbar">
      <input 
        v-model="searchQuery"
        type="text"
        placeholder="Search issues..."
        class="search-input"
      />
    </div>
    
    <div class="issues-list">
      <div 
        v-for="issue in filteredIssues" 
        :key="issue.id"
        class="issue-item"
        @click="$router.push(`/issues/${issue.id}`)"
      >
        <div class="issue-header">
          <h3>#{{ issue.id }} - {{ issue.title }}</h3>
          <span :class="['issue-status', issue.open ? 'status-open' : 'status-closed']">
            {{ issue.open ? 'Open' : 'Closed' }}
          </span>
        </div>
        <p class="issue-description">{{ issue.description }}</p>
      </div>
      
      <div v-if="filteredIssues.length === 0" class="no-results">
        No issues found.
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'IssuesPage',
  data() {
    return {
      searchQuery: '',
      issues: [
        {
          id: 1,
          title: 'Test failure in snap-example-1',
          description: 'Intermittent test failure observed',
          open: true
        },
        {
          id: 2,
          title: 'Missing test coverage',
          description: 'Need to add tests for new features',
          open: true
        },
        {
          id: 3,
          title: 'Performance regression',
          description: 'Tests taking longer than expected',
          open: false
        }
      ]
    }
  },
  computed: {
    filteredIssues() {
      if (!this.searchQuery) return this.issues
      
      const query = this.searchQuery.toLowerCase()
      return this.issues.filter(i =>
        i.title.toLowerCase().includes(query) ||
        i.description.toLowerCase().includes(query)
      )
    }
  }
}
</script>

<style scoped>
.issues-page {
  padding: 24px 0;
}

h1 {
  font-size: 28px;
  font-weight: 300;
  margin-bottom: 24px;
}

.issues-toolbar {
  margin-bottom: 16px;
}

.search-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
  font-size: 16px;
}

.search-input:focus {
  outline: none;
  border-color: #0E8420;
}

.issues-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.issue-item {
  background: white;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.issue-item:hover {
  border-color: #0E8420;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.issue-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.issue-header h3 {
  font-size: 16px;
  font-weight: 500;
  color: #111;
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
  font-size: 14px;
  color: #666;
}

.no-results {
  padding: 32px;
  text-align: center;
  color: #666;
}
</style>
