// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { fetchApi, FetchError } from "$lib/api/client";
import { getApiRoot } from "$lib/config";
import { userStore } from "$lib/stores/user.svelte";
import { formatIdLabel, type IdFilterKey } from "$lib/searchFilterLabels";

export type LookupListField =
  "artefacts" | "environments" | "test_plans" | "test_cases";
export type LookupField = LookupListField | IdFilterKey;
export interface ValueSuggestion {
  value: string;
  label: string;
  unavailable?: string;
}

export function isLookupList(field: string): field is LookupListField {
  return ["artefacts", "environments", "test_plans", "test_cases"].includes(
    field,
  );
}

/** Display/cache context only, not an authorization decision or a /me request. */
export const suggestionScope = () =>
  `${getApiRoot()}:${JSON.stringify(userStore.current)}`;

export function exactValueProblem(value: string): string | undefined {
  if (value.includes(","))
    return "Cannot select a value containing commas: search links use comma-separated lists.";
  if (value.length === 0 || value !== value.trim())
    return "Cannot select an empty value or surrounding whitespace: search links trim list values.";
  return undefined;
}

const endpoints: Record<LookupField, [string, string, number]> = {
  artefacts: ["artefacts/search", "artefacts", 50],
  environments: ["environments", "environments", 50],
  test_plans: ["test-plans", "test_plans", 50],
  test_cases: ["test-cases", "test_cases", 50],
  issues: ["issues", "issues", 10],
  reviewer_ids: ["users", "users", 10],
};

function record(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new Error("Unexpected suggestion response.");
  return value as Record<string, unknown>;
}

export async function lookupValues(
  field: LookupField,
  query: string,
  families: string[],
  signal: AbortSignal,
): Promise<ValueSuggestion[]> {
  if (query.trim().length < 2) return [];
  const [path, key, limit] = endpoints[field];
  const params = new URLSearchParams({ q: query.trim(), limit: String(limit) });
  if (isLookupList(field))
    for (const family of [...new Set(families)].sort())
      params.append("families", family);
  const res = await fetchApi(`${path}?${params}`, { signal });
  if (!res.ok) throw new FetchError("FetchError", res.status, res);
  const body = record(await res.json());
  if (!Array.isArray(body[key]))
    throw new Error("Unexpected suggestion response.");
  const options = new Map<string, ValueSuggestion>();
  for (const item of body[key].slice(0, limit) as unknown[]) {
    if (field === "issues" || field === "reviewer_ids") {
      const detail = record(item);
      const id = detail.id;
      if (typeof id !== "number" || !Number.isSafeInteger(id) || id <= 0)
        continue;
      options.set(String(id), {
        value: String(id),
        label: formatIdLabel(field, id, detail),
      });
    } else {
      const name = field === "test_cases" ? record(item).test_case : item;
      if (typeof name !== "string") continue;
      options.set(name, {
        value: name,
        label: name,
        unavailable: exactValueProblem(name),
      });
    }
  }
  return [...options.values()];
}

export function suggestionError(error: unknown): string {
  if (error instanceof FetchError) {
    if (error.status === 401)
      return "Sign in to load suggestions. Exact values are still available.";
    if (error.status === 403)
      return "You do not have permission to load suggestions. Exact values are still available.";
  }
  return "Suggestions could not be loaded. Retry, or enter exact values.";
}

export type KnownMetadata = Record<string, string[]>;

/** Only the full metadata map is cached, in memory, for the current session.
 * Remote query results are deliberately not cached. Cancelled bodies never
 * populate this cache; typing in the metadata editor only filters locally. */
class MetadataSuggestions {
  private scope = "";
  private value: KnownMetadata | undefined;
  private expires = 0;

  setScope(scope: string): void {
    if (scope !== this.scope) {
      this.scope = scope;
      this.value = undefined;
    }
  }

  async load(scope: string, signal: AbortSignal): Promise<KnownMetadata> {
    this.setScope(scope);
    if (this.value && Date.now() < this.expires) return this.value;
    const res = await fetchApi("execution-metadata", { signal });
    if (!res.ok) throw new FetchError("FetchError", res.status, res);
    const map = record(record(await res.json()).execution_metadata);
    const entries = Object.entries(map).map(([category, values]) => {
      if (!Array.isArray(values) || !values.every((v) => typeof v === "string"))
        throw new Error("Unexpected metadata response.");
      return [category, [...new Set(values)]] as [string, string[]];
    });
    const value = Object.fromEntries(entries);
    if (
      !signal.aborted &&
      scope === this.scope &&
      scope === suggestionScope()
    ) {
      this.value = value;
      this.expires = Date.now() + 5 * 60_000;
    }
    return value;
  }
}

export const metadataSuggestions = new MetadataSuggestions();
