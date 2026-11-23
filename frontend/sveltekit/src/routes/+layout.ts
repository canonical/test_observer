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
import { getApiRoot } from "$lib/config";
import { userStore } from "$lib/stores/user.svelte";
import type { FamilyResponse } from "$lib/types/openapi";

export const ssr = false;
export const prerender = false;

export const load = (async ({ fetch }) => {
  // Load the user and families independently: a failure fetching one (e.g. /me
  // erroring out when the session is invalid) must not prevent the other from
  // loading. Family routes handle lookup failures without blocking the layout.
  // userStore.refresh updates the shared user state, which the layout reads
  // directly, so there's no user value to thread through the returned data.
  const [, artefactFamilies] = await Promise.all([
    userStore.refresh(fetch),
    getFamilies(fetch),
  ]);
  return { artefactFamilies };
}) satisfies LayoutLoad;

const getFamilies = async (
  fetch: Parameters<LayoutLoad>[0]["fetch"],
): Promise<FamilyResponse[] | null> => {
  try {
    const resp = await fetch(`${getApiRoot()}/v1/families`, {
      credentials: "include",
      headers: { "X-CSRF-Token": "1" },
    });
    if (resp.status === 401) {
      return [];
    }
    if (!resp.ok) {
      throw new Error(
        `Failed to fetch families: ${resp.status} ${resp.statusText}`,
      );
    }
    const families: unknown = await resp.json();
    if (!Array.isArray(families)) {
      throw new Error("Expected an array of families");
    }
    if (
      !families.every(
        (family) =>
          typeof family === "object" &&
          family !== null &&
          !Array.isArray(family) &&
          typeof (family as { name?: unknown }).name === "string",
      )
    ) {
      throw new Error(
        "Expected each family to be an object with a string name",
      );
    }
    return families as FamilyResponse[];
  } catch (error) {
    console.error("Error fetching families:", error);
    return null;
  }
};
