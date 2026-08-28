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

import type { LayoutLoad } from "./$types";
import { resolve } from "$app/paths";
import type { Family } from "$lib/types";

export const ssr = false;
export const prerender = false;

export const load: LayoutLoad = async ({ fetch }) => {
  let user = null;
  let artefactFamilies: Family[] = [];
  try {
    const userPromise = getUser(fetch);
    const familiesPromise = getFamilies(fetch);

    user = await userPromise;
    artefactFamilies = await familiesPromise;
  } catch (error) {
    console.error("Error on LayoutLoad:", error);
  }
  console.log("Users:", user);
  console.log("Artefact Families:", artefactFamilies);
  return { user, artefactFamilies };
};

const getUser = async (fetch: Parameters<LayoutLoad>[0]["fetch"]) => {
  const { getApiRoot } = await import("$lib/config");
  const response = await fetch(`${getApiRoot()}/v1/users/me`, {
    credentials: "include",
    headers: { "X-CSRF-Token": "1" },
  });
  if (response.ok) {
    return response.json();
  }
  return null;
};

const getFamilies = async (fetch: Parameters<LayoutLoad>[0]["fetch"]) => {
  const resp = await fetch(resolve("/families.json"));
  if (!resp.ok) {
    throw new Error(
      `Failed to fetch families.json: ${resp.status} ${resp.statusText}`,
    );
  }
  let artefactFamilies: Family[] = [];
  try {
    artefactFamilies = (await resp.json()).families;
  } catch (error) {
    console.error("Error fetching families.json:", error);
  }
  return artefactFamilies;
};
