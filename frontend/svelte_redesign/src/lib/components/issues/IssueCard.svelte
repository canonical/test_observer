<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { Badge, Chip, Link, Switch } from "@canonical/svelte-ds-app-launchpad";
  import { base } from "$app/paths";
  import type { Issue, IssueSource, IssueStatus } from "$lib/types/issue.js";
  import { capitalize } from "$lib/utils/formatting.js";

  interface Props {
    issue: Issue;
    onautorerunchange?: (issueId: number, enabled: boolean) => void;
  }

  const { issue, onautorerunchange }: Props = $props();

  let autoRerun = $state(false);

  $effect(() => {
    autoRerun = issue.autoRerunEnabled;
  });

  function sourceSeverity(source: IssueSource): "positive" | "caution" | "information" {
    switch (source) {
      case "github":
        return "positive";
      case "jira":
        return "caution";
      case "launchpad":
        return "information";
    }
  }

  function statusSeverity(status: IssueStatus): "positive" | "negative" | "caution" {
    switch (status) {
      case "open":
        return "positive";
      case "closed":
        return "negative";
      case "unknown":
        return "caution";
    }
  }

  function handleAutoRerunToggle(): void {
    autoRerun = !autoRerun;
    onautorerunchange?.(issue.id, autoRerun);
  }
</script>

<div class="ds issue-card">
  <a class="ds issue-card__link" href="{base}/issues/{issue.id}">
    <div class="ds issue-card__header">
      <Chip value={capitalize(issue.source)} severity={sourceSeverity(issue.source)} readonly />
      <span class="ds issue-card__project">{issue.project}</span>
      <span class="ds issue-card__separator">/</span>
      <Link href={issue.url} target="_blank" rel="noopener noreferrer">
        {issue.key}
      </Link>
    </div>

    <div class="ds issue-card__body">
      <span class="ds issue-card__title">{issue.title}</span>
    </div>

    <div class="ds issue-card__footer">
      <Chip value={capitalize(issue.status)} severity={statusSeverity(issue.status)} readonly />
      <span class="ds issue-card__executions">
        <Badge value={issue.testExecutionsCount} />
        test execution{issue.testExecutionsCount !== 1 ? "s" : ""}
      </span>
    </div>
  </a>

  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="ds issue-card__actions" onclick={(e) => e.stopPropagation()}>
    <label class="ds issue-card__toggle">
      <Switch checked={autoRerun} onchange={handleAutoRerunToggle} />
      Auto-rerun
    </label>
  </div>
</div>

<style>
  .ds.issue-card {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.75rem 1rem;
    border: 1px solid var(--color-border, #d9d9d9);
    border-radius: 0.25rem;
  }

  .ds.issue-card:hover {
    background-color: var(--color-background-alt, #f7f7f7);
  }

  .ds.issue-card__link {
    flex: 1;
    text-decoration: none;
    color: inherit;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .ds.issue-card__header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .ds.issue-card__project {
    font-weight: 500;
  }

  .ds.issue-card__separator {
    color: var(--color-text-muted, #999);
  }

  .ds.issue-card__body {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .ds.issue-card__title {
    font-size: 0.95rem;
  }

  .ds.issue-card__footer {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .ds.issue-card__executions {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    font-size: 0.85rem;
    color: var(--color-text-muted, #666);
  }

  .ds.issue-card__actions {
    flex-shrink: 0;
  }

  .ds.issue-card__toggle {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.85rem;
    cursor: pointer;
    white-space: nowrap;
  }
</style>
