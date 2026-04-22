import { errorStore } from '$lib/stores/error.svelte';
import { API_BASE } from '$lib/config';

export async function api<T>(path: string, options: RequestInit = {}): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE}/v1${path}`, {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': '1',
        ...(options.headers as Record<string, string> ?? {}),
      },
      ...options,
    });

    if (!res.ok) {
      let message = `Request failed: ${res.status}`;
      try {
        const body = await res.json();
        if (body.detail) message = body.detail;
      } catch { /* non-JSON error body */ }
      
      if (res.status !== 401) {
        errorStore.set(message);
      }
      return null;
    }

    if (res.status === 204) return null as T;
    return (await res.json()) as T;
  } catch (err) {
    errorStore.set(err instanceof Error ? err.message : 'Network error');
    return null;
  }
}

/**
 * Like api() but does NOT push errors to the global error store.
 * Use for optional/background requests where 404 or failure is expected.
 */
export async function silentApi<T>(path: string, options: RequestInit = {}): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE}/v1${path}`, {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': '1',
        ...(options.headers as Record<string, string> ?? {}),
      },
      ...options,
    });

    if (!res.ok) return null;
    if (res.status === 204) return null as T;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}
