<template>
  <div class="test-results-page">
    <h1>Search Test Results</h1>
    <div class="search-section">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search for test results..."
        class="search-input"
        @keyup.enter="search"
      />
      <button @click="search" class="search-button">Search</button>
    </div>

    <div v-if="searched && results.length === 0" class="no-results">
      No results found.
    </div>

    <div v-if="results.length > 0" class="results">
      <p class="results-count">Found {{ results.length }} results</p>
      <div class="results-list">
        <div v-for="result in results" :key="result.id" class="result-item">
          <h3>{{ result.name }}</h3>
          <p>{{ result.description }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TestResultsPage',
  data() {
    return {
      searchQuery: '',
      searched: false,
      results: []
    }
  },
  methods: {
    search() {
      this.searched = true
      // Mock search - would call API in production
      this.results = []
    }
  }
}
</script>

<style scoped>
.test-results-page {
  padding: 24px 0;
}

h1 {
  font-size: 28px;
  font-weight: 300;
  margin-bottom: 24px;
}

.search-section {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.search-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
  font-size: 16px;
}

.search-input:focus {
  outline: none;
  border-color: #0E8420;
}

.search-button {
  padding: 12px 24px;
  background: #0E8420;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
}

.search-button:hover {
  background: #0a6617;
}

.no-results,
.results-count {
  padding: 16px;
  color: #666;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-item {
  background: white;
  border: 1px solid #CDCDCD;
  border-radius: 4px;
  padding: 16px;
}

.result-item h3 {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 4px;
}
</style>
