// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { TestExecution } from "./test-execution.js";

export interface ArtefactBuild {
  id: number;
  architecture: string;
  revision: number | null;
  testExecutions: TestExecution[];
}

export interface ArtefactBuildMinimal {
  id: number;
  architecture: string;
  revision?: number;
}
