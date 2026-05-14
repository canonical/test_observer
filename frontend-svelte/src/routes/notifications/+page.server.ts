// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { PageServerLoad, Actions } from "./$types.js";
import { getNotifications, dismissNotification } from "$lib/api/notifications.js";
import { fail } from "@sveltejs/kit";

export const load: PageServerLoad = async ({ fetch }) => {
  const notifications = await getNotifications(fetch);
  return { notifications };
};

export const actions: Actions = {
  dismiss: async ({ request, fetch }) => {
    const formData = await request.formData();
    const id = Number(formData.get("id"));
    if (!id || Number.isNaN(id)) {
      return fail(400, { error: "Invalid notification id" });
    }
    await dismissNotification(id, fetch);
    return { success: true };
  },
};
