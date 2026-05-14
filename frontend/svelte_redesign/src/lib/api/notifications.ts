// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { apiFetch } from "./client.js";
import type { UserNotification } from "$lib/types/notification.js";

export function getNotifications(
  fetchFn: typeof fetch = fetch,
): Promise<UserNotification[]> {
  return apiFetch<UserNotification[]>("/v1/users/me/notifications", {}, fetchFn);
}

export function getUnreadNotificationCount(
  fetchFn: typeof fetch = fetch,
): Promise<number> {
  return apiFetch<number>("/v1/users/me/notifications/count", {}, fetchFn);
}

export function dismissNotification(
  id: number,
  fetchFn: typeof fetch = fetch,
): Promise<UserNotification> {
  return apiFetch<UserNotification>(`/v1/users/me/notifications/${id}/dismiss`, {
    method: "POST",
  }, fetchFn);
}
