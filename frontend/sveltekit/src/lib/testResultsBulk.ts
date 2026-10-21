// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { SEARCH_FILTERS, type SearchFilters } from "$lib/testResultsFilters";
import type { AppliedSearch } from "$lib/testResultsSearch";
import type {
  ResultExecutionContext,
  SelectionSnapshot,
} from "$lib/testResultsSelection.svelte";
import {
  freezeValue,
  positiveId,
  predicateFilters,
  selectionQuery,
  type Frozen,
} from "$lib/testResultsPredicate";

export type Capability<T> =
  | { readonly ok: true; readonly value: T }
  | { readonly ok: false; readonly reason: string };
const blocked = (reason: string): Capability<never> => ({ ok: false, reason });
const allowed = <T>(value: T): Capability<Frozen<T>> => ({
  ok: true,
  value: freezeValue(value),
});

/** Separate POST JSON contract: deliberately not the GET/Base64 wire codec or
 * the broader generated schema with pagination and the deprecated alias. */
export type TestResultMutationFilters = {
  readonly [K in Exclude<keyof SearchFilters, "execution_metadata">]?: Frozen<
    NonNullable<SearchFilters[K]>
  >;
} & {
  readonly execution_metadata?: Readonly<Record<string, readonly string[]>>;
};

export function mutationFilters(
  input: Frozen<SearchFilters>,
): TestResultMutationFilters {
  const filters = predicateFilters(input);
  const entries = SEARCH_FILTERS.flatMap((key): [string, unknown][] => {
    if (key === "execution_metadata") {
      return filters.execution_metadata.length
        ? [
            [
              key,
              Object.fromEntries(
                filters.execution_metadata.map(({ category, values }) => [
                  category,
                  [...values],
                ]),
              ),
            ],
          ]
        : [];
    }
    const value = filters[key];
    if (value === null || (Array.isArray(value) && !value.length)) return [];
    return [[key, Array.isArray(value) ? [...value] : value]];
  });
  return freezeValue(Object.fromEntries(entries));
}

function backendHasFilters(filters: TestResultMutationFilters): boolean {
  // TestResultSearchFilters.has_filters explicitly excludes dates.
  return Object.keys(filters).some(
    (key) => key !== "from_date" && key !== "until_date",
  );
}

export interface BulkReadiness {
  readonly available: boolean;
  readonly loading: boolean;
  readonly moving: boolean;
  readonly accessError: boolean;
  readonly unapplied: boolean;
  readonly mutating: boolean;
}

function readyReason(state: BulkReadiness): string | null {
  if (state.unapplied)
    return "Apply or discard draft changes with Search before using bulk actions.";
  if (state.loading || state.moving)
    return "Wait for the current search page to finish loading or moving.";
  if (state.accessError || !state.available)
    return "Load an accessible, successful current search response first.";
  if (state.mutating) return "Wait for the current operation to finish.";
  return null;
}

export type BulkTarget =
  | {
      readonly kind: "explicit";
      readonly queryKey: string;
      readonly resultIds: readonly number[];
      readonly executions: readonly ResultExecutionContext[];
    }
  | {
      readonly kind: "query";
      readonly queryKey: string;
      readonly filters: TestResultMutationFilters;
      readonly count: number;
    };

/** Dialog-open snapshot, not a server snapshot. Query mode is explicit opt-in;
 * zero selection never falls back to all. Counts can change on the server. */
