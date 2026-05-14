// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { PageLoad } from "./$types.js";
import { getArtefact } from "$lib/api/artefacts.js";
import { getArtefactBuilds } from "$lib/api/artefacts.js";
import { getArtefactEnvironmentReviews } from "$lib/api/artefacts.js";
import { getArtefactVersions } from "$lib/api/artefacts.js";
import { ApiError, API_BASE } from "$lib/api/client.js";

export const load: PageLoad = async ({ params, url, fetch }) => {
  const id = Number(params.id);

  try {
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
  } catch (err) {
    if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
      if (typeof window !== "undefined") {
        const returnTo = window.location.href;
        window.location.href = `${API_BASE}/v1/auth/saml/login?return_to=${encodeURIComponent(returnTo)}`;
      }
      return { family: params.family, artefact: null, builds: [], reviews: [], versions: [], activeTestExecutionId: undefined, activeTestResultId: undefined };
    }
    throw err;
  }
};
