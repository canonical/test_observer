<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import { page } from '$app/state';
  import { base } from '$app/paths';
  import { SideNavigation, Badge } from '@canonical/svelte-ds-app-launchpad';
  import {
    SearchIcon,
    BugIcon,
    NotificationsIcon,
    HelpIcon,
    UserIcon,
    LogOutIcon,
    HighlightOffIcon,
    HighlightOnIcon,
  } from '@canonical/svelte-icons';
  import ErrorPopup from '$lib/components/ErrorPopup.svelte';
  import { configuredTabs, getApiRoot } from '$lib/config';
  import { userStore } from '$lib/stores/user.svelte';
  import { notificationsStore } from '$lib/stores/notifications.svelte';
  import { themeStore } from '$lib/stores/theme.svelte';
  import '../app.css';

  let { data, children } = $props();
  let expanded = $state(true);

  const pathname = $derived(page.url.pathname);

  $effect(() => {
    themeStore.init();
  });

  $effect(() => {
    userStore.set(data.user);
  });

  $effect(() => {
    if (userStore.isLoggedIn) {
      notificationsStore.loadUnreadCount();
    }
  });

  const loginUrl = $derived(`${getApiRoot()}/v1/auth/saml/login?return_to=${encodeURIComponent(page.url.href)}`);
  const logoutUrl = $derived(`${getApiRoot()}/v1/auth/saml/logout?return_to=${encodeURIComponent(page.url.href)}`);
</script>

<div class="app-shell">
  <SideNavigation {expanded}>
    {#snippet logo()}
      <a href="{base}/" class="side-nav-logo" aria-label="Test Observer Home">
        <img src="{base}/logo.png" alt="Test Observer Logo" class="logo-img" onerror={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none'; }} />
        <span class="logo-text">Test Observer</span>
      </a>
    {/snippet}
    {#snippet expandToggle(toggleProps)}
      <SideNavigation.ExpandToggle {...toggleProps} onclick={() => (expanded = !expanded)} />
    {/snippet}

    {#each configuredTabs as tab}
      <SideNavigation.NavigationItem href={tab.href} selected={pathname.startsWith(tab.href)}>
        {tab.label}
      </SideNavigation.NavigationItem>
    {/each}

    <hr class="nav-divider" />

    <SideNavigation.NavigationItem href="{base}/test-results" selected={pathname.startsWith(`${base}/test-results`)}>
      {#snippet icon()}<SearchIcon />{/snippet}
      Search Results
    </SideNavigation.NavigationItem>

    <SideNavigation.NavigationItem href="{base}/issues" selected={pathname.startsWith(`${base}/issues`)}>
      {#snippet icon()}<BugIcon />{/snippet}
      Issues
    </SideNavigation.NavigationItem>

    {#snippet footer()}
      <SideNavigation.NavigationItem href="https://canonical-test-observer.readthedocs-hosted.com/en/latest/" target="_blank" rel="noopener noreferrer">
        {#snippet icon()}<HelpIcon />{/snippet}
        Documentation
      </SideNavigation.NavigationItem>

      <SideNavigation.NavigationItem onclick={() => themeStore.cycle()}>
        {#snippet icon()}{#if themeStore.current === 'dark'}<HighlightOnIcon />{:else}<HighlightOffIcon />{/if}{/snippet}
        {themeStore.label}
      </SideNavigation.NavigationItem>

      {#if userStore.isLoggedIn}
        <SideNavigation.NavigationItem href="{base}/notifications" selected={pathname.startsWith(`${base}/notifications`)}>
          {#snippet icon()}<NotificationsIcon />{/snippet}
          Notifications
          {#if notificationsStore.unreadCount > 0}
            <Badge value={notificationsStore.unreadCount} severity="caution" />
          {/if}
        </SideNavigation.NavigationItem>

        <SideNavigation.NavigationItem onclick={(e: MouseEvent) => e.preventDefault()}>
          {#snippet icon()}<UserIcon />{/snippet}
          {userStore.current?.name ?? 'Account'}
        </SideNavigation.NavigationItem>

        <SideNavigation.NavigationItem href={logoutUrl}>
          {#snippet icon()}<LogOutIcon />{/snippet}
          Log out
        </SideNavigation.NavigationItem>
      {:else}
        <SideNavigation.NavigationItem href={loginUrl}>
          {#snippet icon()}<UserIcon />{/snippet}
          Log in
        </SideNavigation.NavigationItem>
      {/if}
    {/snippet}
  </SideNavigation>

  <main class="main-content">
    {@render children()}
  </main>

  <ErrorPopup />
</div>

<style>
  .app-shell {
    display: flex;
    min-height: 100vh;
  }

  .main-content {
    flex: 1;
    min-width: 0;
    padding: 1.5rem 2rem;
    overflow-y: auto;
    max-width: 1600px;
  }

  .side-nav-logo {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    text-decoration: none;
    color: inherit;
    padding: 0.25rem 0;
  }

  .logo-img {
    height: 32px;
    width: auto;
  }

  .logo-text {
    font-weight: 500;
    font-size: 1.1rem;
    white-space: nowrap;
  }

  .nav-divider {
    border: none;
    border-top: 1px solid rgba(0, 0, 0, 0.1);
    margin: 0.5rem 0;
  }
</style>
