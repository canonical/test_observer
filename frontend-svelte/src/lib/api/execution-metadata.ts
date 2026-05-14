// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { apiFetch } from "./client.js";
import type { ExecutionMetadata } from "$lib/types/filters.js";

export function getExecutionMetadata(
  fetchFn: typeof fetch = fetch,
): Promise<ExecutionMetadata> {
  return apiFetch<ExecutionMetadata>("/v1/execution-metadata", {}, fetchFn);
}
