<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { base } from "$app/paths";
  import { Badge } from "@canonical/svelte-ds-app-launchpad";
  import type { User } from "$lib/types/user.js";
  import {
    getUnreadCount,
    startPolling,
    stopPolling,
  } from "$lib/stores/notifications.svelte.js";
  import { onDestroy } from "svelte";

  interface Props {
    user: User | null;
  }

  const { user }: Props = $props();

  const unreadCount = $derived(getUnreadCount());

  $effect(() => {
    if (user) {
      startPolling();
    }
  });

  onDestroy(() => {
    stopPolling();
  });
</script>

<div class="ds header">
  <div class="ds header__logo">
    <strong>Test Observer</strong>
  </div>
  <div class="ds header__spacer"></div>
  {#if user}
    <a href="{base}/notifications" class="ds header__notifications" aria-label="Notifications">
      Notifications
      {#if unreadCount > 0}
        <Badge value={unreadCount} />
      {/if}
    </a>
    <div class="ds header__divider" aria-hidden="true"></div>
    <div class="ds header__user">
      <span>{user.name}</span>
    </div>
  {/if}
</div>

<style>
  .ds.header {
    display: flex;
    align-items: center;
    width: 100%;
    gap: var(--spacing-4);
    background-color: var(--lp-color-background-brand-default);
    color: var(--lp-color-text-reversed);
  }

  .ds.header__logo strong {
    font-size: 1rem;
    letter-spacing: 0.02em;
    color: var(--lp-color-text-reversed);
  }

  .ds.header__spacer {
    flex: 1;
  }

  .ds.header__divider {
    width: 1px;
    height: 1.25rem;
    background-color: rgba(255, 255, 255, 0.3);
    flex-shrink: 0;
  }

  .ds.header__notifications {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    text-decoration: none;
    color: var(--lp-color-text-reversed);
    padding: var(--spacing-1) var(--spacing-2);
    border-radius: var(--lp-dimension-radius-small);
  }

  .ds.header__notifications:hover {
    background-color: rgba(255, 255, 255, 0.15);
    text-decoration: none;
  }

  .ds.header__user {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    color: var(--lp-color-text-reversed);
    font-weight: 500;
  }
</style>
