<template>
  <div class="artefact-page">
    <div class="page-header">
      <button @click="$router.back()" class="back-button">← Back</button>
      <h1>Artefact #{{ artefactId }}</h1>
    </div>
    
    <div v-if="loading" class="loading">Loading artefact details...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="artefact-content">
      <div class="info-card">
        <h2>{{ artefact.name }}</h2>
        <div class="info-grid">
          <div class="info-item">
            <span class="label">Version:</span>
            <span class="value">{{ artefact.version }}</span>
          </div>
          <div class="info-item">
            <span class="label">Status:</span>
            <span :class="['status-badge', getStatusClass(artefact.status)]">
              {{ artefact.status }}
            </span>
          </div>
          <div class="info-item">
            <span class="label">Family:</span>
            <span class="value">{{ family }}</span>
          </div>
        </div>
      </div>
      
      <div class="section">
        <h3>Test Executions</h3>
        <p class="placeholder">Test execution details would appear here.</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ArtefactPage',
  data() {
    return {
      loading: false,
      error: null,
      artefact: null
    }
  },
  computed: {
    artefactId() {
      return parseInt(this.$route.params.artefactId)
    },
    family() {
      return this.$route.meta.family
    }
  },
  methods: {
    getStatusClass(status) {
      const statusMap = {
        'PASSED': 'status-passed',
        'FAILED': 'status-failed',
        'IN_PROGRESS': 'status-progress',
        'PENDING': 'status-pending'
      }
      return statusMap[status] || 'status-unknown'
    },
    async loadArtefact() {
      this.loading = true
      this.error = null
      
      try {
        await new Promise(resolve => setTimeout(resolve, 300))
        
        // Mock data
        const statuses = ['PASSED', 'FAILED', 'IN_PROGRESS', 'PENDING']
        this.artefact = {
          id: this.artefactId,
          name: `${this.family}-example-${this.artefactId}`,
          version: `1.${this.artefactId}.0`,
          status: statuses[this.artefactId % statuses.length]
        }
      } catch (e) {
        this.error = 'Failed to load artefact: ' + e.message
      } finally {
        this.loading = false
      }
    }
  },
  mounted() {
    this.loadArtefact()
  },
  watch: {
    artefactId() {
      this.loadArtefact()
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

.info-card {
  background: white;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
  padding: 24px;
  margin-bottom: 24px;
}

.info-card h2 {
  font-size: 20px;
  font-weight: 500;
  margin-bottom: 16px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.label {
  font-size: 12px;
  color: #666;
  text-transform: uppercase;
  font-weight: 500;
}

.value {
  font-size: 16px;
  color: #111;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
  display: inline-block;
  width: fit-content;
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

.section {
  background: white;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
  padding: 24px;
  margin-bottom: 16px;
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
