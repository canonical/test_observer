// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { silentApi } from "$lib/api/client";

class NotificationsStore {
  unreadCount = $state(0);

  async loadUnreadCount() {
    try {
      const data = await silentApi<number>(
        "/users/me/notifications/count?unread_only=true",
      );
      if (data !== null) {
        this.unreadCount = data;
      }
    } catch {
      // silently fail — count is non-critical
    }
  }
}

export const notificationsStore = new NotificationsStore();
