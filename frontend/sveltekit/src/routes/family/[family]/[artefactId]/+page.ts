// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { error, redirect } from "@sveltejs/kit";
import { resolve } from "$app/paths";
import { findFamilyByName, familyRedirectTarget } from "$lib/families";
import { parseArtefactId } from "$lib/utils/artefact-filters";
import type { PageLoad } from "./$types";

export const load: PageLoad = async ({ parent, params, url }) => {
  const { artefactFamilies } = await parent();
  if (artefactFamilies === null) {
    error(503, "Unable to load artefact families");
  }
  const family = findFamilyByName(artefactFamilies, params.family);

  if (!family) {
    error(404, `Unknown family: ${params.family}`);
  }

  const id = parseArtefactId(params.artefactId);
  if (id === null) {
    redirect(307, familyRedirectTarget(family, null, url.search, resolve));
  }

  return { family, artefactId: id };
};
