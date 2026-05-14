// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { Environment } from "./environment.js";
import type { EnvironmentReview } from "./environment.js";

export type TestExecutionStatus =
  | "FAILED"
  | "NOT_STARTED"
  | "NOT_TESTED"
  | "IN_PROGRESS"
  | "PASSED"
  | "ENDED_PREMATURELY";

export interface ExecutionMetadata {
  data: Record<string, string[]>;
}

export interface TestExecutionRelevantLink {
  id: number;
  label: string;
  url: string;
}

export interface TestExecution {
  id: number;
  ciLink: string | null;
  c3Link: string | null;
  status: TestExecutionStatus;
  environment: Environment;
  isRerunRequested: boolean;
  artefactBuildId?: number;
  testPlan: string;
  relevantLinks: TestExecutionRelevantLink[];
  createdAt: string;
  executionMetadata: ExecutionMetadata;
  isTriaged: boolean;
}

export interface TestEvent {
  eventName: string;
  timestamp: string;
  detail: string;
}

export interface RerunRequest {
  testExecutionId: number;
  ciLink: string;
}

export interface EnrichedTestExecution {
  testExecution: TestExecution;
  environmentReview: EnvironmentReview;
}
