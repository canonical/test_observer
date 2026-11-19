// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

/** Read the family enum from the backend's runtime OpenAPI document. */
export async function fetchApiFamilyNames(
  fetcher: typeof fetch,
  apiRoot: string,
): Promise<string[]> {
  const response = await fetcher(`${apiRoot}/openapi.json`, {
    credentials: "include",
    headers: { "X-CSRF-Token": "1" },
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch API schema: ${response.status}`);
  }
  return extractApiFamilyNames(await response.json());
}

/** Extract the backend-owned FamilyName enum without duplicating its values. */
export function extractApiFamilyNames(document: unknown): string[] {
  const root = asRecord(document);
  if (!root) {
    throw new Error("The API schema is not an object.");
  }
  const components = asRecord(root.components);
  if (!components) {
    throw new Error("The API schema has no components.");
  }
  const schemas = asRecord(components.schemas);
  if (!schemas) {
    throw new Error("The API schema has no component schemas.");
  }
  const familyNameSchema = asRecord(schemas.FamilyName);
  if (!familyNameSchema) {
    throw new Error("The API schema has no FamilyName enum.");
  }
  const values = familyNameSchema.enum;
  if (!Array.isArray(values) || values.length === 0) {
    throw new Error("The API FamilyName enum is invalid.");
  }
  const names: string[] = [];
  for (const value of values as unknown[]) {
    if (typeof value !== "string") {
      throw new Error("The API FamilyName enum is invalid.");
    }
    names.push(value);
  }
  return names;
}

function asRecord(value: unknown): Record<string, unknown> | null {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return null;
  }
  return value as Record<string, unknown>;
}
