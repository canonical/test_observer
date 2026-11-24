// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0
import { error } from "@sveltejs/kit";
import { parseArtefactId } from "$lib/utils/artefact-filters";
import type { PageLoad } from "./$types";

export const load: PageLoad = async ({ parent, params }) => {
  const { artefactFamilies } = await parent();
  const family = artefactFamilies.find((item) => item.name === params.family);
  const artefactId = parseArtefactId(params.artefactId);
  if (!family || artefactId === null) error(404, "Artefact not found");
  return { family, artefactId };
};
