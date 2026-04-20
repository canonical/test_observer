<script lang="ts">
  import { page } from '$app/state';
  import { base } from '$app/paths';
  import NavbarEntry from './navbar/NavbarEntry.svelte';
  import NavbarDropdown from './navbar/NavbarDropdown.svelte';
  import { configuredTabs, helpLinks } from '$lib/config';
  import { userStore } from '$lib/stores/user.svelte';

  const pathname = $derived(page.url.pathname);

  function loginUrl(): string {
    return `/v1/auth/saml/login?return_to=${encodeURIComponent(window.location.href)}`;
  }

  function logoutUrl(): string {
    return `/v1/auth/saml/logout?return_to=${encodeURIComponent(window.location.href)}`;
  }
</script>

<nav class="navbar" aria-label="Main navigation">
  <div class="navbar-inner">
    <a href="{base}/" class="logo">
      <img src="{base}/logo.png" alt="Test Observer" height="28" onerror={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none'; }} />
    </a>

    {#each configuredTabs as tab}
      <NavbarEntry href={tab.href} title={tab.label} isActive={pathname.startsWith(tab.href)} />
    {/each}

    <div class="spacer"></div>

    <NavbarEntry href="{base}/test-results" title="Search" isActive={pathname.startsWith(`${base}/test-results`)} />
    <NavbarEntry href="{base}/issues" title="Issues" isActive={pathname.startsWith(`${base}/issues`)} />

    <NavbarDropdown label="Help">
      {#each helpLinks as link}
        <a href={link.href} target="_blank" rel="noopener noreferrer">{link.label}</a>
      {/each}
    </NavbarDropdown>

    {#if userStore.isLoggedIn}
      <NavbarDropdown label={userStore.current?.name ?? ''}>
        <a href={logoutUrl()}>Log out</a>
      </NavbarDropdown>
    {:else}
      <a href={loginUrl()} class="nav-button">Log in</a>
    {/if}
  </div>
</nav>

<style>
  .navbar {
    height: 57px;
    background: #333;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .navbar-inner {
    display: flex;
    align-items: center;
    max-width: 1800px;
    width: 100%;
    padding: 0 32px;
    height: 100%;
  }

  .logo {
    display: flex;
    align-items: center;
    margin-right: 16px;
    height: 100%;
  }

  .logo img {
    height: 28px;
    width: auto;
  }

  .spacer {
    flex: 1;
  }

  .nav-button {
    display: flex;
    align-items: center;
    height: 100%;
    padding: 0 16px;
    color: white;
    font-size: 0.95rem;
    font-weight: 500;
  }

  .nav-button:hover {
    background: hsl(0 0% 28%);
  }
</style>
