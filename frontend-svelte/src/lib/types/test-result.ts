// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { IssueAttachment } from "./attachment-rule.js";
import type { TestExecution } from "./test-execution.js";
import type { Artefact } from "./artefact.js";
import type { ArtefactBuildMinimal } from "./build.js";

export type TestResultStatus = "FAILED" | "PASSED" | "SKIPPED";

export interface PreviousTestResult {
  status: TestResultStatus;
  version: string;
  artefactId: number;
  testExecutionId: number;
  testResultId: number;
}

export interface TestResult {
  id: number;
  name: string;
  status: TestResultStatus;
  createdAt: string;
  category: string;
  comment: string;
  templateId: string;
  ioLog: string;
  previousResults: PreviousTestResult[];
  issueAttachments: IssueAttachment[];
}

export interface TestResultWithContext {
  testResult: TestResult;
  testExecution: TestExecution;
  artefact: Artefact;
  artefactBuild: ArtefactBuildMinimal;
}

export interface TestResultsSearchResult {
  count: number;
  testResults: TestResultWithContext[];
}

export interface TestIssue {
  id: number;
  templateId: string;
  caseName: string;
  description: string;
  url: string;
}
