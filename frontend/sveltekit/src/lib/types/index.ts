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

export interface User {
  id: number;
  email: string;
  name: string;
  launchpad_handle: string | null;
  teams: { permissions: string[] }[];
  is_admin: boolean;
}

export interface Family {
  name: string;
  friendly_name: string;
  api_name: string;
  stages: string[];
  columns: ColumnSpec[];
  filters: FilterSpec[];
}

// A table column, described by data (from families.json) rather than code.
// `field` names an Artefact property to read; `format` optionally names a
// generic formatter (see artefactMetadata.ts). Neither is family-specific.
export interface ColumnSpec {
  label: string;
  key: string;
  field?: string;
  format?: string;
  /** Starts out of view, still listed in the grid's "Choose columns" menu. */
  hidden?: boolean;
}

// A filter, described by data (from families.json). `field` names an Artefact
// property to group by; `category` optionally names a generic bucketing
// function (see artefactMetadata.ts). Neither is family-specific.
export interface FilterSpec {
  label: string;
  field?: string;
  category?: string;
}

export type ArtefactStatus = "APPROVED" | "MARKED_AS_FAILED" | "UNDECIDED";
export type ViewMode = "dashboard" | "list";

// A type alias rather than an interface because only object type aliases get
// TypeScript's implicit index signature, which is what lets this satisfy
// SvGrid's `RowData extends Record<string, unknown>` constraint.
// eslint-disable-next-line @typescript-eslint/consistent-type-definitions
export type Artefact = {
  id: number;
  name: string;
  version: string;
  track: string;
  store: string;
  branch: string;
  series: string;
  repo: string;
  source: string;
  os: string;
  release: string;
  owner: string;
  sha256: string;
  image_url: string;
  stage: string;
  risk: string;
  family: string;
  status: ArtefactStatus;
  comment: string;
  archived: boolean;
  // The API omits reviewers (null) when none are assigned; loaders normalise
  // this to an empty array.
  reviewers: User[] | null;
  due_date: string | null;
  created_at: string;
  bug_link: string;
  jira_issue: string | null;
  all_environment_reviews_count: number;
  completed_environment_reviews_count: number;
};

export const STATUS_COLORS: Record<ArtefactStatus, string> = {
  APPROVED: "#0e8420",
  MARKED_AS_FAILED: "#c7162b",
  UNDECIDED: "#666",
};

export const STATUS_LABELS: Record<ArtefactStatus, string> = {
  APPROVED: "Approved",
  MARKED_AS_FAILED: "Rejected",
  UNDECIDED: "Undecided",
};

export function formatDueDate(isoDate: string | null): string | null {
  if (!isoDate) return null;
  const d = new Date(isoDate);
  const month = d.toLocaleString("en-US", { month: "long" });
  return `${month} ${d.getDate()}`;
}

export function stageDisplayName(stage: string): string {
  if (stage === "") return "PPAs";
  return stage.charAt(0).toUpperCase() + stage.slice(1);
}

export function userInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }
  return (parts[0]?.[0] ?? "").toUpperCase();
}
