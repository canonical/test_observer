// @ts-nocheck
import { redirect } from '@sveltejs/kit';
import { base } from '$app/paths';
import type { PageLoad } from './$types';

export const load = () => {
  redirect(307, `${base}/snaps`);
};
;null as any as PageLoad;