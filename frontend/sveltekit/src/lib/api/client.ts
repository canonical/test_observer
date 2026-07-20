// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { errorStore } from '$lib/stores/error.svelte';
import { getApiRoot } from '$lib/config';

const API_VERSION = 'v1';

async function fetchApi<T>(path: string, options: RequestInit, reportErrors: boolean): Promise<T | null> {
  try {
    const res = await fetch(`${getApiRoot()}/${API_VERSION}/${path}`, {
      ...options,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': '1',
        ...(options.headers as Record<string, string> ?? {}),
      },
    });

    if (!res.ok) {
      if (reportErrors && res.status !== 401) {
        let message = `Request failed: ${res.status}`;
        try {
          const body = await res.json();
          if (body.detail !== undefined) {
            message = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
          }
        } catch { /* non-JSON error body */ }
        errorStore.set(message);
      }
      return null;
    }

    if (res.status === 204) return null;
    return (await res.json()) as T;
  } catch (err) {
    if (reportErrors) {
      errorStore.set(err instanceof Error ? err.message : 'Network error');
    }
    return null;
  }
}

export function api<T>(path: string, options: RequestInit = {}): Promise<T | null> {
  return fetchApi(path, options, true);
}

/**
 * Like api() but does NOT push errors to the global error store.
 * Use for optional/background requests where failure is expected.
 */
export function silentApi<T>(path: string, options: RequestInit = {}): Promise<T | null> {
  return fetchApi(path, options, false);
}
