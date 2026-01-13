<template>
  <nav class="navbar">
    <div class="navbar-content">
      <div class="navbar-logo">
        <img src="/canonical.png" alt="Canonical" />
      </div>

      <div class="navbar-links">
        <router-link to="/snaps" class="nav-link">Snap Testing</router-link>
        <router-link to="/debs" class="nav-link">Deb Testing</router-link>
        <router-link to="/charms" class="nav-link">Charm Testing</router-link>
        <router-link to="/images" class="nav-link">Image Testing</router-link>

        <div class="spacer"></div>

        <router-link to="/test-results" class="nav-link">Search</router-link>
        <router-link to="/issues" class="nav-link">Issues</router-link>

        <div class="dropdown">
          <button class="nav-button dropdown-toggle">Help</button>
          <div class="dropdown-menu">
            <a href="https://canonical-test-observer.readthedocs-hosted.com/en/latest/" target="_blank" class="dropdown-item">Docs</a>
            <a href="https://github.com/canonical/test_observer/issues" target="_blank" class="dropdown-item">Feedback</a>
            <a href="https://github.com/canonical/test_observer" target="_blank" class="dropdown-item">Source Code</a>
          </div>
        </div>

        <div v-if="user" class="dropdown">
          <button class="nav-button dropdown-toggle">{{ user.name }}</button>
          <div class="dropdown-menu">
            <a :href="logoutUrl" class="dropdown-item">Log out</a>
          </div>
        </div>
        <button v-else @click="login" class="nav-button">Log in</button>
      </div>
    </div>
  </nav>
</template>

<script>
export default {
  name: 'Navbar',
  data() {
    return {
      user: null
    }
  },
  computed: {
    apiUrl() {
      // In production, this would come from environment config
      return window.location.origin.replace(':30001', ':30000')
    },
    vueAppUrl() {
      return window.location.origin + '/vue_poc/'
    },
    logoutUrl() {
      return `${this.apiUrl}/v1/auth/saml/logout?return_to=${encodeURIComponent(this.vueAppUrl)}`
    }
  },
  methods: {
    login() {
      const loginUrl = `${this.apiUrl}/v1/auth/saml/login?return_to=${encodeURIComponent(this.vueAppUrl)}`
      window.location.href = loginUrl
    },
    async fetchCurrentUser() {
      try {
        const response = await fetch(`${this.apiUrl}/v1/users/me`, {
          credentials: 'include', // Include cookies in the request
          headers: {
            'X-CSRF-Token': '1'
          }
        })

        if (response.ok) {
          const data = await response.json()
          this.user = data || null
        } else {
          this.user = null
        }
      } catch (error) {
        console.error('Failed to fetch current user:', error)
        this.user = null
      }
    }
  },
  mounted() {
    this.fetchCurrentUser()
  }
}
</script>

<style scoped>
.navbar {
  background: #333333;
  height: 57px;
  display: flex;
  justify-content: center;
}

.navbar-content {
  width: 100%;
  max-width: 1780px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.navbar-logo img {
  /*height: 24px;  - from Claude; disabled to avoid stretching */
  margin-top: 6px;  /* From Paul - lines up better versus Flutter UI on FF */
  filter: brightness(0) invert(1);
}

.navbar-links {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0;
}

.nav-link,
.nav-button {
  color: white;
  text-decoration: none;
  padding: 16px;
  font-size: 20px;
  font-weight: 500;
  background: none;
  border: none;
  cursor: pointer;
  height: 57px;
  display: flex;
  align-items: center;
  white-space: nowrap;
  transition: background-color 0.2s;
}

.nav-link:hover,
.nav-button:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.nav-link.router-link-active {
  background-color: #E95420;
}

.spacer {
  flex: 1;
}

.dropdown {
  position: relative;
  display: inline-block;
}

.dropdown-toggle::after {
  content: ' ▾';
  font-size: 12px;
}

.dropdown-menu {
  display: none;
  position: absolute;
  top: 100%;
  left: 0;
  background: #772953;
  min-width: 160px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  z-index: 1000;
}

.dropdown:hover .dropdown-menu {
  display: block;
}

.dropdown-item {
  color: white;
  text-decoration: none;
  padding: 16px;
  display: block;
  font-size: 16px;
  transition: background-color 0.2s;
}

.dropdown-item:hover {
  background-color: rgba(255, 255, 255, 0.1);
}
</style>
