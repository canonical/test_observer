// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { apiFetch } from "./client.js";

export function getPermissions(
  fetchFn: typeof fetch = fetch,
): Promise<string[]> {
  return apiFetch<string[]>("/v1/permissions", {}, fetchFn);
}
