// Copyright 2026 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { errorStore } from "$lib/stores/error.svelte";
import { getApiRoot } from "$lib/config";

const API_VERSION = "v1";

async function fetchApi<T>(
  path: string,
  options: RequestInit,
  reportErrors: boolean,
): Promise<T | null> {
  // Strip leading slashes, else we'll accidentally double them up below on the fetch call.
  path = path.replace(/^\/+/, "");
  try {
    const headers = new Headers({
      "Content-Type": "application/json",
      "X-CSRF-Token": "1",
    });
    // Caller-supplied headers win over the defaults above.
    new Headers(options.headers).forEach((value, key) => {
      headers.set(key, value);
    });

    const res = await fetch(`${getApiRoot()}/${API_VERSION}/${path}`, {
      ...options,
      credentials: "include",
      headers,
    });

    if (!res.ok) {
      if (reportErrors && res.status !== 401) {
        let message = `Request failed: ${res.status}`;
        try {
          const body: unknown = await res.json();
          if (typeof body === "object" && body !== null && "detail" in body) {
            const detail: unknown = body.detail;
            message =
              typeof detail === "string" ? detail : JSON.stringify(detail);
          }
        } catch {
          /* non-JSON error body */
        }
        errorStore.set(message);
      }
      return null;
    }

    if (res.status === 204) return null;
    return (await res.json()) as T;
  } catch (err) {
    if (reportErrors) {
      errorStore.set(err instanceof Error ? err.message : "Network error");
    }
    return null;
  }
}

export function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T | null> {
  return fetchApi(path, options, true);
}

/**
 * Like api() but does NOT push errors to the global error store.
 * Use for optional/background requests where failure is expected.
 */
export function silentApi<T>(
  path: string,
  options: RequestInit = {},
): Promise<T | null> {
  return fetchApi(path, options, false);
}
