import { error } from '@sveltejs/kit';
import { FAMILIES } from '$lib/types';
import type { PageLoad } from './$types';

export const load: PageLoad = ({ params }) => {
  if (!FAMILIES.includes(params.family as any)) {
    error(404, `Unknown family: ${params.family}`);
  }
  return { family: params.family };
};
