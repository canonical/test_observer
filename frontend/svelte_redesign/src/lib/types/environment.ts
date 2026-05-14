// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { User } from "./user.js";
import type { TestExecution } from "./test-execution.js";

export interface Environment {
  id: number;
  name: string;
  architecture: string;
}

export type EnvironmentReviewDecision =
  | "REJECTED"
  | "APPROVED_INCONSISTENT_TEST"
  | "APPROVED_UNSTABLE_PHYSICAL_INFRA"
  | "APPROVED_CUSTOMER_PREREQUISITE_FAIL"
  | "APPROVED_FAULTY_HARDWARE"
  | "APPROVED_ALL_TESTS_PASS";

export interface EnvironmentReviewArtefactBuild {
  id: number;
  architecture: string;
  revision: number | null;
}

export interface EnvironmentReview {
  id: number;
  artefactBuild: EnvironmentReviewArtefactBuild;
  environment: Environment;
  reviewComment: string;
  reviewDecision: EnvironmentReviewDecision[];
  reviewers: User[];
}

export interface EnvironmentIssue {
  id: number;
  environmentName: string;
  description: string;
  url: string | null;
  isConfirmed: boolean;
}

export interface ArtefactEnvironment {
  review: EnvironmentReview;
  runsDescending: TestExecution[];
}
