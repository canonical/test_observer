// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { TestResultStatus } from "./test-result.js";
import type { ExecutionMetadata } from "./test-execution.js";

export type IntListFilter =
  | { type: "list"; values: number[] }
  | { type: "any" }
  | { type: "none" };

export type { ExecutionMetadata };

export interface TestResultsFilters {
  families: string[];
  testResultStatuses: TestResultStatus[];
  artefacts: string[];
  artefactIsArchived?: boolean;
  rerunIsRequested?: boolean;
  executionIsLatest?: boolean;
  environments: string[];
  testCases: string[];
  templateIds: string[];
  executionMetadata: ExecutionMetadata;
  issues: IntListFilter;
  assignees: IntListFilter;
  fromDate?: string;
  untilDate?: string;
  offset?: number;
  limit?: number;
}
