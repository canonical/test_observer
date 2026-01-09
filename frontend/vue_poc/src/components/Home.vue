<template>
  <div class="home">
    <h2>Welcome to Test Observer Vue.js PoC</h2>
    <div class="info-card">
      <p>This is a proof-of-concept Vue.js rewrite of the Test Observer frontend.</p>
      <p>The original Flutter frontend is still accessible at <a href="/">the root path (/)</a>.</p>
      <p>This Vue.js version is served from <strong>/vue_poc/</strong></p>
    </div>
    
    <div class="status-section">
      <h3>Status</h3>
      <ul>
        <li>✅ Vue.js 3 setup complete</li>
        <li>✅ Vue Router configured with base path</li>
        <li>✅ Vite build system</li>
        <li>✅ Served alongside Flutter UI</li>
      </ul>
    </div>

    <div class="links-section">
      <h3>Quick Links</h3>
      <div class="link-buttons">
        <a href="/" class="button">Flutter UI (Original)</a>
        <a href="/vue_poc/" class="button button-primary">Vue.js UI (PoC)</a>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Home'
}
</script>

<style scoped>
.home {
  animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

h2 {
  color: #2c3e50;
  margin-bottom: 1.5rem;
  font-size: 2rem;
}

h3 {
  color: #2c3e50;
  margin-bottom: 1rem;
  font-size: 1.5rem;
}

.info-card {
  background: #f8f9fa;
  border-left: 4px solid #42b983;
  padding: 1.5rem;
  margin-bottom: 2rem;
  border-radius: 4px;
}

.info-card p {
  margin-bottom: 0.5rem;
}

.info-card a {
  color: #42b983;
  text-decoration: none;
  font-weight: 500;
}

.info-card a:hover {
  text-decoration: underline;
}

.status-section {
  margin-bottom: 2rem;
}

.status-section ul {
  list-style: none;
  padding: 0;
}

.status-section li {
  padding: 0.5rem 0;
  font-size: 1.1rem;
}

.links-section {
  margin-top: 2rem;
}

.link-buttons {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.button {
  display: inline-block;
  padding: 0.75rem 1.5rem;
  background: #e9ecef;
  color: #495057;
  text-decoration: none;
  border-radius: 4px;
  font-weight: 500;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.button:hover {
  background: #dee2e6;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.button-primary {
  background: #42b983;
  color: white;
}

.button-primary:hover {
  background: #359268;
}
</style>
