// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { base } from "$app/paths";
import type { PageServerLoad } from "./$types.js";

export const load: PageServerLoad = async ({ url }) => {
  const returnTo = url.searchParams.get("returnTo") ?? `${base}/`;
  return { returnTo };
};
