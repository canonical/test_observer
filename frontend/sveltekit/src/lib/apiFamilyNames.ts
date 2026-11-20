// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

/** Read the current family names from the backend. */
export async function fetchApiFamilyNames(
  fetcher: typeof fetch,
  apiRoot: string,
): Promise<string[]> {
  const response = await fetcher(`${apiRoot}/v1/families`, {
    credentials: "include",
    headers: { "X-CSRF-Token": "1" },
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch families: ${response.status}`);
  }
  const families: unknown = await response.json();
  if (!Array.isArray(families)) {
    throw new Error("Expected an array of families.");
  }
  return (families as unknown[]).map((family) => {
    if (
      typeof family !== "object" ||
      family === null ||
      !("name" in family) ||
      typeof family.name !== "string"
    ) {
      throw new Error("The API returned an invalid family.");
    }
    return family.name;
  });
}
