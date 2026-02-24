<template>
  <div>
    <div class="dashboard-header">
      <h1>Snap Update Verification</h1>
    </div>
    
    <div v-if="pending">Loading...</div>
    <div v-else-if="error">Error: {{ error }}</div>
    <div v-else>
      <div v-for="artefact in artefacts" :key="artefact.id" class="card">
        <h3>{{ artefact.name }}</h3>
        <p>ID: {{ artefact.id }}</p>
        <p>Version: {{ artefact.version }}</p>
        <p>Track: {{ artefact.track }}</p>
        <p>Store: {{ artefact.store }}</p>
        <p>Status: {{ artefact.status }}</p>
      </div>
      <div v-if="artefacts && artefacts.length === 0">No artefacts found.</div>
    </div>
  </div>
</template>

<script setup>
const { data: artefacts, pending, error } = await useFetch('http://localhost:30000/v1/artefacts?family=snap', {
  lazy: true,
  server: false
})
</script>
