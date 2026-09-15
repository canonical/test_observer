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
import type { Artefact } from "$lib/types";
import type { PageLoad } from "./$types";

export const load: PageLoad = async ({ parent, params, fetch }) => {
  const { artefactFamilies } = await parent();
  const family = artefactFamilies.find((f) => f.name === params.family);

  if (!family) {
    error(404, `Unknown family: ${params.family}`);
  }

  const res = await fetch(
    `${getApiRoot()}/v1/artefacts?family=${family.api_name}`,
    {
      credentials: "include",
      headers: { "X-CSRF-Token": "1" },
    },
  );

  if (!res.ok) {
    if (res.status === 401 || res.status === 403) {
      const returnTo =
        typeof window !== "undefined" ? window.location.href : "";
      const loginUrl = `${getApiRoot()}/v1/auth/saml/login?return_to=${encodeURIComponent(returnTo)}`;
      if (typeof window !== "undefined") {
        window.location.href = loginUrl;
      }
      return { family, artefacts: [] as Artefact[] };
    }
    error(res.status, "Failed to load artefacts");
  }

  const raw: Artefact[] = await res.json();
  const artefacts = raw.map((a) => ({ ...a, reviewers: a.reviewers ?? [] }));

  return {
    family,
    artefacts,
  };
};
