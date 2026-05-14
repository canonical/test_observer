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
    gap: var(--spacing-3);
  }

  .ds.header__spacer {
    flex: 1;
  }

  .ds.header__notifications {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    text-decoration: none;
    color: var(--color-text);
  }

  .ds.header__notifications:hover {
    text-decoration: underline;
  }
</style>
