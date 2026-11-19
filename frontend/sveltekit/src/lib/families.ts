// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import type { FamilyResponse } from "$lib/types/openapi";

function capitalize(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** Route segment for a family's dashboard, e.g. "snaps" for the "snap" family. */
export function familyRouteName(family: FamilyResponse): string {
  return `${family.name}s`;
}

/** Looks up the family whose dashboard is served at the given route segment. */
export function findFamilyByRouteName(
  families: FamilyResponse[],
  routeName: string,
): FamilyResponse | undefined {
  return families.find((family) => familyRouteName(family) === routeName);
}

/** Navigation label, e.g. "Snaps". */
export function familyNavLabel(family: FamilyResponse): string {
  return capitalize(familyRouteName(family));
}

/** Dashboard title, e.g. "Snap Testing". */
export function familyTitle(family: FamilyResponse): string {
  return `${capitalize(family.name)} Testing`;
}
