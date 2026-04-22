import { api, silentApi } from '$lib/api/client';
import type {
  UserNotification,
  UserNotifications,
  UnreadCountResponse,
} from '$lib/types/notifications';

class NotificationsStore {
  notifications = $state<UserNotification[]>([]);
  unreadCount = $state(0);
  loading = $state(false);
  error = $state<string | null>(null);

  async loadNotifications() {
    this.loading = true;
    this.error = null;
    try {
      const data = await silentApi<UserNotifications>('/users/me/notifications');
      if (data) {
        this.notifications = data.notifications;
      } else {
        this.error = 'Failed to load notifications';
      }
    } catch {
      this.error = 'Failed to load notifications';
    } finally {
      this.loading = false;
    }
  }

  async loadUnreadCount() {
    try {
      const data = await silentApi<UnreadCountResponse>(
        '/users/me/notifications/count?unread_only=true',
      );
      if (data) {
        this.unreadCount = data.count;
      }
    } catch {
      // silently fail for count
    }
  }

  async dismissNotification(id: number): Promise<boolean> {
    try {
      const result = await api<UserNotification>(
        `/users/me/notifications/${id}/dismiss`,
        { method: 'POST' },
      );
      if (result) {
        await Promise.all([this.loadNotifications(), this.loadUnreadCount()]);
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }
}

export const notificationsStore = new NotificationsStore();
