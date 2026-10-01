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
import { resolve } from "$app/paths";
import { userStore } from "$lib/stores/user.svelte";
import type { Family } from "$lib/types";

export const ssr = false;
export const prerender = false;

export const load: LayoutLoad = async ({ fetch }) => {
  // Load the user and families independently: a failure fetching one (e.g. /me
  // erroring out when the session is invalid) must not prevent the other from
  // loading. Both helpers swallow their own errors, so this never rejects.
  // userStore.refresh updates the shared user state, which the layout reads
  // directly, so there's no user value to thread through the returned data.
  const [, artefactFamilies] = await Promise.all([
    userStore.refresh(fetch),
    getFamilies(fetch),
  ]);
  return { artefactFamilies };
};

const getFamilies = async (fetch: Parameters<LayoutLoad>[0]["fetch"]) => {
  let artefactFamilies: Family[] = [];
  try {
    const resp = await fetch(resolve("/families.json"));
    if (!resp.ok) {
      throw new Error(
        `Failed to fetch families.json: ${resp.status} ${resp.statusText}`,
      );
    }
    artefactFamilies =
      ((await resp.json()) as { families?: Family[] }).families ?? [];
  } catch (error) {
    console.error("Error fetching families.json:", error);
  }
  return artefactFamilies;
};
