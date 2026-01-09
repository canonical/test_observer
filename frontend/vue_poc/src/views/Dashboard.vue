<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1>{{ title }}</h1>
    </div>
    
    <div class="dashboard-body">
      <div class="filters-toggle">
        <button @click="showFilters = !showFilters" class="filter-button">
          <span class="filter-icon">⚙</span>
        </button>
      </div>
      
      <div v-if="showFilters" class="filters-panel">
        <h3>Filters</h3>
        <input 
          v-model="searchQuery" 
          type="text" 
          placeholder="Search by name"
          class="search-input"
        />
      </div>
      
      <div class="content-area">
        <div v-if="loading" class="loading">Loading artefacts...</div>
        <div v-else-if="error" class="error">{{ error }}</div>
        <div v-else class="artefacts-grid">
          <div 
            v-for="artefact in filteredArtefacts" 
            :key="artefact.id"
            class="artefact-card"
            @click="navigateToArtefact(artefact.id)"
          >
            <h3>{{ artefact.name }}</h3>
            <p class="artefact-version">Version: {{ artefact.version }}</p>
            <div class="artefact-status">
              <span :class="['status-badge', getStatusClass(artefact.status)]">
                {{ artefact.status }}
              </span>
            </div>
          </div>
          
          <div v-if="filteredArtefacts.length === 0" class="no-results">
            No artefacts found{{ searchQuery ? ' matching your search' : '' }}.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Dashboard',
  data() {
    return {
      showFilters: false,
      searchQuery: '',
      loading: false,
      error: null,
      artefacts: []
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
      if (!this.searchQuery) return this.artefacts
      
      const query = this.searchQuery.toLowerCase()
      return this.artefacts.filter(a => 
        a.name.toLowerCase().includes(query) ||
        a.version.toLowerCase().includes(query)
      )
    }
  },
  methods: {
    navigateToArtefact(artefactId) {
      this.$router.push(`/${this.family}s/${artefactId}`)
    },
    getStatusClass(status) {
      const statusMap = {
        'PASSED': 'status-passed',
        'FAILED': 'status-failed',
        'IN_PROGRESS': 'status-progress',
        'PENDING': 'status-pending'
      }
      return statusMap[status] || 'status-unknown'
    },
    async loadArtefacts() {
      this.loading = true
      this.error = null
      
      try {
        // Mock data for demonstration - in production this would call the API
        await new Promise(resolve => setTimeout(resolve, 500))
        
        this.artefacts = this.generateMockArtefacts()
      } catch (e) {
        this.error = 'Failed to load artefacts: ' + e.message
      } finally {
        this.loading = false
      }
    },
    generateMockArtefacts() {
      const statuses = ['PASSED', 'FAILED', 'IN_PROGRESS', 'PENDING']
      const count = 12
      
      return Array.from({ length: count }, (_, i) => ({
        id: i + 1,
        name: `${this.family}-example-${i + 1}`,
        version: `1.${i}.0`,
        status: statuses[i % statuses.length]
      }))
    }
  },
  watch: {
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
  margin-bottom: 24px;
}

.dashboard-header h1 {
  font-size: 28px;
  font-weight: 300;
  color: #111;
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

.content-area {
  flex: 1;
  min-width: 0;
}

.loading,
.error,
.no-results {
  padding: 32px;
  text-align: center;
  color: #666;
}

.error {
  color: #C7162B;
}

.artefacts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.artefact-card {
  background: white;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.artefact-card:hover {
  border-color: #0E8420;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.artefact-card h3 {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
  color: #111;
}

.artefact-version {
  font-size: 14px;
  color: #666;
  margin-bottom: 12px;
}

.artefact-status {
  display: flex;
  gap: 8px;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
}

.status-passed {
  background: #0E8420;
  color: white;
}

.status-failed {
  background: #C7162B;
  color: white;
}

.status-progress {
  background: #0066CC;
  color: white;
}

.status-pending {
  background: #666;
  color: white;
}

.status-unknown {
  background: #CDCDCD;
  color: #111;
}
</style>
