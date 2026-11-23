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

// Generic accessors that turn a data-driven ColumnSpec into displayable/sortable
// values. Nothing here branches on a specific family — the named `format`
// values are reusable value transformations, not family identifiers.

import type { Artefact, ColumnSpec } from "$lib/types";
import { EMPTY_STAGE_LABEL, STATUS_COLORS, STATUS_LABELS } from "$lib/types";

export const ARTEFACT_COLUMNS: ColumnSpec[] = [
  { label: "Name", key: "name", field: "name" },
  { label: "Version", key: "version", field: "version" },
  { label: "Stage", key: "stage", field: "stage", format: "stage" },
  { label: "Track", key: "track", field: "track" },
  { label: "Branch", key: "branch", field: "branch" },
  { label: "Series", key: "series", field: "series" },
  { label: "Repo", key: "repo", field: "repo" },
  { label: "Source", key: "source", field: "source" },
  { label: "OS", key: "os", field: "os" },
  { label: "Release", key: "release", field: "release" },
  { label: "Owner", key: "owner", field: "owner" },
  { label: "Store", key: "store", field: "store", hidden: true },
  { label: "Risk", key: "risk", field: "risk" },
  { label: "SHA256", key: "sha256", field: "sha256", hidden: true },
  { label: "Image URL", key: "imageUrl", field: "image_url", hidden: true },
  { label: "Due date", key: "dueDate", field: "due_date", format: "date" },
  { label: "Created", key: "createdAt", field: "created_at", format: "date" },
  { label: "Reviews", key: "reviewsRemaining", format: "reviewsRemaining" },
  { label: "Status", key: "status", field: "status", format: "status" },
  { label: "Reviewers", key: "reviewers", format: "reviewers" },
  { label: "Bug link", key: "bugLink", field: "bug_link", hidden: true },
  { label: "Jira issue", key: "jiraIssue", field: "jira_issue", hidden: true },
  { label: "Comment", key: "comment", field: "comment", hidden: true },
  { label: "Archived", key: "archived", field: "archived", hidden: true },
];

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
    case "stage":
      return fieldValue(a, col.field) || EMPTY_STAGE_LABEL;
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
