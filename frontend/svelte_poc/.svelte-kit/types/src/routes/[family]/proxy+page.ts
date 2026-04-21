// @ts-nocheck
import { error } from '@sveltejs/kit';
import { FAMILIES, FAMILY_TO_API, type Artefact, type Family } from '$lib/types';
import { API_BASE } from '$lib/config';
import type { PageLoad } from './$types';

export const load = async ({ params, fetch }: Parameters<PageLoad>[0]) => {
  const family = params.family as string;

  if (!FAMILIES.includes(family as Family)) {
    error(404, `Unknown family: ${family}`);
  }

  const apiFamily = FAMILY_TO_API[family as Family];
  const res = await fetch(`${API_BASE}/v1/artefacts?family=${apiFamily}`, {
    credentials: 'include',
    headers: { 'X-CSRF-Token': '1' },
  });

  if (!res.ok) {
    if (res.status === 401 || res.status === 403) {
      const returnTo = typeof window !== 'undefined' ? window.location.href : '';
      const loginUrl = `${API_BASE}/v1/auth/saml/login?return_to=${encodeURIComponent(returnTo)}`;
      if (typeof window !== 'undefined') {
        window.location.href = loginUrl;
      }
      // Return empty while redirecting
      return { family: family as Family, artefacts: [] as Artefact[] };
    }
    error(res.status, 'Failed to load artefacts');
  }

  const artefacts: Artefact[] = await res.json();

  return {
    family: family as Family,
    artefacts,
  };
};
