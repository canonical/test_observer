// Copyright 2026 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { LayoutLoad } from "./$types";
import { FAMILIES_DEPENDENCY, fetchFamilies } from "$lib/familiesApi";
import { userStore } from "$lib/stores/user.svelte";

export const ssr = false;
export const prerender = false;

export const load = (async ({ fetch, depends }) => {
  // Load the user and families independently: a failure fetching one (e.g. /me
  // erroring out when the session is invalid) must not prevent the other from
  // loading. Family routes handle lookup failures without blocking the layout.
  // userStore.refresh updates the shared user state, which the layout reads
  // directly, so there's no user value to thread through the returned data.
  // This load otherwise only runs once per app start, so pages that need a
  // fresh family list invalidate FAMILIES_DEPENDENCY to rerun it.
  depends(FAMILIES_DEPENDENCY);
  const [, { families: artefactFamilies, unauthorized }] = await Promise.all([
    userStore.refresh(fetch),
    fetchFamilies(fetch),
  ]);
  // Anonymous users get an empty sidebar, but pages that validate input
  // against the family list must not mistake a 401 for an empty catalogue.
  return { artefactFamilies, artefactFamiliesUnauthorized: unauthorized };
}) satisfies LayoutLoad;
