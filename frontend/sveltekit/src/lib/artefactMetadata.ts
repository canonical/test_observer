// Copyright 2026 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

// Generic accessors that turn a data-driven ColumnSpec/FilterSpec (declared per
// family in families.json) into displayable/sortable/filterable values. Nothing
// here branches on a specific family — the named `format`/`category` values are
// reusable value transformations, not family identifiers.

import type { Artefact, ColumnSpec, FilterSpec } from "$lib/types";
import { STATUS_COLORS, STATUS_LABELS } from "$lib/types";

function fieldValue(a: Artefact, field?: string): string {
  if (!field) return "";
  const v: unknown = (a as unknown as Record<string, unknown>)[field];
  if (typeof v === "string") return v;
  if (typeof v === "number" || typeof v === "boolean") return String(v);
  return "";
}

function reviewsRemaining(a: Artefact): number {
  return (
    a.all_environment_reviews_count - a.completed_environment_reviews_count
  );
}

// Display string for the reviewers column ("N/A" when unassigned).
function reviewersColumnValue(reviewers: Artefact["reviewers"]): string {
  const r = reviewers ?? [];
  if (r.length === 0) return "N/A";
  if (r.length === 1) return r[0].name;
  return `${r.length} reviewers`;
}

// Grouping label for the reviewers filter ("Unassigned" when there are none).
function reviewersFilterValue(reviewers: Artefact["reviewers"]): string {
  const r = reviewers ?? [];
  if (r.length === 0) return "Unassigned";
  if (r.length === 1) return r[0].name;
  return `${r.length} reviewers`;
}

function dueDateCategory(dueDate: string | null): string {
  if (!dueDate) return "No due date";
  const due = new Date(dueDate);
  const now = new Date();
  if (due < now) return "Overdue";
  const diffDays = (due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);
  if (diffDays < 7) return "Within a week";
  return "More than a week";
}

/** Value shown in a table cell for the given column. */
export function columnValue(a: Artefact, col: ColumnSpec): string {
  switch (col.format) {
    case "date": {
      const raw = fieldValue(a, col.field);
      return raw ? new Date(raw).toLocaleDateString() : "";
    }
    case "reviewsRemaining":
      return String(reviewsRemaining(a));
    case "status":
      return STATUS_LABELS[a.status];
    case "reviewers":
      return reviewersColumnValue(a.reviewers);
    default:
      return fieldValue(a, col.field);
  }
}

/** Optional text colour for a table cell (currently only status columns). */
export function columnColor(a: Artefact, col: ColumnSpec): string | undefined {
  if (col.format === "status") return STATUS_COLORS[a.status];
  return undefined;
}

/** Comparable value used when sorting by the given column. */
export function columnSortValue(
  a: Artefact,
  col: ColumnSpec,
): string | number | null {
  switch (col.format) {
    case "date":
      return fieldValue(a, col.field) || null;
    case "reviewsRemaining":
      return reviewsRemaining(a);
    case "reviewers":
      return a.reviewers?.[0]?.name ?? null;
    default:
      return fieldValue(a, col.field);
  }
}

/** Grouping value used when filtering by the given filter. */
export function filterValue(a: Artefact, filter: FilterSpec): string {
  switch (filter.category) {
    case "reviewers":
      return reviewersFilterValue(a.reviewers);
    case "dueDate":
      return dueDateCategory(fieldValue(a, filter.field) || null);
    default:
      return fieldValue(a, filter.field);
  }
}
