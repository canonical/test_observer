// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import type { TestExecutionStatus } from "$lib/types/openapi";
import type { TestResultStatus } from "$lib/types/artefact-page";

export const RESULT_STATUS_COLORS: Record<TestResultStatus, string> = {
  PASSED: "#0e8420",
  FAILED: "#c7162b",
  SKIPPED: "#757575",
};

export const EXECUTION_STATUS_COLORS: Record<TestExecutionStatus, string> = {
  NOT_STARTED: "#757575",
  IN_PROGRESS: "#757575",
  PASSED: "#0e8420",
  FAILED: "#c7162b",
  NOT_TESTED: "#757575",
  ENDED_PREMATURELY: "#757575",
};
