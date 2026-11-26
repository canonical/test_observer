// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { getApiRoot } from "$lib/config";
import type { FamilyResponse } from "$lib/types/openapi";

/** Dependency key for loads that read the family list; pass to invalidate(). */
export const FAMILIES_DEPENDENCY = "app:families";

export interface FamiliesResult {
  /** The validated family list, or null when it could not be loaded. */
  families: FamilyResponse[] | null;
  /** True when the API rejected the request as unauthenticated (401). */
  unauthorized: boolean;
}

/**
 * Fetches and validates the family list. Never throws: a 401 yields an empty
 * list flagged as unauthorized, and any other failure yields null.
 */
export async function fetchFamilies(
  fetch: typeof globalThis.fetch,
): Promise<FamiliesResult> {
  try {
    const resp = await fetch(`${getApiRoot()}/v1/families`, {
      credentials: "include",
      headers: { "X-CSRF-Token": "1" },
    });
    if (resp.status === 401) {
      return { families: [], unauthorized: true };
    }
    if (!resp.ok) {
      throw new Error(
        `Failed to fetch families: ${resp.status} ${resp.statusText}`,
      );
    }
    const families: unknown = await resp.json();
    if (!Array.isArray(families)) {
      throw new Error("Expected an array of families");
    }
    if (
      !families.every(
        (family) =>
          typeof family === "object" &&
          family !== null &&
          !Array.isArray(family) &&
          typeof (family as { name?: unknown }).name === "string",
      )
    ) {
      throw new Error(
        "Expected each family to be an object with a string name",
      );
    }
    return { families: families as FamilyResponse[], unauthorized: false };
  } catch (error) {
    console.error("Error fetching families:", error);
    return { families: null, unauthorized: false };
  }
}
