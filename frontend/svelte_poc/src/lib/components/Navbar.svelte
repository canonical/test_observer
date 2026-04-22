<script lang="ts">
  import { page } from '$app/state';
  import { base } from '$app/paths';
  import NavbarEntry from './navbar/NavbarEntry.svelte';
  import NavbarDropdown from './navbar/NavbarDropdown.svelte';
  import { configuredTabs, helpLinks } from '$lib/config';
  import { userStore } from '$lib/stores/user.svelte';
  import { notificationsStore } from '$lib/stores/notifications.svelte';

  const pathname = $derived(page.url.pathname);

  $effect(() => {
    if (userStore.isLoggedIn) {
      notificationsStore.loadUnreadCount();
    }
  });

  const badgeText = $derived(
    notificationsStore.unreadCount > 99 ? '99+' : String(notificationsStore.unreadCount),
  );

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
      <img src="{base}/logo.png" alt="Test Observer" onerror={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none'; }} />
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
      <a href="{base}/notifications" class="bell-link" aria-label="Notifications">
        <span class="bell-icon">🔔</span>
        {#if notificationsStore.unreadCount > 0}
          <span class="bell-badge">{badgeText}</span>
        {/if}
      </a>
    {/if}

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
    height: 57px;
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

  .bell-link {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    padding: 0 12px;
    text-decoration: none;
  }

  .bell-link:hover {
    background: hsl(0 0% 28%);
  }

  .bell-icon {
    font-size: 1.25rem;
    line-height: 1;
  }

  .bell-badge {
    position: absolute;
    top: 10px;
    right: 4px;
    background: #c7162b;
    color: #fff;
    font-size: 0.65rem;
    font-weight: 700;
    min-width: 16px;
    height: 16px;
    line-height: 16px;
    text-align: center;
    border-radius: 8px;
    padding: 0 4px;
    pointer-events: none;
  }
</style>
