// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { silentApi } from '$lib/api/client';
import type { UnreadCountResponse } from '$lib/types/notifications';

class NotificationsStore {
  unreadCount = $state(0);

  async loadUnreadCount() {
    try {
      const data = await silentApi<UnreadCountResponse>(
        '/users/me/notifications/count?unread_only=true',
      );
      if (data) {
        this.unreadCount = data.count;
      }
    } catch {
      // silently fail — count is non-critical
    }
  }
}

export const notificationsStore = new NotificationsStore();
