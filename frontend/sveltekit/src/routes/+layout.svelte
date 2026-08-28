<!--
  Copyright 2026 Canonical Ltd.

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License version 3, as
  published by the Free Software Foundation.
  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <https://www.gnu.org/licenses/>.

  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: GPL-3.0-only
-->

<script lang="ts">
  import favicon from '$lib/assets/logo.png';
  import { page } from '$app/state';
  import { resolve } from '$app/paths';
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
  import { getApiRoot } from '$lib/config';
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

<svelte:head>
  <title>Test Observer</title>
  <link href="https://fonts.googleapis.com/css2?family=Ubuntu:wght@300;400;500;700&display=swap" rel="stylesheet" />
  <link rel="icon" href={favicon} />
</svelte:head>

<div class="app-shell">
  <SideNavigation {expanded}>
    {#snippet logo()}
      <a href="{resolve('/')}" class="side-nav-logo" aria-label="Test Observer Home">
        <img src="{favicon}" alt="Test Observer Logo" class="logo-img" onerror={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none'; }} />
        <span class="logo-text">Test Observer</span>
      </a>
    {/snippet}
    {#snippet expandToggle(toggleProps)}
      <SideNavigation.ExpandToggle {...toggleProps} onclick={() => (expanded = !expanded)} />
    {/snippet}

    {#each data.artefactFamilies as family}
      <SideNavigation.NavigationItem href={resolve(`/${family.name}`)} selected={pathname.startsWith(resolve(`/${family.name}`))}>
        {family.friendly_name}
      </SideNavigation.NavigationItem>
    {/each}

    <hr class="nav-divider" />

    <SideNavigation.NavigationItem href={resolve('/test-results')} selected={pathname.startsWith(resolve('/test-results'))}>
      {#snippet icon()}<SearchIcon />{/snippet}
      Search Results
    </SideNavigation.NavigationItem>

    <SideNavigation.NavigationItem href={resolve('/issues')} selected={pathname.startsWith(resolve('/issues'))}>
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
        <SideNavigation.NavigationItem href={resolve('/notifications')} selected={pathname.startsWith(resolve('/notifications'))}>
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
