// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import type { FamilyResponse } from "$lib/types/openapi";

function capitalize(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/**
 * Legacy route segment and saved-view key, e.g. "snaps" for "snap".
 * Keep this independent from the current URL so existing saved views survive
 * the route migration.
 */
export function familyRouteName(family: FamilyResponse): string {
  return `${family.name}s`;
}

/** Encoded path to a family's dashboard, preserving its exact API name. */
export function familyDashboardRoute(family: FamilyResponse): string {
  return `family/${encodeURIComponent(family.name)}`;
}

/** Encoded path to an artefact detail page. */
export function familyDetailRoute(
  family: FamilyResponse,
  artefactId: string | number,
): string {
  return `${familyDashboardRoute(family)}/${encodeURIComponent(String(artefactId))}`;
}

/** Builds a redirect destination while retaining SvelteKit's base path. */
export function familyRedirectTarget(
  family: FamilyResponse,
  artefactId: string | number | null,
  search: string,
  resolvePath: (path: string) => string,
): string {
  const route =
    artefactId === null
      ? familyDashboardRoute(family)
      : familyDetailRoute(family, artefactId);
  return `${resolvePath(route)}${search}`;
}

/** Looks up a family by its exact API name. */
export function findFamilyByName(
  families: FamilyResponse[],
  familyName: string,
): FamilyResponse | undefined {
  return families.find((family) => family.name === familyName);
}

/** Resolves an old pluralized route segment for backwards-compatible redirects. */
export function findFamilyByLegacyRouteName(
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
