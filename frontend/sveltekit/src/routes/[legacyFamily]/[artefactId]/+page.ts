// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { error, redirect } from "@sveltejs/kit";
import { resolve } from "$app/paths";
import {
  findFamilyByLegacyRouteName,
  familyRedirectTarget,
} from "$lib/families";
import { parseArtefactId } from "$lib/utils/artefact-filters";
import type { PageLoad } from "./$types";

export const load: PageLoad = async ({ parent, params, url }) => {
  const { artefactFamilies } = await parent();
  if (artefactFamilies === null) {
    error(503, "Unable to load artefact families");
  }
  const family = findFamilyByLegacyRouteName(
    artefactFamilies,
    params.legacyFamily,
  );

  if (!family) {
    error(404, `Unknown family: ${params.legacyFamily}`);
  }

  const id = parseArtefactId(params.artefactId);
  redirect(307, familyRedirectTarget(family, id, url.search, resolve));
};
