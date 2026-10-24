// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

/* eslint-disable svelte/prefer-svelte-reactivity -- Sets are local builders or
 * immutable snapshots assigned wholesale to $state.raw<ReadonlySet>. Published
 * sets are never mutated; their replacement is the reactive notification. */

import {
  freezeValue,
  positiveId,
  selectionQuery,
  type SelectionQuery,
} from "$lib/testResultsPredicate";
export { selectionQuery, type SelectionQuery } from "$lib/testResultsPredicate";

/** Deliberately contains no row objects, logs, metadata or invented latest flag. */
export interface ResultExecutionContext {
  readonly resultId: number;
  readonly executionId: number;
}

export interface SelectionSnapshot {
  readonly query: SelectionQuery | null;
  readonly explicitIds: readonly number[];
  readonly exclusions: readonly number[];
  readonly allMatches: boolean;
  readonly matchCount: number;
  readonly executions: readonly ResultExecutionContext[];
}

function uniqueIds(ids: Iterable<number>): Set<number> {
  return new Set([...ids].filter(positiveId));
}

/** Ephemeral, per-route state. All mode is a rule, not an enumerated result set.
 * Nothing here knows about URLs, views, storage or the network. */
export class TestResultsSelection {
  private activeQuery = $state.raw<SelectionQuery | null>(null);
  private selectedIds = $state.raw<ReadonlySet<number>>(new Set());
  private excludedIds = $state.raw<ReadonlySet<number>>(new Set());
  private executions = $state.raw<readonly ResultExecutionContext[]>([]);
  private epoch = $state(0);
  allMatches = $state(false);
  matchCount = $state(0);

  get query() {
    return this.activeQuery;
  }
  // Read-only TS types alone do not prevent callers mutating a Set at runtime.
  get explicitIds(): ReadonlySet<number> {
    return new Set(this.selectedIds);
  }
  get exclusions(): ReadonlySet<number> {
    return new Set(this.excludedIds);
  }

  snapshot(): SelectionSnapshot {
    return freezeValue({
      query: this.activeQuery,
      explicitIds: [...this.selectedIds],
      exclusions: [...this.excludedIds],
      allMatches: this.allMatches,
      matchCount: this.matchCount,
      executions: this.executions.map((item) => ({ ...item })),
    });
  }

  setQuery(query: SelectionQuery | null) {
    const normalized = query
      ? selectionQuery({
          filters: query.filters,
          hasFilters: true,
          problems: [],
        })
      : null;
    if (normalized?.key === this.query?.key) return;
    this.clear();
    this.matchCount = 0;
    this.activeQuery = normalized;
  }

  updateCount(count: number) {
    this.matchCount = Number.isSafeInteger(count) && count >= 0 ? count : 0;
  }

  get selectedCount(): number {
    return this.allMatches
      ? Math.max(0, this.matchCount - this.excludedIds.size)
      : this.selectedIds.size;
  }

  isSelected(id: number): boolean {
    return this.allMatches
      ? !this.excludedIds.has(id)
      : this.selectedIds.has(id);
  }

  clear() {
    this.epoch++;
    this.allMatches = false;
    this.selectedIds = new Set();
    this.excludedIds = new Set();
    this.executions = [];
  }

  /** A page-scoped capability. Callers revoke it on loading, navigation,
   * errors or unmount, so retained DOM/API callbacks cannot touch a new page. */
  page(
    loadedIds: Iterable<number>,
    current: () => boolean,
    contexts: Iterable<ResultExecutionContext> = [],
  ) {
    const loaded = uniqueIds(loadedIds);
    const owner = this.query?.key;
    const epoch = this.epoch;
    // Captured once from a successful current response; never retain that response.
    const available = [...contexts]
      .filter(
        (item) => loaded.has(item.resultId) && positiveId(item.executionId),
      )
      .map(({ resultId, executionId }) => ({ resultId, executionId }));
    const enabled = () => {
      const currentKey = this.query?.key;
      return Boolean(
        owner && owner === currentKey && epoch === this.epoch && current(),
      );
    };
    const retainContext = () => {
      const byId = new Map(
        this.executions.map((item) => [item.resultId, item]),
      );
      for (const item of available) byId.set(item.resultId, item);
      this.executions = freezeValue(
        [...byId.values()].filter(
          (item) => !this.allMatches && this.selectedIds.has(item.resultId),
        ),
      );
    };
    const isSelected = (id: number) =>
      enabled() && loaded.has(id) && this.isSelected(id);
    const allLoadedSelected = () =>
      loaded.size > 0 && [...loaded].every(isSelected);
    const toggle = (ids: Iterable<number>, next: boolean) => {
      if (!enabled()) return;
      const updated = new Set(
        this.allMatches ? this.excludedIds : this.selectedIds,
      );
      for (const id of uniqueIds(ids)) {
        if (!loaded.has(id)) continue;
        if (this.allMatches ? !next : next) updated.add(id);
        else updated.delete(id);
      }
      if (this.allMatches) this.excludedIds = updated;
      else this.selectedIds = updated;
      retainContext();
    };
    return {
      enabled,
      isSelected,
      allLoadedSelected,
      toggle,
      headerState: (displayed: Iterable<number>): "none" | "some" | "all" => {
        const ids = [...uniqueIds(displayed)].filter((id) => loaded.has(id));
        const selected = ids.filter(isSelected).length;
        return !selected ? "none" : selected === ids.length ? "all" : "some";
      },
      toggleAllMatches: () => {
        if (!enabled()) return;
        if (this.allMatches) {
          // Opting out keeps selected rows on the entire loaded backend page,
          // including locally hidden rows, but drops the unbounded rule.
          this.selectedIds = new Set([...loaded].filter(isSelected));
          this.excludedIds = new Set();
          this.allMatches = false;
        } else if (this.matchCount > 0 && allLoadedSelected()) {
          this.selectedIds = new Set();
          this.excludedIds = new Set();
          this.allMatches = true;
        }
        retainContext();
      },
      clear: () => {
        if (enabled()) this.clear();
      },
    };
  }
}

export type SearchSelectionPage = ReturnType<TestResultsSelection["page"]>;
