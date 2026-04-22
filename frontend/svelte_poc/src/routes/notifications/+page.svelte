<script lang="ts">
  import { notificationsStore } from '$lib/stores/notifications.svelte';
  import { notificationDisplayTitle } from '$lib/types/notifications';
  import { userStore } from '$lib/stores/user.svelte';
  import { goto } from '$app/navigation';

  let dismissingId = $state<number | null>(null);
  let dismissError = $state<string | null>(null);

  $effect(() => {
    if (userStore.isLoggedIn) {
      notificationsStore.loadNotifications();
    }
  });

  async function dismiss(id: number) {
    dismissingId = id;
    dismissError = null;
    const ok = await notificationsStore.dismissNotification(id);
    if (!ok) {
      dismissError = `Failed to dismiss notification ${id}`;
    }
    dismissingId = null;
  }

  function handleClick(targetUrl: string | null) {
    if (targetUrl) {
      goto(targetUrl);
    }
  }

  function formatTimestamp(iso: string): string {
    const d = new Date(iso);
    return d.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  }
</script>

<div class="notifications-page">
  <h1>Notifications</h1>

  {#if dismissError}
    <div class="toast-error">
      {dismissError}
      <button onclick={() => (dismissError = null)}>✕</button>
    </div>
  {/if}

  {#if notificationsStore.loading}
    <div class="center-state">
      <div class="spinner"></div>
      <p>Loading notifications…</p>
    </div>
  {:else if notificationsStore.error}
    <div class="center-state">
      <p class="error-text">{notificationsStore.error}</p>
      <button class="retry-btn" onclick={() => notificationsStore.loadNotifications()}>
        Retry
      </button>
    </div>
  {:else if notificationsStore.notifications.length === 0}
    <div class="center-state">
      <span class="empty-bell">🔔</span>
      <p class="muted">No notifications</p>
    </div>
  {:else}
    <div class="notification-list">
      {#each notificationsStore.notifications as notif (notif.id)}
        {@const isUnread = notif.dismissed_at === null}
        <div
          class="notification-card"
          class:unread={isUnread}
          role="button"
          tabindex="0"
          onclick={() => handleClick(notif.target_url)}
          onkeydown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') handleClick(notif.target_url);
          }}
        >
          <div class="card-content">
            <div class="card-left">
              <span class="notif-title">
                {notificationDisplayTitle(notif.notification_type)}
              </span>
              <span class="notif-time">{formatTimestamp(notif.created_at)}</span>
            </div>
            <div class="card-right">
              {#if isUnread}
                <button
                  class="dismiss-btn"
                  disabled={dismissingId === notif.id}
                  onclick={(e) => { e.stopPropagation(); dismiss(notif.id); }}
                >
                  {#if dismissingId === notif.id}
                    Dismissing…
                  {:else}
                    Dismiss
                  {/if}
                </button>
              {:else}
                <span class="dismissed-label">Dismissed</span>
              {/if}
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .notifications-page {
    max-width: 800px;
  }

  h1 {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 24px;
  }

  .center-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 64px 0;
    gap: 12px;
  }

  .empty-bell {
    font-size: 3rem;
  }

  .muted {
    color: #888;
    font-size: 1rem;
  }

  .error-text {
    color: #c7162b;
  }

  .retry-btn {
    padding: 6px 16px;
    border: 1px solid #ccc;
    border-radius: 4px;
    background: #fff;
    cursor: pointer;
  }

  .retry-btn:hover {
    background: #f0f0f0;
  }

  .spinner {
    width: 24px;
    height: 24px;
    border: 3px solid #ddd;
    border-top-color: #333;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .notification-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .notification-card {
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 12px 16px;
    background: #fff;
    cursor: default;
    transition: box-shadow 0.15s;
  }

  .notification-card:hover {
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  }

  .notification-card.unread {
    background: #f6f9ff;
    border-left: 3px solid #007bff;
  }

  .card-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
  }

  .card-left {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .notif-title {
    font-weight: 500;
    font-size: 0.95rem;
  }

  .notif-time {
    font-size: 0.82rem;
    color: #888;
  }

  .card-right {
    flex-shrink: 0;
  }

  .dismiss-btn {
    padding: 4px 12px;
    border: 1px solid #ccc;
    border-radius: 4px;
    background: #fff;
    cursor: pointer;
    font-size: 0.85rem;
  }

  .dismiss-btn:hover:not(:disabled) {
    background: #f0f0f0;
  }

  .dismiss-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .dismissed-label {
    font-size: 0.85rem;
    color: #888;
  }

  .toast-error {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #fce4e4;
    border: 1px solid #e0a0a0;
    border-radius: 4px;
    padding: 8px 12px;
    margin-bottom: 16px;
    color: #c7162b;
    font-size: 0.9rem;
  }

  .toast-error button {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1rem;
    color: #c7162b;
    padding: 0 4px;
  }
</style>
