<template>
  <div class="search-multiselect">
    <!-- Collapsible header -->
    <div class="multiselect-header" @click="toggle">
      <span class="header-title">
        {{ title }} ({{ selectedArtefacts.length }} selected)
      </span>
      <span class="expand-icon">{{ isExpanded ? '▲' : '▼' }}</span>
    </div>

    <!-- Expanded content -->
    <div v-if="isExpanded" class="multiselect-content">
      <!-- Search input -->
      <input
        v-model="searchQuery"
        type="text"
        class="search-input"
        :placeholder="placeholder"
        @input="handleSearchInput"
      />

      <!-- Loading state -->
      <div v-if="isLoading" class="loading-state">
        <span class="loading-spinner"></span>
        <span>Searching...</span>
      </div>

      <!-- Error state -->
      <div v-if="error" class="error-state">
        <span>Error loading suggestions</span>
      </div>

      <!-- Search results dropdown -->
      <div v-if="suggestions.length > 0 && !isLoading" class="suggestions-dropdown">
        <div
          v-for="suggestion in suggestions"
          :key="suggestion"
          class="suggestion-item"
          @click="selectArtefact(suggestion)"
        >
          {{ suggestion }}
        </div>
      </div>

      <!-- Selected items with checkboxes -->
      <div v-if="selectedArtefacts.length > 0" class="selected-items">
        <div
          v-for="artefact in selectedArtefacts"
          :key="artefact"
          class="selected-item"
        >
          <label class="checkbox-label">
            <input
              type="checkbox"
              :checked="true"
              @change="deselectArtefact(artefact)"
            />
            <span class="item-name">{{ artefact }}</span>
          </label>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SearchMultiSelect',
  props: {
    title: {
      type: String,
      required: true
    },
    placeholder: {
      type: String,
      default: 'Type 2+ characters to search...'
    },
    modelValue: {
      type: Array,
      default: () => []
    },
    searchFunction: {
      type: Function,
      required: true
    }
  },
  emits: ['update:modelValue'],
  data() {
    return {
      isExpanded: false,
      searchQuery: '',
      suggestions: [],
      isLoading: false,
      error: null,
      debounceTimeout: null
    }
  },
  computed: {
    selectedArtefacts() {
      return this.modelValue
    }
  },
  watch: {
    // Auto-expand if there are initial selections
    selectedArtefacts: {
      immediate: true,
      handler(newVal) {
        if (newVal.length > 0 && !this.isExpanded) {
          this.isExpanded = true
        }
      }
    }
  },
  methods: {
    toggle() {
      this.isExpanded = !this.isExpanded
      if (this.isExpanded) {
        // Focus the search input when expanded
        this.$nextTick(() => {
          const input = this.$el.querySelector('.search-input')
          if (input) input.focus()
        })
      }
    },
    handleSearchInput() {
      // Clear previous timeout
      if (this.debounceTimeout) {
        clearTimeout(this.debounceTimeout)
      }

      // Only search if we have 2+ characters
      if (this.searchQuery.trim().length < 2) {
        this.suggestions = []
        return
      }

      // Debounce the search
      this.debounceTimeout = setTimeout(() => {
        this.performSearch()
      }, 300) // 300ms debounce
    },
    async performSearch() {
      this.isLoading = true
      this.error = null

      try {
        const results = await this.searchFunction(this.searchQuery.trim())
        this.suggestions = results || []
      } catch (e) {
        this.error = 'Search failed'
        console.error('Search failed:', e)
        this.suggestions = []
      } finally {
        this.isLoading = false
      }
    },
    selectArtefact(artefact) {
      if (!this.selectedArtefacts.includes(artefact)) {
        const updated = [...this.selectedArtefacts, artefact]
        this.$emit('update:modelValue', updated)
      }
      // Clear search after selection
      this.searchQuery = ''
      this.suggestions = []
    },
    deselectArtefact(artefact) {
      const updated = this.selectedArtefacts.filter(a => a !== artefact)
      this.$emit('update:modelValue', updated)
    }
  }
}
</script>

<style scoped>
.search-multiselect {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.multiselect-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: white;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.multiselect-header:hover {
  background: #f7f7f7;
  border-color: #999;
}

.header-title {
  font-size: 14px;
  color: #111;
}

.expand-icon {
  color: #666;
  font-size: 12px;
}

.multiselect-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px;
  background: white;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
}

.search-input {
  padding: 8px 12px;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
  font-size: 14px;
}

.search-input:focus {
  outline: none;
  border-color: #0E8420;
}

.loading-state,
.error-state {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  font-size: 14px;
  color: #666;
}

.loading-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #0E8420;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-state {
  color: #C7162B;
}

.suggestions-dropdown {
  max-height: 250px;
  overflow-y: auto;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
  background: white;
}

.suggestion-item {
  padding: 8px 12px;
  cursor: pointer;
  font-size: 14px;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.2s;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-item:hover {
  background: #f7f7f7;
}

.selected-items {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.selected-item {
  display: flex;
  align-items: center;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #111;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  cursor: pointer;
}

.item-name {
  user-select: none;
}
</style>
