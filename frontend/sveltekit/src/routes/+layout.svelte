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
  import { page, navigating } from '$app/state';
  import { onMount } from 'svelte';
  import { resolve } from '$app/paths';
  import { SideNavigation, Badge, Spinner } from '@canonical/svelte-ds-app-launchpad';
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

  // The initial-load spinner lives in app.html and blocks the blank grey flash
  // until SvelteKit finishes the first load chain and mounts this layout.
  onMount(() => {
    document.getElementById('app-loading')?.remove();
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

    {#each data.artefactFamilies as family (family.name)}
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

  {#if navigating.to}
    <div class="loading-overlay" role="status" aria-live="polite">
      <div class="loading-box">
        <Spinner class="loading-spinner" />
        <span class="loading-text">Loading…</span>
      </div>
    </div>
  {/if}

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

  .loading-overlay {
    position: fixed;
    inset: 0;
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
    /* The overlay background color's opacity seems a bit strong, especially in light mode.
       Toning it down a bit. */
    background: rgb(from var(--lp-color-background-overlay) r g b / 0.25);
    backdrop-filter: blur(1px);
  }

  .loading-box {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    padding: 1.5rem 2rem;
    border-radius: 0.5rem;
    background: var(--lp-color-background-default);
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
  }

  .loading-box :global(.loading-spinner) {
    width: 2rem;
    height: 2rem;
    color: var(--lp-color-brand-default);
  }

  .loading-text {
    font-size: 0.875rem;
    color: var(--lp-color-text-muted);
  }
</style>
