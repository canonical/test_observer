<template>
  <div class="grid-view">
    <div v-if="artefacts.length === 0" class="no-results">
      No artefacts found.
    </div>
    <div v-else class="stages-container">
      <div v-for="stage in stages" :key="stage" class="stage-column">
        <h3 class="stage-title">{{ getStageTitle(stage) }}</h3>
        <div class="artefacts-list">
          <div
            v-for="artefact in getArtefactsForStage(stage)"
            :key="artefact.id"
            class="artefact-card"
            @click="$emit('artefact-click', artefact.id)"
          >
            <h4 class="artefact-name">{{ artefact.name }}</h4>
            <div class="artefact-info">
              <p>version: {{ artefact.version }}</p>
              <p v-if="artefact.track">track: {{ artefact.track }}</p>
              <p v-if="artefact.store">store: {{ artefact.store }}</p>
              <p v-if="artefact.branch">branch: {{ artefact.branch }}</p>
              <p v-if="artefact.series">series: {{ artefact.series }}</p>
              <p v-if="artefact.repo">repo: {{ artefact.repo }}</p>
              <p v-if="artefact.source">source: {{ artefact.source }}</p>
              <p v-if="artefact.os">os: {{ artefact.os }}</p>
              <p v-if="artefact.release">release: {{ artefact.release }}</p>
              <p v-if="artefact.owner">owner: {{ artefact.owner }}</p>
            </div>
            <div class="artefact-footer">
              <span :class="['status-badge', getStatusClass(artefact.status)]">
                {{ getStatusName(artefact.status) }}
              </span>
              <span v-if="artefact.due_date" class="due-date">
                Due {{ formatDueDate(artefact.due_date) }}
              </span>
              <span class="assignee" :title="artefact.assignee?.name || 'Unassigned'">
                {{ getInitials(artefact.assignee?.name) }}
                <span class="review-count">
                  {{ artefact.completed_environment_reviews_count }}/{{ artefact.all_environment_reviews_count }}
                </span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { FAMILY_STAGES, STATUS_NAMES } from '../services/api'

export default {
  name: 'ArtefactsGridView',
  props: {
    artefacts: {
      type: Array,
      required: true
    },
    family: {
      type: String,
      required: true
    }
  },
  emits: ['artefact-click'],
  computed: {
    stages() {
      return FAMILY_STAGES[this.family] || []
    }
  },
  methods: {
    getStageTitle(stage) {
      if (!stage && this.family === 'deb') return 'PPAs'
      if (!stage) return 'Unknown'
      return stage.charAt(0).toUpperCase() + stage.slice(1)
    },
    getArtefactsForStage(stage) {
      return this.artefacts.filter(a => a.stage === stage)
    },
    formatDueDate(dueDate) {
      if (!dueDate) return ''

      const date = new Date(dueDate)
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
      // Use UTC to match Flutter behavior which uses the date components directly
      return `${monthNames[date.getUTCMonth()]} ${date.getUTCDate()}`
    },
    getStatusClass(status) {
      const statusMap = {
        'APPROVED': 'status-approved',
        'MARKED_AS_FAILED': 'status-rejected',
        'UNDECIDED': 'status-undecided'
      }
      return statusMap[status] || 'status-undecided'
    },
    getStatusName(status) {
      return STATUS_NAMES[status] || status
    },
    getInitials(name) {
      if (!name) return '?'
      return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    }
  }
}
</script>

<style scoped>
.grid-view {
  width: 100%;
}

.stages-container {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding-bottom: 16px;
}

.stage-column {
  flex: 0 0 320px;
  min-width: 320px;
}

.stage-title {
  font-size: 20px;
  font-weight: 400;
  margin-bottom: 16px;
  color: #111;
}

.artefacts-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.artefact-card {
  background: white;
  border: 1px solid #CDCDCD;
  border-radius: 2px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
  min-height: 180px;
  display: flex;
  flex-direction: column;
}

.artefact-card:hover {
  border-color: #0E8420;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.artefact-name {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
  color: #111;
}

.artefact-info {
  flex: 1;
  font-size: 14px;
  color: #111;
  line-height: 1.4;
}

.artefact-info p {
  margin: 2px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.artefact-footer {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 12px;
  padding-top: 8px;
  border-top: 1px solid #E5E5E5;
}

.status-badge {
  padding: 2px 6px;
  border-radius: 2px;
  font-size: 11px;
  font-weight: 500;
  flex-shrink: 0;
}

.status-approved {
  color: #0E8420;
}

.status-rejected {
  color: #C7162B;
}

.status-undecided {
  color: #666;
}

.due-date {
  font-size: 11px;
  color: #C7162B;
  flex-shrink: 0;
}

.assignee {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 500;
  background: #E5E5E5;
  padding: 4px 8px;
  border-radius: 12px;
  color: #111;
}

.review-count {
  font-size: 10px;
  color: #666;
}

.no-results {
  padding: 32px;
  text-align: center;
  color: #666;
}
</style>
