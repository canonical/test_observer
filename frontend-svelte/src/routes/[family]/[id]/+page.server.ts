// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { PageServerLoad } from "./$types.js";
import { getArtefact } from "$lib/api/artefacts.js";
import { getArtefactBuilds } from "$lib/api/artefacts.js";
import { getArtefactEnvironmentReviews } from "$lib/api/artefacts.js";
import { getArtefactVersions } from "$lib/api/artefacts.js";

export const load: PageServerLoad = async ({ params, url, fetch }) => {
  const id = Number(params.id);

  const [artefact, builds, reviews, versions] = await Promise.all([
    getArtefact(id, fetch),
    getArtefactBuilds(id, fetch),
    getArtefactEnvironmentReviews(id, fetch),
    getArtefactVersions(id, fetch),
  ]);

  return {
    family: params.family,
    artefact,
    builds,
    reviews,
    versions,
    activeTestExecutionId: url.searchParams.get("testExecutionId")
      ? Number(url.searchParams.get("testExecutionId"))
      : undefined,
    activeTestResultId: url.searchParams.get("testResultId")
      ? Number(url.searchParams.get("testResultId"))
      : undefined,
  };
};
