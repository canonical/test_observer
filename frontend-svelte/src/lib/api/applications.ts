// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { apiFetch } from "./client.js";

export function getApplications(
  fetchFn: typeof fetch = fetch,
): Promise<unknown[]> {
  return apiFetch<unknown[]>("/v1/applications", {}, fetchFn);
}
