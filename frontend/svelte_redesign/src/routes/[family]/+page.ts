// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { error } from "@sveltejs/kit";
import type { PageLoad } from "./$types.js";
import { getArtefacts } from "$lib/api/artefacts.js";

export const load: PageLoad = async ({ params, parent, fetch }) => {
  const { config } = await parent();

  if (!config.tabs.includes(params.family)) {
    error(404, `Unknown family: ${params.family}`);
  }

  const artefacts = await getArtefacts(params.family, fetch);

  return {
    family: params.family,
    artefacts,
  };
};
