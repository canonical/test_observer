import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import Dashboard from './views/Dashboard.vue'
import ArtefactPage from './views/ArtefactPage.vue'
import TestResultsPage from './views/TestResultsPage.vue'
import IssuesPage from './views/IssuesPage.vue'
import IssuePage from './views/IssuePage.vue'

const routes = [
  { path: '/', redirect: '/snaps' },
  { path: '/snaps', name: 'snaps', component: Dashboard, meta: { family: 'snap' } },
  { path: '/snaps/:artefactId', name: 'snap-artefact', component: ArtefactPage, meta: { family: 'snap' } },
  { path: '/debs', name: 'debs', component: Dashboard, meta: { family: 'deb' } },
  { path: '/debs/:artefactId', name: 'deb-artefact', component: ArtefactPage, meta: { family: 'deb' } },
  { path: '/charms', name: 'charms', component: Dashboard, meta: { family: 'charm' } },
  { path: '/charms/:artefactId', name: 'charm-artefact', component: ArtefactPage, meta: { family: 'charm' } },
  { path: '/images', name: 'images', component: Dashboard, meta: { family: 'image' } },
  { path: '/images/:artefactId', name: 'image-artefact', component: ArtefactPage, meta: { family: 'image' } },
  { path: '/test-results', name: 'test-results', component: TestResultsPage },
  { path: '/issues', name: 'issues', component: IssuesPage },
  { path: '/issues/:issueId', name: 'issue', component: IssuePage }
]

const router = createRouter({
  history: createWebHistory('/vue_poc/'),
  routes
})

const app = createApp(App)
app.use(router)
app.mount('#app')
