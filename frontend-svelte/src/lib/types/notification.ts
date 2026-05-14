// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

export type NotificationType =
  | "USER_ASSIGNED_ARTEFACT_REVIEW"
  | "USER_ASSIGNED_ENVIRONMENT_REVIEW";

export interface UserNotification {
  id: number;
  userId: number;
  notificationType: NotificationType;
  targetUrl?: string;
  createdAt: string;
  dismissedAt?: string;
}
