// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { PageLoad } from "./$types.js";
import { getNotifications } from "$lib/api/notifications.js";

export const load: PageLoad = async ({ fetch }) => {
  const notifications = await getNotifications(fetch);
  return { notifications };
};
