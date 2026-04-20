import type { LayoutLoad } from './$types';
import type { User } from '$lib/types';

export const ssr = false;
export const prerender = false;

export const load: LayoutLoad = async ({ fetch }) => {
  try {
    const res = await fetch('/v1/users/me', {
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