export function freezeBulkTarget(
  selection: SelectionSnapshot,
  applied: AppliedSearch,
  state: BulkReadiness,
): Capability<BulkTarget> {
  const reason = readyReason(state);
  if (reason) return blocked(reason);
  const query = selectionQuery(applied);
  const selected = selection.query;
  if (!query || !selected)
    return blocked(
      "Select results from the current valid applied query first.",
    );
  const selectedQuery = selectionQuery({
    ...selected,
    hasFilters: true,
    problems: [],
  });
  if (query.key !== selectedQuery?.key || query.key !== selected.key)
    return blocked(
      "Select results from the current valid applied query first.",
    );
  if (![...selection.explicitIds, ...selection.exclusions].every(positiveId))
    return blocked(
      "Selection contains invalid result IDs. Clear it and select results again.",
    );
  if (selection.allMatches) {
    if (selection.exclusions.length)
      return blocked(
        "All-matches exclusions are not supported by the server. Remove all exclusions or select explicit rows instead.",
      );
    if (selection.explicitIds.length)
      return blocked(
        "Mixed explicit IDs and all-matches criteria are unsupported. Clear the selection and select again.",
      );
    if (
      !Number.isSafeInteger(selection.matchCount) ||
      selection.matchCount <= 0
    )
      return blocked("There are no current matches selected.");
    const filters = mutationFilters(query.filters);
    if (!backendHasFilters(filters))
      return blocked(
        "The server cannot bulk-mutate a date-only query. Add a non-date condition or select explicit rows.",
      );
    return allowed({
      kind: "query" as const,
      queryKey: query.key,
      filters,
      count: selection.matchCount,
    });
  }
  if (selection.exclusions.length)
    return blocked(
      "Explicit selection cannot contain exclusions. Clear it and select again.",
    );
  const resultIds = [...new Set(selection.explicitIds)].sort((a, b) => a - b);
  if (!resultIds.length)
    return blocked(
      "Select at least one result, or explicitly opt into all matches.",
    );
  const selectedIds = new Set(resultIds);
  // Missing context may still attach issues. Reruns fail closed below rather
  // than treating a result ID as an execution ID or guessing an off-page row.
  const executions = selection.executions
    .filter(({ resultId }) => selectedIds.has(resultId))
    .map(({ resultId, executionId }) => ({ resultId, executionId }));
  return allowed({
    kind: "explicit" as const,
    queryKey: query.key,
    resultIds,
    executions,
  });
}

/** An exclusive union: the backend handles criteria as UNION/OR, never AND. */
export type IssueAttachmentPayload =
  | {
      readonly test_results: readonly number[];
      readonly test_results_filters?: never;
    }
  | {
      readonly test_results_filters: TestResultMutationFilters;
      readonly test_results?: never;
    };

export function issueAttachmentPayload(
  target: BulkTarget,
): IssueAttachmentPayload {
  return target.kind === "explicit"
    ? freezeValue({ test_results: [...target.resultIds] })
    : freezeValue({ test_results_filters: structuredClone(target.filters) });
}

export function executionIds(
  target: BulkTarget,
): Capability<readonly number[]> {
  if (target.kind !== "explicit")
    return blocked("Execution IDs require an explicit result selection.");
  const byResult = new Map<number, number>();
  for (const { resultId, executionId } of target.executions) {
    if (
      !positiveId(resultId) ||
      !positiveId(executionId) ||
      (byResult.has(resultId) && byResult.get(resultId) !== executionId)
    )
      return blocked(
        "Invalid or conflicting selected execution context. Search and select results again.",
      );
    byResult.set(resultId, executionId);
  }
  if (
    !target.resultIds.length ||
    target.resultIds.some((id) => !positiveId(id) || !byResult.has(id))
  )
    return blocked(
      "Execution context is missing for selected results. Search and select those rows again.",
    );
  return allowed(
    [...new Set(target.resultIds.flatMap((id) => byResult.get(id) ?? []))].sort(
      (a, b) => a - b,
    ),
  );
}

export type RerunPayload = (
  | {
      readonly test_execution_ids: readonly number[];
      readonly test_results_filters?: never;
    }
  | {
      readonly test_results_filters: TestResultMutationFilters;
      readonly test_execution_ids?: never;
    }
) & { readonly priority?: number };
export interface RerunOptions {
  /** Defaults on for create, off for delete. Applies latest=true/archive=false. */
  readonly eligibleOnly?: boolean;
  /** Explicit opt-in: exact execution groups, with NO eligibility/request-state
   * guards. The API cannot intersect IDs with filter criteria (they are OR). */
  readonly explicitMode?: "guarded" | "exact";
  readonly priority?: number;
}

export interface RerunPlan {
  readonly payload: RerunPayload;
  /** Required on POST for filter criteria; safe for explicit IDs as well. */
  readonly silent: true;
  readonly scope: "query-intersection" | "exact-execution-groups";
}

