<script>
  import { onMount } from 'svelte';
  import { Link } from 'svelte-routing';

  let user = null;

  const apiUrl = window.location.origin.replace(':30001', ':30000');
  const svelteAppUrl = window.location.origin + '/svelte_poc/';
  const logoutUrl = `${apiUrl}/v1/auth/saml/logout?return_to=${encodeURIComponent(svelteAppUrl)}`;

  function login() {
    const loginUrl = `${apiUrl}/v1/auth/saml/login?return_to=${encodeURIComponent(svelteAppUrl)}`;
    window.location.href = loginUrl;
  }

  async function fetchCurrentUser() {
    try {
      const response = await fetch(`${apiUrl}/v1/users/me`, {
        credentials: 'include',
        headers: {
          'X-CSRF-Token': '1'
        }
      });

      if (response.ok) {
        const data = await response.json();
        user = data || null;
      } else {
        user = null;
      }
    } catch (error) {
      console.error('Failed to fetch current user:', error);
      user = null;
    }
  }

  onMount(() => {
    fetchCurrentUser();
  });
</script>

<nav class="navbar">
  <div class="navbar-content">
    <div class="navbar-logo">
      <img src="/canonical.png" alt="Canonical" />
    </div>

    <div class="navbar-links">
      <Link to="/svelte_poc/snaps" class="nav-link">Snap Testing</Link>
      <Link to="/svelte_poc/debs" class="nav-link">Deb Testing</Link>
      <Link to="/svelte_poc/charms" class="nav-link">Charm Testing</Link>
      <Link to="/svelte_poc/images" class="nav-link">Image Testing</Link>

      <div class="spacer"></div>

      <Link to="/svelte_poc/test-results" class="nav-link">Search</Link>
      <Link to="/svelte_poc/issues" class="nav-link">Issues</Link>

      <div class="dropdown">
        <button class="nav-button dropdown-toggle">Help</button>
        <div class="dropdown-menu">
          <a href="https://canonical-test-observer.readthedocs-hosted.com/en/latest/" target="_blank" class="dropdown-item">Docs</a>
          <a href="https://github.com/canonical/test_observer/issues" target="_blank" class="dropdown-item">Feedback</a>
          <a href="https://github.com/canonical/test_observer" target="_blank" class="dropdown-item">Source Code</a>
        </div>
      </div>

      {#if user}
        <div class="dropdown">
          <button class="nav-button dropdown-toggle">{user.name}</button>
          <div class="dropdown-menu">
            <a href={logoutUrl} class="dropdown-item">Log out</a>
          </div>
        </div>
      {:else}
        <button on:click={login} class="nav-button">Log in</button>
      {/if}
    </div>
  </div>
</nav>

<style>
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
  margin-top: 6px;
  filter: brightness(0) invert(1);
}

.navbar-links {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0;
}

:global(.nav-link),
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

:global(.nav-link:hover),
.nav-button:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

:global(.nav-link[aria-current="page"]) {
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
