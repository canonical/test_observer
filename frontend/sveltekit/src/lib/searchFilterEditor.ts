// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import {
  FILTER_DEFINITIONS,
  type SearchFilter,
  type SearchFilters,
} from "$lib/testResultsFilters";
import type { Family } from "$lib/types";
import { familyDisplayName } from "$lib/types";
import {
  idLabelKey,
  loadingIdLabel,
  type IdFilterKey,
} from "$lib/searchFilterLabels";

export type ListFilterKey = {
  [K in SearchFilter]: SearchFilters[K] extends string[] ? K : never;
}[SearchFilter];
export type BooleanFilterKey =
  "artefact_is_archived" | "rerun_is_requested" | "execution_is_latest";
export type InstantFilterKey = "from_date" | "until_date";
export const isListFilter = (key: SearchFilter): key is ListFilterKey =>
  FILTER_DEFINITIONS[key].kind === "list";
export const isBooleanFilter = (key: SearchFilter): key is BooleanFilterKey =>
  FILTER_DEFINITIONS[key].kind === "boolean";
export const isIdFilter = (key: SearchFilter): key is IdFilterKey =>
  FILTER_DEFINITIONS[key].kind === "ids";
export const isInstantFilter = (key: SearchFilter): key is InstantFilterKey =>
  FILTER_DEFINITIONS[key].kind === "instant";

export const BOOLEAN_LABELS: Record<BooleanFilterKey, [string, string]> = {
  artefact_is_archived: ["Non archived only", "Archived only"],
  rerun_is_requested: ["No rerun requested", "Rerun requested"],
  execution_is_latest: ["Older executions only", "Latest execution only"],
};
export const ID_MODE_LABELS: Record<
  IdFilterKey,
  { any: string; none: string }
> = {
  issues: { any: "Has any issue", none: "Has no issues" },
  reviewer_ids: { any: "Has any reviewer", none: "Has no reviewer" },
};
export const statusDisplayName = (status: string) =>
  status.charAt(0) + status.slice(1).toLowerCase();

export function filterValueLabels(
  key: SearchFilter,
  filters: SearchFilters,
  families: Family[],
  labels: Record<string, string>,
): string[] {
  if (isListFilter(key))
    return filters[key].map((value) => {
      if (key === "families") {
        const family = families.find((family) => family.api_name === value);
        return family ? familyDisplayName(family) : value;
      }
      if (key === "test_result_statuses") return statusDisplayName(value);
      if (key === "artefact_stages" && value === "") return "(none)";
      return value;
    });
  if (isBooleanFilter(key)) {
    const value = filters[key];
    return value === null ? [] : [BOOLEAN_LABELS[key][Number(value)]];
  }
  if (isIdFilter(key)) {
    const value = filters[key];
    return Array.isArray(value)
      ? value.map((id) => labels[idLabelKey(key, id)] ?? loadingIdLabel(id))
      : [ID_MODE_LABELS[key][value]];
  }
  if (key === "execution_metadata")
    return filters.execution_metadata.flatMap(({ category, values }) =>
      values.map(
        (value) => `${JSON.stringify(category)} = ${JSON.stringify(value)}`,
      ),
    );
  const value = filters[key];
  return value === null ? [] : [value];
}
