<template>
  <div class="table-view">
    <div v-if="artefacts.length === 0" class="no-results">
      No artefacts found.
    </div>
    <div v-else class="table-container">
      <table class="artefacts-table">
        <thead>
          <tr>
            <th v-for="column in columns" :key="column.key" :style="{ flex: column.flex }">
              {{ column.label }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="artefact in artefacts"
            :key="artefact.id"
            @click="$emit('artefact-click', artefact.id)"
            class="artefact-row"
          >
            <td :style="{ flex: 2 }">{{ artefact.name }}</td>
            <td :style="{ flex: 2 }">{{ artefact.version }}</td>
            <td v-if="family === 'snap' || family === 'charm'" :style="{ flex: 1 }">{{ artefact.track }}</td>
            <td v-if="family === 'snap' || family === 'charm'" :style="{ flex: 1 }">{{ getStageName(artefact.stage) }}</td>
            <td v-if="family === 'snap' || family === 'charm'" :style="{ flex: 1 }">{{ artefact.branch }}</td>
            <td v-if="family === 'deb'" :style="{ flex: 1 }">{{ artefact.series }}</td>
            <td v-if="family === 'deb'" :style="{ flex: 1 }">{{ artefact.repo }}</td>
            <td v-if="family === 'deb'" :style="{ flex: 1 }">{{ getStageName(artefact.stage) }}</td>
            <td v-if="family === 'deb'" :style="{ flex: 2 }">{{ artefact.source }}</td>
            <td v-if="family === 'image'" :style="{ flex: 1 }">{{ artefact.os }}</td>
            <td v-if="family === 'image'" :style="{ flex: 1 }">{{ artefact.release }}</td>
            <td v-if="family === 'image'" :style="{ flex: 1 }">{{ getStageName(artefact.stage) }}</td>
            <td :style="{ flex: 1 }">{{ formatDueDate(artefact.due_date) }}</td>
            <td :style="{ flex: 1 }">{{ artefact.all_environment_reviews_count - artefact.completed_environment_reviews_count }}</td>
            <td :style="{ flex: 1 }">
              <span :class="['status-badge', getStatusClass(artefact.status)]">
                {{ getStatusName(artefact.status) }}
              </span>
            </td>
            <td :style="{ flex: 1 }">{{ artefact.assignee?.name || 'N/A' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import { STATUS_COLORS, STATUS_NAMES } from '../services/api'

export default {
  name: 'ArtefactsTableView',
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
    columns() {
      const baseColumns = [
        { key: 'name', label: 'Name', flex: 2 },
        { key: 'version', label: 'Version', flex: 2 }
      ]

      const familyColumns = {
        snap: [
          { key: 'track', label: 'Track', flex: 1 },
          { key: 'risk', label: 'Risk', flex: 1 },
          { key: 'branch', label: 'Branch', flex: 1 }
        ],
        deb: [
          { key: 'series', label: 'Series', flex: 1 },
          { key: 'repo', label: 'Repo', flex: 1 },
          { key: 'pocket', label: 'Pocket', flex: 1 },
          { key: 'source', label: 'Source', flex: 2 }
        ],
        charm: [
          { key: 'track', label: 'Track', flex: 1 },
          { key: 'risk', label: 'Risk', flex: 1 },
          { key: 'branch', label: 'Branch', flex: 1 }
        ],
        image: [
          { key: 'os', label: 'OS', flex: 1 },
          { key: 'release', label: 'Release', flex: 1 },
          { key: 'stage', label: 'Stage', flex: 1 }
        ]
      }

      const endColumns = [
        { key: 'due_date', label: 'Due date', flex: 1 },
        { key: 'reviews_remaining', label: 'Reviews remaining', flex: 1 },
        { key: 'status', label: 'Status', flex: 1 },
        { key: 'assignee', label: 'Assignee', flex: 1 }
      ]

      return [...baseColumns, ...(familyColumns[this.family] || []), ...endColumns]
    }
  },
  methods: {
    getStageName(stage) {
      if (!stage) return ''
      return stage.charAt(0).toUpperCase() + stage.slice(1)
    },
    formatDueDate(dueDate) {
      if (!dueDate) return ''

      const date = new Date(dueDate)
      const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                          'July', 'August', 'September', 'October', 'November', 'December']
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
    }
  }
}
</script>

<style scoped>
.table-view {
  width: 100%;
}

.table-container {
  width: 100%;
  max-width: 1300px;
  overflow-x: auto;
}

.artefacts-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
}

.artefacts-table thead {
  border-bottom: 1px solid #CDCDCD;
}

.artefacts-table th {
  padding: 16px 8px;
  text-align: left;
  font-size: 16px;
  font-weight: 500;
  color: #111;
  white-space: nowrap;
}

.artefacts-table tbody tr {
  border-bottom: 1px solid #E5E5E5;
}

.artefact-row {
  cursor: pointer;
  transition: background-color 0.2s;
}

.artefact-row:hover {
  background-color: #f7f7f7;
}

.artefacts-table td {
  padding: 12px 8px;
  font-size: 14px;
  color: #111;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.artefacts-table th,
.artefacts-table td {
  display: inline-flex;
  align-items: center;
}

.artefacts-table tr {
  display: flex;
  width: 100%;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  display: inline-block;
  border: 1px solid currentColor;
}

.status-approved {
  color: #0E8420;
  background: transparent;
}

.status-rejected {
  color: #C7162B;
  background: transparent;
}

.status-undecided {
  color: #666;
  background: transparent;
}

.no-results {
  padding: 32px;
  text-align: center;
  color: #666;
}
</style>
