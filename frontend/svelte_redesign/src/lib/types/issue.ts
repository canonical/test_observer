// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { AttachmentRule } from "./attachment-rule.js";

export type IssueSource = "github" | "jira" | "launchpad";
export type IssueStatus = "unknown" | "closed" | "open";

export interface Issue {
  id: number;
  source: IssueSource;
  project: string;
  key: string;
  title: string;
  status: IssueStatus;
  url: string;
  autoRerunEnabled: boolean;
  testExecutionsCount: number;
}

export interface IssueWithContext extends Issue {
  attachmentRules: AttachmentRule[];
}
