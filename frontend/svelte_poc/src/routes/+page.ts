import { redirect } from '@sveltejs/kit';
import { base } from '$app/paths';
import type { PageLoad } from './$types';

export const load: PageLoad = () => {
  redirect(307, `${base}/snaps`);
};
