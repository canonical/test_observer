import { redirect } from '@sveltejs/kit';
import { base } from '$app/paths';
import { FAMILIES } from '$lib/types';
import type { PageLoad } from './$types';

export const ssr = false;

export const load: PageLoad = async ({ params }) => {
  const { family, artefactId } = params;

  if (!FAMILIES.includes(family as (typeof FAMILIES)[number])) {
    throw redirect(307, `${base}/snaps`);
  }

  const id = parseInt(artefactId, 10);
  if (isNaN(id)) {
    throw redirect(307, `${base}/${family}`);
  }

  return { family: family as (typeof FAMILIES)[number], artefactId: id };
};
