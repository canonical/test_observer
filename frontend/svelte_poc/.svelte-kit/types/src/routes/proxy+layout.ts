// @ts-nocheck
import type { LayoutLoad } from './$types';
import type { User } from '$lib/types';

export const ssr = false;
export const prerender = false;

export const load = async ({ fetch }: Parameters<LayoutLoad>[0]) => {
  try {
    const { API_BASE } = await import('$lib/config');
    const res = await fetch(`${API_BASE}/v1/users/me`, {
      credentials: 'include',
      headers: { 'X-CSRF-Token': '1' },
    });
    if (res.ok) {
      const user: User = await res.json();
      return { user };
    }
  } catch {
    // Not logged in or network error
  }
  return { user: null as User | null };
};
