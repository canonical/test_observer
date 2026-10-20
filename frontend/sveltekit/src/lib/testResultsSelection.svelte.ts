// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

/* eslint-disable svelte/prefer-svelte-reactivity -- Sets are local builders or
 * immutable snapshots assigned wholesale to $state.raw<ReadonlySet>. Published
 * sets are never mutated; their replacement is the reactive notification. */

import {
  cloneFilters,
  filterValues,
  SEARCH_FILTERS,
  type AppliedSearch,
  type SearchFilters,
} from "$lib/testResultsSearch";

export interface SelectionQuery {
  readonly key: string;
  readonly filters: SearchFilters;
}

/** The validated backend predicate, never pagination or local presentation.
 * Wire alternatives (including structured metadata pairs) are sets. Dates keep
 * microseconds, but equivalent timezone/fraction spellings have one identity. */
export function selectionQuery(query: AppliedSearch): SelectionQuery | null {
  if (!query.hasFilters || query.problems.length) return null;
  const filters = cloneFilters(query.filters);
  const entries = SEARCH_FILTERS.map((key) => {
    const values = filterValues(key, filters);
    if (key === "from_date" || key === "until_date") {
      return [
        key,
        values.map((value) => {
          const seconds = value.replace(/\.\d+(?=Z|[+-]\d{2}:\d{2}$)/, "");
          const fraction = /\.(\d+)/.exec(value)?.[1] ?? "";
          return [Date.parse(seconds), fraction.slice(0, 6).padEnd(6, "0")];
        }),
      ];
    }
    return [key, [...new Set(values)].sort()];
  });
  return { key: JSON.stringify(entries), filters };
}

function uniqueIds(ids: Iterable<number>): Set<number> {
  return new Set([...ids].filter((id) => Number.isSafeInteger(id) && id > 0));
}

/** Ephemeral, per-route state. All mode is a rule, not an enumerated result set.
 * Nothing here knows about URLs, views, storage or the network. */
export class TestResultsSelection {
  query = $state.raw<SelectionQuery | null>(null);
  explicitIds = $state.raw<ReadonlySet<number>>(new Set());
  exclusions = $state.raw<ReadonlySet<number>>(new Set());
  allMatches = $state(false);
  matchCount = $state(0);

  setQuery(query: SelectionQuery | null) {
    if (query?.key === this.query?.key) return;
    this.clear();
    this.matchCount = 0;
    this.query = query;
  }

  updateCount(count: number) {
    this.matchCount = Number.isSafeInteger(count) && count >= 0 ? count : 0;
  }

  get selectedCount(): number {
    return this.allMatches
      ? Math.max(0, this.matchCount - this.exclusions.size)
      : this.explicitIds.size;
  }

  isSelected(id: number): boolean {
    return this.allMatches
      ? !this.exclusions.has(id)
      : this.explicitIds.has(id);
  }

  clear() {
    this.allMatches = false;
    this.explicitIds = new Set();
    this.exclusions = new Set();
  }

  /** A page-scoped capability. Callers revoke it on loading, navigation,
   * errors or unmount, so retained DOM/API callbacks cannot touch a new page. */
  page(loadedIds: Iterable<number>, current: () => boolean) {
    const loaded = uniqueIds(loadedIds);
    const owner = this.query?.key;
    const enabled = () =>
      Boolean(owner && owner === this.query?.key && current());
    const isSelected = (id: number) =>
      enabled() && loaded.has(id) && this.isSelected(id);
    const allLoadedSelected = () =>
      loaded.size > 0 && [...loaded].every(isSelected);
    const toggle = (ids: Iterable<number>, next: boolean) => {
      if (!enabled()) return;
      const updated = new Set(
        this.allMatches ? this.exclusions : this.explicitIds,
      );
      for (const id of uniqueIds(ids)) {
        if (!loaded.has(id)) continue;
        if (this.allMatches ? !next : next) updated.add(id);
        else updated.delete(id);
      }
      if (this.allMatches) this.exclusions = updated;
      else this.explicitIds = updated;
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
          this.explicitIds = new Set([...loaded].filter(isSelected));
          this.exclusions = new Set();
          this.allMatches = false;
        } else if (this.matchCount > 0 && allLoadedSelected()) {
          this.explicitIds = new Set();
          this.exclusions = new Set();
          this.allMatches = true;
        }
      },
      clear: () => {
        if (enabled()) this.clear();
      },
    };
  }
}

export type SearchSelectionPage = ReturnType<TestResultsSelection["page"]>;
