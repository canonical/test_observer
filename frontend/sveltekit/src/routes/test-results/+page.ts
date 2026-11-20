// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { PageLoad } from "./$types";
import { getApiRoot } from "$lib/config";
import { fetchApiFamilyNames } from "$lib/apiFamilyNames";

export const load: PageLoad = async ({ fetch }) => {
  try {
    const apiFamilyNames = await fetchApiFamilyNames(fetch, getApiRoot());
    return { apiFamilyNames, familyNamesError: false };
  } catch {
    // Family-bearing URLs cannot be safely validated from a stale client list.
    // The page will keep them fail-closed and explain that no search was sent.
    return { apiFamilyNames: [], familyNamesError: true };
  }
};
