// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { NotificationType } from "$lib/types/notification.js";

const NOTIFICATION_TYPE_LABELS: Record<NotificationType, string> = {
  USER_ASSIGNED_ARTEFACT_REVIEW: "Assigned to artefact review",
  USER_ASSIGNED_ENVIRONMENT_REVIEW: "Assigned to environment review",
};

export function notificationTypeLabel(type: NotificationType): string {
  return NOTIFICATION_TYPE_LABELS[type] ?? type;
}
