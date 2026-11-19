// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

/** Compact row data returned only by /v1/test-results/search-page. */
export type SearchPageTestResultStatus = "PASSED" | "FAILED" | "SKIPPED";

export interface SearchPageTestResult {
  id: number;
  created_at: string;
  name: string;
  category: string;
  status: SearchPageTestResultStatus;
}

export interface SearchPageEnvironment {
  name: string;
}

export interface SearchPageTestExecution {
  id: number;
  environment: SearchPageEnvironment;
  test_plan: string;
}

export interface SearchPageArtefact {
  id: number;
  name: string;
  version: string;
  track: string;
  family: "snap" | "deb" | "charm" | "image" | "solution";
}

export interface SearchPageArtefactBuild {
  architecture: string;
}

export interface TestResultSearchPageRow {
  test_result: SearchPageTestResult;
  test_execution: SearchPageTestExecution;
  artefact: SearchPageArtefact;
  artefact_build: SearchPageArtefactBuild;
}

export interface TestResultSearchPageResponse {
  count: number | null;
  limit: number;
  offset: number;
  test_results: TestResultSearchPageRow[];
}
