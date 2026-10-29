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

import type { FamilyName } from "$lib/types/openapi";

export type IssueSource = "github" | "jira" | "launchpad";
export type IssueStatus = "unknown" | "closed" | "open";

export type TestResultStatus = "PASSED" | "FAILED" | "SKIPPED";

export interface Issue {
  id: number;
  source: IssueSource;
  project: string;
  key: string;
  title: string;
  status: IssueStatus;
  url: string;
  test_executions_count?: number;
}

/** Complete rule returned on an issue detail response. */
export interface AttachmentRule {
  id: number;
  enabled: boolean;
  families: FamilyName[];
  artefacts: string[];
  artefact_versions: string[];
  artefact_stages: string[];
  artefact_tracks: string[];
  environment_names: string[];
  test_plans: string[];
  test_case_names: string[];
  template_ids: string[];
  test_result_statuses: TestResultStatus[];
  execution_metadata: Record<string, string[]>;
}

/** GET /v1/issues/{id} response. */
export interface IssueDetail extends Issue {
  labels: string[] | null;
  auto_rerun_enabled: boolean;
  attachment_rules: AttachmentRule[];
}

export interface IssueListResponse {
  issues: Issue[];
  count: number;
  limit: number;
  offset: number;
}

export interface IssueFilters {
  sources: IssueSource[];
  statuses: IssueStatus[];
  families: string[];
  projects: string[];
  query: string;
}

export const ISSUE_SOURCES: IssueSource[] = ["github", "jira", "launchpad"];
export const ISSUE_STATUSES: IssueStatus[] = ["open", "unknown", "closed"];
export const DEFAULT_ISSUE_STATUSES: IssueStatus[] = ["open", "unknown"];
