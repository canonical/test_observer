// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

/**
 * Backend API base URL.
 * In development the backend runs on port 30000.
 * This exact string gets replaced by nginx in production by the frontend charm;
 * please do not modify it.
 */
export const API_BASE = "http://localhost:30000/";

/** Returns API_BASE, properly normalized. */
export function getApiRoot(): string {
  return API_BASE.replace(/\/$/, "");
}
