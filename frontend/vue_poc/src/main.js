import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import Home from './components/Home.vue'

const routes = [
  { path: '/', component: Home }
]

const router = createRouter({
  history: createWebHistory('/vue_poc/'),
  routes
})

const app = createApp(App)
app.use(router)
app.mount('#app')
