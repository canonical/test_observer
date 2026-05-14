// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { redirect } from "@sveltejs/kit";
import { base } from "$app/paths";
import type { PageServerLoad } from "./$types.js";

export const load: PageServerLoad = async ({ parent }) => {
  const { config } = await parent();
  const target =
    config.tabs.length > 0
      ? `${base}/${config.tabs[0]}`
      : `${base}/test-results`;
  redirect(302, target);
};
