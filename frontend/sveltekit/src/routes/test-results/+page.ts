// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { PageLoad } from "./$types";
import { FAMILIES_DEPENDENCY, fetchFamilies } from "$lib/familiesApi";

export const load: PageLoad = async ({ fetch, parent, depends }) => {
  depends(FAMILIES_DEPENDENCY);
  let { artefactFamilies, artefactFamiliesUnauthorized } = await parent();
  if (artefactFamilies === null || artefactFamiliesUnauthorized) {
    // The layout list is loaded once per app start, so a startup failure would
    // otherwise persist for the whole session. Try again on navigation.
    ({
      families: artefactFamilies,
      unauthorized: artefactFamiliesUnauthorized,
    } = await fetchFamilies(fetch));
  }
  if (artefactFamilies === null || artefactFamiliesUnauthorized) {
    // Family-bearing URLs cannot be safely validated without the API list.
    // The page will keep them fail-closed and explain that no search was sent.
    return { apiFamilyNames: [], familyNamesError: true };
  }
  return {
    apiFamilyNames: artefactFamilies.map((family) => family.name),
    familyNamesError: false,
  };
};