/** The server creates/deletes REQUEST GROUPS keyed by (test_plan_id,
 * artefact_build_id, environment_id), not one request per result/execution.
 * Rows do NOT expose execution_is_latest; it cannot be checked locally. */
export function rerunPlan(
  target: BulkTarget,
  operation: "create" | "delete",
  options: RerunOptions = {},
): Capability<RerunPlan> {
  if (
    options.priority !== undefined &&
    (operation !== "create" ||
      !Number.isSafeInteger(options.priority) ||
      Math.abs(options.priority) > 1_000_000)
  )
    return blocked(
      "Rerun priority must be an integer between -1000000 and 1000000, and is only supported for creation.",
    );
  const priority =
    options.priority === undefined ? {} : { priority: options.priority };
  if (target.kind === "explicit") {
    if (options.explicitMode !== "exact" || options.eligibleOnly === true)
      return blocked(
        "The server ORs execution IDs and filters, so guarded explicit reruns cannot be expressed. Choose an all-matches query, or explicitly choose exact execution groups without eligibility/request-state guards.",
      );
    const ids = executionIds(target);
    return ids.ok
      ? allowed({
          payload: { test_execution_ids: [...ids.value], ...priority },
          silent: true as const,
          scope: "exact-execution-groups" as const,
        })
      : ids;
  }
  const filters = structuredClone(target.filters);
  if (!backendHasFilters(filters))
    return blocked("The server cannot bulk-mutate a date-only query.");
  const guards = {
    rerun_is_requested: operation === "delete",
    ...((options.eligibleOnly ?? operation === "create")
      ? { execution_is_latest: true, artefact_is_archived: false }
      : {}),
  };
  for (const [key, value] of Object.entries(guards)) {
    const existing = filters[key as keyof typeof guards];
    if (existing !== undefined && existing !== value)
      return blocked(
        `No eligible matches: applied ${key}=${String(existing)} contradicts required ${String(value)}. Change the query or options; its constraints will not be overridden.`,
      );
  }
  return allowed({
    payload: { test_results_filters: { ...filters, ...guards }, ...priority },
    silent: true as const,
    scope: "query-intersection" as const,
  });
}

export interface AttachmentRuleFilters {
  readonly families?: readonly string[];
  readonly artefacts?: readonly string[];
  readonly artefact_versions?: readonly string[];
  readonly artefact_stages?: readonly string[];
  readonly artefact_tracks?: readonly string[];
  readonly environment_names?: readonly string[];
  readonly test_plans?: readonly string[];
  readonly test_case_names?: readonly string[];
  readonly template_ids?: readonly string[];
  readonly test_result_statuses?: readonly string[];
  readonly execution_metadata?: Readonly<Record<string, readonly string[]>>;
}
const RULE_FIELDS = [
  "families",
  "artefacts",
  "artefact_versions",
  "artefact_stages",
  "artefact_tracks",
  "environments",
  "test_plans",
  "test_cases",
  "template_ids",
  "test_result_statuses",
  "execution_metadata",
];

/** Query-level only. Persistent FUTURE conditions, not an attachment of the
 * current results. Pagination/view are absent; selection is not an argument. */
export function attachmentRuleFilters(
  applied: AppliedSearch,
  state: BulkReadiness,
): Capability<AttachmentRuleFilters> {
  const reason = readyReason(state);
  if (reason) return blocked(reason);
  const query = selectionQuery(applied);
  if (!query)
    return blocked("Apply a valid, nonempty query before creating a rule.");
  const filters = mutationFilters(query.filters);
  const unsupported = Object.keys(filters).filter(
    (key) => !RULE_FIELDS.includes(key),
  );
  if (unsupported.length)
    return blocked(
      `Attachment rules cannot represent: ${unsupported.join(", ")}. Remove those conditions and apply Search first.`,
    );
  if (!Object.keys(filters).some((key) => key !== "test_result_statuses"))
    return blocked(
      "Attachment rules require at least one non-status condition.",
    );
  return allowed(
    Object.fromEntries(
      Object.entries(filters).map(([key, value]) => [
        key === "environments"
          ? "environment_names"
          : key === "test_cases"
            ? "test_case_names"
            : key,
        value,
      ]),
    ) as AttachmentRuleFilters,
  );
}
