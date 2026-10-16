// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { error, redirect } from "@sveltejs/kit";
import { resolve } from "$app/paths";
import { parseArtefactId } from "$lib/utils/artefact-filters";
import type { PageLoad } from "./$types";

export const load: PageLoad = async ({ parent, params }) => {
  const { artefactFamilies } = await parent();
  const family = artefactFamilies.find((f) => f.name === params.family);

  if (!family) {
    error(404, `Unknown family: ${params.family}`);
  }

  const id = parseArtefactId(params.artefactId);
  if (id === null) {
    redirect(307, resolve(`/${family.name}`));
  }

  return { family, artefactId: id };
};
