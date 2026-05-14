// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { ExecutionMetadata } from "$lib/types/test-execution.js";

export function encodeMetadata(metadata: ExecutionMetadata): string {
  const json = JSON.stringify(metadata.data);
  return btoa(json);
}

export function decodeMetadata(encoded: string): ExecutionMetadata {
  const json = atob(encoded);
  return { data: JSON.parse(json) as Record<string, string[]> };
}
