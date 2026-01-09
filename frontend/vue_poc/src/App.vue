<template>
  <div id="app">
    <Navbar />
    <main>
      <div class="content-container">
        <router-view></router-view>
      </div>
    </main>
  </div>
</template>

<script>
import Navbar from './components/Navbar.vue'

export default {
  name: 'App',
  components: {
    Navbar
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: Ubuntu, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Cantarell, sans-serif;
  line-height: 1.6;
  color: #111;
  background: #fff;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

main {
  flex: 1;
  display: flex;
  justify-content: center;
}

.content-container {
  width: 100%;
  max-width: 1200px;
  padding: 0 24px;
}
</style>
