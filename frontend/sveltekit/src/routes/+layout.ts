// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import type { LayoutLoad } from './$types';
import type { User } from '$lib/types';

export const ssr = false;
export const prerender = false;

export const load: LayoutLoad = async ({ fetch }) => {
  try {
    const { getApiRoot } = await import('$lib/config');
    const res = await fetch(`${getApiRoot()}/v1/users/me`, {
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
