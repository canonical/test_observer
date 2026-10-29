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

import {
  DEFAULT_ISSUE_STATUSES,
  ISSUE_SOURCES,
  ISSUE_STATUSES,
  type Issue,
  type IssueFilters,
  type IssueSource,
  type IssueStatus,
} from "$lib/types/issues";

export const ISSUE_PAGE_SIZE = 50;

function values(params: URLSearchParams, name: string): string[] {
  return params
    .getAll(name)
    .flatMap((value) => value.split(","))
    .map((value) => value.trim())
    .filter(Boolean);
}

function unique<T extends string>(items: T[]): T[] {
  return [...new Set(items)];
}

/** Read the issue list state from the shareable page URL. */
export function parseIssueFilters(
  params: URLSearchParams,
  familyOptions: string[],
): IssueFilters {
  const sources = unique(
    values(params, "source").filter((value): value is IssueSource =>
      ISSUE_SOURCES.includes(value as IssueSource),
    ),
  );
  const statuses = params.has("status")
    ? unique(
        values(params, "status").filter((value): value is IssueStatus =>
          ISSUE_STATUSES.includes(value as IssueStatus),
        ),
      )
    : [...DEFAULT_ISSUE_STATUSES];
  const knownFamilies = new Set(familyOptions);
  const families = unique(
    values(params, "family").filter((value) => knownFamilies.has(value)),
  );
  const projects = unique(values(params, "project"));
  return {
    sources,
    statuses,
    families,
    projects,
    query: (params.get("q") ?? "").trim(),
  };
}

/** Build a bounded API page query. A single source uses its server-side
 * filter; source multi-select and project selection are applied to each page. */
export function issueApiParams(
  filters: IssueFilters,
  offset: number,
): URLSearchParams {
  const params = new URLSearchParams({
    limit: String(ISSUE_PAGE_SIZE),
    offset: String(offset),
  });
  if (filters.sources.length === 1) params.set("source", filters.sources[0]);
  for (const status of filters.statuses) params.append("status", status);
  for (const family of filters.families) params.append("families", family);
  if (filters.query) params.set("q", filters.query);
  return params;
}

/** Filter the server-paged rows by local multi-select dimensions. */
export function filterIssueRows(
  issues: Issue[],
  filters: IssueFilters,
): Issue[] {
  return issues.filter(
    (issue) =>
      (filters.sources.length === 0 ||
        filters.sources.includes(issue.source)) &&
      (filters.projects.length === 0 ||
        filters.projects.includes(issue.project)),
  );
}

/** Keep pagination deterministic if a backend page overlaps an earlier page. */
export function appendUniqueIssues(
  existing: Issue[],
  incoming: Issue[],
): Issue[] {
  const ids = new Set(existing.map((issue) => issue.id));
  const uniqueIncoming: Issue[] = [];
  for (const issue of incoming) {
    if (ids.has(issue.id)) continue;
    ids.add(issue.id);
    uniqueIncoming.push(issue);
  }
  return [...existing, ...uniqueIncoming];
}

/** Return a helpful validation message unless this is a supported tracker URL. */
export function externalIssueUrlError(value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) return "Enter an issue URL.";

  let url: URL;
  try {
    url = new URL(trimmed);
  } catch {
    return "Enter a valid absolute issue URL.";
  }
  if (
    url.protocol !== "https:" ||
    url.username !== "" ||
    url.password !== "" ||
    url.port !== ""
  ) {
    return "Use an HTTPS URL from GitHub, Jira, or Launchpad.";
  }

  const supported =
    (url.hostname === "github.com" &&
      /^\/[^/]+\/[^/]+\/issues\/\d+$/.test(url.pathname)) ||
    (url.hostname === "warthogs.atlassian.net" &&
      /^\/browse\/[A-Za-z]+-\d+$/.test(url.pathname)) ||
    (url.hostname === "bugs.launchpad.net" &&
      /^\/[^/]+(?:\/\+source\/[^/]+)?\/\+bug\/\d+$/.test(url.pathname));
  return supported
    ? null
    : "Enter a supported GitHub issue, Jira issue, or Launchpad bug URL.";
}

export function issueFilterKey(filters: IssueFilters): string {
  return JSON.stringify({
    sources: [...filters.sources].sort(),
    statuses: [...filters.statuses].sort(),
    families: [...filters.families].sort(),
    projects: [...filters.projects].sort(),
    query: filters.query,
  });
}
