// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { redirect, type Handle } from "@sveltejs/kit";
import { base } from "$app/paths";
import { loadConfig } from "$lib/config.js";
import { getCurrentUser } from "$lib/api/users.js";

export const handle: Handle = async ({ event, resolve }) => {
  const config = loadConfig();
  event.locals.config = config;

  const user = await getCurrentUser(event.fetch).catch(() => null);
  event.locals.user = user;

  if (
    config.requireAuthentication &&
    !user &&
    event.url.pathname !== `${base}/login`
  ) {
    redirect(
      302,
      `${base}/login?returnTo=${encodeURIComponent(event.url.pathname + event.url.search)}`,
    );
  }

  return resolve(event);
};
