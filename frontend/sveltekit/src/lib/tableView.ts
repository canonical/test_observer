// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

// Pure sorting and filtering for the dashboard table, kept apart from the
// component so the behaviour can be tested without a DOM.

import type { Artefact, ColumnSpec } from "$lib/types";
import { columnSortValue, columnValue } from "$lib/artefactMetadata";

export interface SortState {
  id: string;
  desc: boolean;
}

export interface TableView {
  sorting: SortState | null;
  globalFilter: string;
  /** Substring filters keyed by column id. */
  columnFilters: Record<string, string>;
}

export const EMPTY_VIEW: TableView = {
  sorting: null,
  globalFilter: "",
  columnFilters: {},
};

function includesText(haystack: string, needle: string): boolean {
  return haystack.toLowerCase().includes(needle.trim().toLowerCase());
}

/** Rows matching the global search and every column filter. */
export function filterArtefacts(
  artefacts: Artefact[],
  columns: ColumnSpec[],
  visibleIds: ReadonlySet<string>,
  view: Pick<TableView, "globalFilter" | "columnFilters">,
): Artefact[] {
  const global = view.globalFilter.trim();
  const active = columns.filter(
    (c) =>
      Object.hasOwn(view.columnFilters, c.key) &&
      view.columnFilters[c.key].trim() !== "",
  );
  const searchable = columns.filter((c) => visibleIds.has(c.key));
  return artefacts.filter(
    (a) =>
      active.every((c) =>
        includesText(columnValue(a, c), view.columnFilters[c.key]),
      ) &&
      (global === "" ||
        searchable.some((c) => includesText(columnValue(a, c), global))),
  );
}

function compare(a: string | number | null, b: string | number | null): number {
  if (typeof a === "number" && typeof b === "number") return a - b;
  return String(a).localeCompare(String(b), undefined, {
    numeric: true,
    sensitivity: "base",
  });
}

/** Sorts by the given column; empty values always land last. */
export function sortArtefacts(
  artefacts: Artefact[],
  columns: ColumnSpec[],
  sorting: SortState | null,
): Artefact[] {
  const col = sorting && columns.find((c) => c.key === sorting.id);
  if (!sorting || !col) return artefacts;
  const direction = sorting.desc ? -1 : 1;
  return artefacts
    .map((artefact) => ({ artefact, key: columnSortValue(artefact, col) }))
    .sort((x, y) => {
      const xEmpty = x.key === null || x.key === "";
      const yEmpty = y.key === null || y.key === "";
      if (xEmpty || yEmpty) return Number(xEmpty) - Number(yEmpty);
      return direction * compare(x.key, y.key);
    })
    .map(({ artefact }) => artefact);
}

/** Cycles a column through ascending, descending, then unsorted. */
export function nextSorting(
  current: SortState | null,
  id: string,
): SortState | null {
  if (current?.id !== id) return { id, desc: false };
  return current.desc ? null : { id, desc: true };
}

export const PAGE_SIZES = [25, 50, 100] as const;

/** Number of pages needed for the rows; always at least one. */
export function pageCount(total: number, pageSize: number): number {
  return Math.max(1, Math.ceil(total / pageSize));
}

/** The rows on a zero-based page, with the page clamped into range. */
export function paginate<T>(
  rows: T[],
  page: number,
  pageSize: number,
): { rows: T[]; page: number } {
  const clamped = Math.min(
    Math.max(0, page),
    pageCount(rows.length, pageSize) - 1,
  );
  return {
    rows: rows.slice(clamped * pageSize, (clamped + 1) * pageSize),
    page: clamped,
  };
}
