// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { issueErrorMessage, listIssues } from "$lib/api/issues";
import { appendUniqueIssues, issueApiParams } from "$lib/issuePageModel";
import type { Issue, IssueFilters } from "$lib/types/issues";

/** One explicitly paged Issues stream. Results and project discovery own separate
 * instances: selecting a project must not cancel or restart facet discovery. */
export class IssueListPages {
  rows = $state<Issue[]>([]);
  totalCount = $state(0);
  nextOffset = $state(0);
  initialLoading = $state(true);
  loadingMore = $state(false);
  error = $state("");
  private failedOffset = 0;
  private generation = 0;
  private live = true;
  private selected: IssueFilters | null = null;
  private scope = "";

  constructor(private currentScope: () => string) {}

  get hasMore() {
    return this.nextOffset < this.totalCount;
  }

  reset(selected: IssueFilters, scope: string) {
    if (!this.live) return;
    ++this.generation;
    this.selected = selected;
    this.scope = scope;
    this.rows = [];
    this.totalCount = 0;
    this.nextOffset = 0;
    this.failedOffset = 0;
    this.error = "";
    this.initialLoading = true;
    this.loadingMore = false;
    return this.load(0);
  }

  more() {
    if (this.initialLoading || this.loadingMore || !this.hasMore || this.error)
      return;
    return this.load(this.nextOffset);
  }

  retry() {
    if (this.initialLoading || this.loadingMore || !this.error) return;
    return this.load(this.failedOffset);
  }

  dispose() {
    this.live = false;
    ++this.generation;
  }

  private async load(offset: number) {
    const selected = this.selected;
    if (!selected) return;
    const generation = this.generation;
    const scope = this.scope;
    // Check the current context as well as the generation, including the window
    // before the route's reactive reset runs. A/B/A resets never revive a page.
    const owns = () =>
      this.live &&
      generation === this.generation &&
      scope === this.currentScope();
    if (!owns()) return;
    if (offset === 0 && this.rows.length === 0) this.initialLoading = true;
    else this.loadingMore = true;
    this.error = "";
    try {
      const response = await listIssues(issueApiParams(selected, offset));
      if (!owns()) return;
      this.rows = appendUniqueIssues(this.rows, response.issues);
      this.totalCount = response.count;
      // Advance by raw response length, never by unique or locally matching rows.
      this.nextOffset = response.offset + response.issues.length;
      this.failedOffset = this.nextOffset;
    } catch (error) {
      if (!owns()) return;
      const message = await issueErrorMessage(error);
      if (!owns()) return;
      this.failedOffset = offset;
      this.error = message;
    } finally {
      if (owns()) {
        this.initialLoading = false;
        this.loadingMore = false;
      }
    }
  }
}
