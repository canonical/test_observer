// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import type { PageLoad } from './$types';
import { FAMILIES, FAMILY_TITLES, type Family } from '$lib/types';
import { error } from '@sveltejs/kit';

export const load: PageLoad = ({ params }) => {
  const family = params.family as Family;
  if (!FAMILIES.includes(family)) {
    error(404, `Unknown family: ${family}`);
  }
  return { family, title: FAMILY_TITLES[family] };
};
