<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1>{{ title }}</h1>
      <div class="view-toggle">
        <button
          @click="viewMode = 'list'"
          :class="['toggle-button', { active: viewMode === 'list' }]"
          title="Table view"
        >
          ☰
        </button>
        <button
          @click="viewMode = 'grid'"
          :class="['toggle-button', { active: viewMode === 'grid' }]"
          title="Grid view"
        >
          ▦
        </button>
      </div>
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
    async loadArtefacts() {
      this.loading = true
      this.error = null

      try {
        this.artefacts = await api.fetchArtefacts(this.family)
      } catch (e) {
        this.error = 'Failed to load artefacts: ' + e.message
        console.error('Failed to load artefacts:', e)
      } finally {
        this.loading = false
      }
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
  padding: 8px 16px;
  background: white;
  border: none;
  border-right: 1px solid #CDCDCD;
  cursor: pointer;
  font-size: 18px;
  color: #E95420;
  transition: all 0.2s;
}

.toggle-button:last-child {
  border-right: none;
}

.toggle-button:hover {
  background: #f7f7f7;
}

.toggle-button.active {
  background: #E95420;
  color: white;
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
.error {
  padding: 32px;
  text-align: center;
  color: #666;
}

.error {
  color: #C7162B;
}
</style>
