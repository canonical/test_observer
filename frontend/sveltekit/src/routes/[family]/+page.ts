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

import { error } from "@sveltejs/kit";
import { getApiRoot } from "$lib/config";
import { userStore } from "$lib/stores/user.svelte";
import type { Artefact, Family } from "$lib/types";
import type { PageLoad } from "./$types";

type ArtefactPageResult =
  | { kind: "loaded"; artefacts: Artefact[] }
  | { kind: "requiresLogin" }
  | { kind: "forbidden" }
  | { kind: "sessionCheckFailed" };

export const load: PageLoad = async ({ parent, params, fetch }) => {
  const { artefactFamilies } = await parent();
  const family = artefactFamilies.find((f) => f.name === params.family);

  if (!family) {
    error(404, `Unknown family: ${params.family}`);
  }

  // Keep the family lookup and 404 validation in the load chain, but let
  // SvelteKit finish navigation while this potentially slow request is pending.
  return { family, artefacts: fetchArtefacts(fetch, family) };
};

async function fetchArtefacts(
  fetch: typeof globalThis.fetch,
  family: Family,
): Promise<ArtefactPageResult> {
  const res = await fetch(
    `${getApiRoot()}/v1/artefacts?family=${family.api_name}`,
    {
      credentials: "include",
      headers: { "X-CSRF-Token": "1" },
    },
  );

  if (!res.ok) {
    if (res.status === 401 || res.status === 403) {
      // The cached user may be stale (e.g. the session expired after the
      // initial layout load), so re-check the session directly rather than
      // trusting it. refresh() also updates the shared store, keeping the
      // sidebar in sync on this client-side navigation (the layout load isn't
      // rerun).
      const authStatus = await userStore.refresh(fetch);
      // Only show the forbidden state when we've *confirmed* the user is still
      // authenticated (so a 403 means they lack permission).
      if (res.status === 403 && authStatus === "authenticated") {
        return { kind: "forbidden" };
      }
      // If the session check itself was inconclusive, don't claim the user is
      // logged out (that would contradict the cached user the sidebar still
      // shows). Surface a distinct "couldn't verify" state they can retry.
      if (authStatus === "unknown") {
        return { kind: "sessionCheckFailed" };
      }
      // Confirmed unauthenticated: prompt for login.
      return { kind: "requiresLogin" };
    }
    throw new Error(`Failed to load artefacts (${res.status})`);
  }

  const raw = (await res.json()) as Artefact[];
  const artefacts = raw.map((a) => ({ ...a, reviewers: a.reviewers ?? [] }));

  return { kind: "loaded", artefacts };
}
