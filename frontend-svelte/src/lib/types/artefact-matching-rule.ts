// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

export interface ArtefactMatchingRule {
  id: number;
  series?: string;
  repo?: string;
  source?: string;
  model?: string;
  project?: string;
  baseImageTag?: string;
  launchpadHosted?: boolean;
  team?: TeamMinimal;
}

export interface TeamMinimal {
  id: number;
  name: string;
}

export interface ArtefactMatchingRulePatch {
  series?: string | null;
  repo?: string | null;
  source?: string | null;
  model?: string | null;
  project?: string | null;
  baseImageTag?: string | null;
  launchpadHosted?: boolean | null;
  teamId?: number | null;
}
