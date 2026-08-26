// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import type { LayoutLoad } from "./$types";
import { resolve } from "$app/paths";

export const ssr = false;
export const prerender = false;

export const load: LayoutLoad = async ({ fetch }) => {
  let user = null;
  let artefactFamilies = [];
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

const getUser = async (fetch) => {
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

const getFamilies = async (fetch) => {
  const resp = await fetch(resolve("/families.json"));
  if (!resp.ok) {
    throw new Error(
      `Failed to fetch families.json: ${resp.status} ${resp.statusText}`,
    );
  }
  let artefactFamilies = [];
  try {
    artefactFamilies = (await resp.json()).families;
  } catch (error) {
    console.error("Error fetching families.json:", error);
  }
  return artefactFamilies;
};
