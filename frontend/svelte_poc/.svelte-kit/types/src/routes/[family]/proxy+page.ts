// @ts-nocheck
import { error } from '@sveltejs/kit';
import { FAMILIES } from '$lib/types';
import type { PageLoad } from './$types';

export const load = ({ params }: Parameters<PageLoad>[0]) => {
  if (!FAMILIES.includes(params.family as any)) {
    error(404, `Unknown family: ${params.family}`);
  }
  return { family: params.family };
};
