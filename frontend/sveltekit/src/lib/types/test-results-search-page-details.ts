// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import type {
  ExecutionMetadata,
  FamilyName,
  MinimalIssueResponse,
  TestExecutionStatus,
  TestResultStatus,
} from "./openapi";

export interface SearchPageDetailsIssue {
  issue: Pick<
    MinimalIssueResponse,
    "id" | "source" | "project" | "key" | "title" | "status" | "url"
  >;
}

export interface SearchPageDetailsResponse {
  test_result: {
    id: number;
    name: string;
    category: string;
    template_id: string;
    status: TestResultStatus;
    io_log: string;
    issues: SearchPageDetailsIssue[];
  };
  test_execution: {
    id: number;
    status: TestExecutionStatus;
    environment: { name: string };
    test_plan: string;
    created_at: string;
    execution_metadata: ExecutionMetadata;
  };
  artefact: {
    id: number;
    name: string;
    version: string;
    track: string;
    family: FamilyName;
  };
  artefact_build: { architecture: string };
}
