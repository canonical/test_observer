// Copyright 2026 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

export type NotificationType =
  "USER_ASSIGNED_ARTEFACT_REVIEW" | "USER_ASSIGNED_ENVIRONMENT_REVIEW";

export interface UserNotification {
  id: number;
  user_id: number;
  notification_type: NotificationType;
  target_url: string | null;
  created_at: string;
  dismissed_at: string | null;
}

export interface UserNotifications {
  notifications: UserNotification[];
  count: number;
  limit: number;
  offset: number;
}
