// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { error } from "@sveltejs/kit";
import type { PageLoad } from "./$types.js";
import { getArtefacts } from "$lib/api/artefacts.js";
import { ApiError, API_BASE } from "$lib/api/client.js";

// Map plural URL tab names to singular API family names
const FAMILY_TO_API: Record<string, string> = {
  snaps: "snap",
  debs: "deb",
  charms: "charm",
  images: "image",
};

export const load: PageLoad = async ({ params, parent, fetch }) => {
  const { config } = await parent();

  if (!config.tabs.includes(params.family)) {
    error(404, `Unknown family: ${params.family}`);
  }

  const apiFamily = FAMILY_TO_API[params.family] ?? params.family;

  try {
    const artefacts = await getArtefacts(apiFamily, fetch);
    return { family: params.family, artefacts };
  } catch (err) {
    if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
      if (typeof window !== "undefined") {
        const returnTo = window.location.href;
        window.location.href = `${API_BASE}/v1/auth/saml/login?return_to=${encodeURIComponent(returnTo)}`;
      }
      return { family: params.family, artefacts: [] };
    }
    throw err;
  }
};
