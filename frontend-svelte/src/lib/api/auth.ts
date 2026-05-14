// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { apiFetch } from "./client.js";

export function getVersion(
  fetchFn: typeof fetch = fetch,
): Promise<{ version: string }> {
  return apiFetch<{ version: string }>("/v1/version", {}, fetchFn);
}
