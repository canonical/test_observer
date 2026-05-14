// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { redirect } from "@sveltejs/kit";
import { base } from "$app/paths";
import { loadConfig } from "$lib/config.js";
import { getCurrentUser } from "$lib/api/users.js";
import type { LayoutLoad } from "./$types.js";

export const load: LayoutLoad = async ({ url, fetch }) => {
  const [config, user] = await Promise.all([
    loadConfig(fetch),
    getCurrentUser(fetch).catch(() => null),
  ]);

  if (
    config.requireAuthentication &&
    !user &&
    url.pathname !== `${base}/login`
  ) {
    redirect(
      302,
      `${base}/login?returnTo=${encodeURIComponent(url.pathname + url.search)}`,
    );
  }

  return { user, config };
};
