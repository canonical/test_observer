// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { PageServerLoad } from "./$types.js";
import { getIssues } from "$lib/api/issues.js";

export const load: PageServerLoad = async ({ url, fetch }) => {
  const params: Record<string, string> = {};
  for (const [key, value] of url.searchParams.entries()) {
    params[key] = value;
  }
  const issues = await getIssues(params, fetch);
  const searchQuery = url.searchParams.get("q") ?? "";

  return { issues, searchQuery };
};
