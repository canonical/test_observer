<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { base } from "$app/paths";
  import { Breadcrumbs, Button, Link } from "@canonical/svelte-ds-app-launchpad";
  import { notificationTypeLabel } from "$lib/utils/notification-labels.js";
  import { formatDate } from "$lib/utils/formatting.js";
  import { dismissNotification } from "$lib/api/notifications.js";
  import { invalidateAll } from "$app/navigation";
  import { setUnreadCount, getUnreadCount } from "$lib/stores/notifications.svelte.js";
  import type { UserNotification } from "$lib/types/notification.js";

  let { data } = $props();

  let dismissingIds = $state(new Set<number>());
  let dismissingAll = $state(false);

  const breadcrumbSegments = [
    { label: "Notifications", href: `${base}/notifications` },
  ];

  const unreadNotifications = $derived(
    data.notifications.filter((n: UserNotification) => !n.dismissedAt),
  );

  async function handleDismiss(id: number): Promise<void> {
    dismissingIds.add(id);
    dismissingIds = new Set(dismissingIds);
    try {
      await dismissNotification(id);
      setUnreadCount(Math.max(0, getUnreadCount() - 1));
      await invalidateAll();
    } catch {
      // Will be refreshed on next load
    } finally {
      dismissingIds.delete(id);
      dismissingIds = new Set(dismissingIds);
    }
  }

  async function handleDismissAll(): Promise<void> {
    dismissingAll = true;
    try {
      await Promise.all(
        unreadNotifications.map((n: UserNotification) => dismissNotification(n.id)),
      );
      setUnreadCount(0);
      await invalidateAll();
    } catch {
      await invalidateAll();
    } finally {
      dismissingAll = false;
    }
  }
</script>

<svelte:head>
  <title>Notifications — Test Observer</title>
</svelte:head>

<div class="ds notifications-page">
  <Breadcrumbs segments={breadcrumbSegments} />

  <div class="ds notifications-page__header">
    <h1>Notifications</h1>
    {#if unreadNotifications.length > 0}
      <Button onclick={handleDismissAll} disabled={dismissingAll}>
        Dismiss all ({unreadNotifications.length})
      </Button>
    {/if}
  </div>

  {#if data.notifications.length === 0}
    <div class="ds notifications-page__empty">
      <p>No notifications</p>
    </div>
  {:else}
    <ul class="ds notifications-page__list">
      {#each data.notifications as notification (notification.id)}
        <li
          class="ds notification-card"
          class:dismissed={!!notification.dismissedAt}
        >
          <div class="ds notification-card__content">
            <span class="ds notification-card__type">
              {notificationTypeLabel(notification.notificationType)}
            </span>

            {#if notification.targetUrl}
              <Link href={notification.targetUrl}>View</Link>
            {/if}

            <span class="ds notification-card__date">
              {formatDate(notification.createdAt)}
            </span>
          </div>

          <div class="ds notification-card__actions">
            {#if notification.dismissedAt}
              <span class="ds notification-card__dismissed-label">Dismissed</span>
            {:else}
              <Button
                onclick={() => handleDismiss(notification.id)}
                disabled={dismissingIds.has(notification.id)}
              >
                Dismiss
              </Button>
            {/if}
          </div>
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .ds.notifications-page {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-4);
  }

  .ds.notifications-page__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .ds.notifications-page__header h1 {
    margin: 0;
  }

  .ds.notifications-page__empty {
    text-align: center;
    padding: var(--spacing-6);
    color: var(--color-text-muted, #666);
  }

  .ds.notifications-page__list {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-2);
  }

  .ds.notification-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--spacing-3) var(--spacing-4);
    border: 1px solid var(--color-border, #d9d9d9);
    border-radius: var(--border-radius, 4px);
    background: var(--color-background-alt, #fff);
  }

  .ds.notification-card.dismissed {
    opacity: 0.6;
  }

  .ds.notification-card__content {
    display: flex;
    align-items: center;
    gap: var(--spacing-3);
  }

  .ds.notification-card__type {
    font-weight: 600;
  }

  .ds.notification-card__date {
    color: var(--color-text-muted, #666);
    font-size: 0.875rem;
  }

  .ds.notification-card__actions {
    display: flex;
    align-items: center;
  }

  .ds.notification-card__dismissed-label {
    color: var(--color-text-muted, #666);
    font-style: italic;
  }
</style>
