// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { User } from "./user.js";

export type ArtefactStatus = "APPROVED" | "MARKED_AS_FAILED" | "UNDECIDED";

export interface Artefact {
  id: number;
  name: string;
  version: string;
  family: string;
  track: string;
  store: string;
  branch: string;
  series: string;
  repo: string;
  source: string;
  os: string;
  release: string;
  owner: string;
  sha256: string;
  imageUrl: string;
  status: ArtefactStatus;
  comment: string;
  stage: string;
  allEnvironmentReviewsCount: number;
  completedEnvironmentReviewsCount: number;
  reviewers: User[];
  bugLink: string;
  dueDate?: string;
}

export interface ArtefactVersion {
  artefactId: number;
  version: string;
}

export interface ArtefactHistoryItem {
  artefactId: number;
  name: string;
  version: string;
  stage: string;
  createdAt: string;
}

export interface ArtefactHistory {
  count: number;
  items: ArtefactHistoryItem[];
}

export interface ArtefactSearchResult {
  artefacts: string[];
  count: number;
  limit: number;
  offset: number;
}
