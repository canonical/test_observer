// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { getUnreadNotificationCount } from "$lib/api/notifications.js";

const POLL_INTERVAL_MS = 60_000;

let unreadCount: number = $state(0);
let pollTimer: ReturnType<typeof setInterval> | undefined;

export function getUnreadCount(): number {
  return unreadCount;
}

export function setUnreadCount(count: number): void {
  unreadCount = count;
}

async function fetchCount(): Promise<void> {
  try {
    unreadCount = await getUnreadNotificationCount();
  } catch {
    // Silently ignore - will retry on next poll
  }
}

export function startPolling(): void {
  stopPolling();
  void fetchCount();
  pollTimer = setInterval(() => void fetchCount(), POLL_INTERVAL_MS);
}

export function stopPolling(): void {
  if (pollTimer !== undefined) {
    clearInterval(pollTimer);
    pollTimer = undefined;
  }
}
