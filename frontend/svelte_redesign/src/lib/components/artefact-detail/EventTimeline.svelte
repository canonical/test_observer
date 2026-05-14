<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import type { TestEvent } from "$lib/types/test-execution.js";

  interface Props {
    events: TestEvent[];
  }

  const { events }: Props = $props();

  function formatTimestamp(iso: string): string {
    return new Date(iso).toLocaleString("en-GB", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  }
</script>

<div class="ds event-timeline">
  <h4 class="ds event-timeline__heading">Event Timeline</h4>
  <ul class="ds event-timeline__list">
    {#each events as event, i (i)}
      <li class="ds event-timeline__item">
        <span class="ds event-timeline__dot"></span>
        <div class="ds event-timeline__content">
          <span class="ds event-timeline__name">{event.eventName}</span>
          <span class="ds event-timeline__time">{formatTimestamp(event.timestamp)}</span>
          {#if event.detail}
            <span class="ds event-timeline__detail">{event.detail}</span>
          {/if}
        </div>
      </li>
    {/each}
  </ul>
</div>

<style>
  .ds.event-timeline {
    margin-top: 0.75rem;
  }

  .ds.event-timeline__heading {
    font-size: 0.875rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
  }

  .ds.event-timeline__list {
    list-style: none;
    padding: 0;
    margin: 0;
    border-left: 2px solid var(--color-border, #d9d9d9);
    padding-left: 1rem;
  }

  .ds.event-timeline__item {
    display: flex;
    gap: 0.5rem;
    align-items: flex-start;
    padding-bottom: 0.75rem;
    position: relative;
  }

  .ds.event-timeline__dot {
    position: absolute;
    left: -1.3rem;
    top: 0.25rem;
    width: 0.5rem;
    height: 0.5rem;
    border-radius: 50%;
    background-color: var(--color-link, #06c);
  }

  .ds.event-timeline__content {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .ds.event-timeline__name {
    font-weight: 500;
    font-size: 0.875rem;
  }

  .ds.event-timeline__time {
    font-size: 0.75rem;
    color: var(--color-text-muted, #666);
  }

  .ds.event-timeline__detail {
    font-size: 0.8125rem;
    color: var(--color-text-muted, #666);
  }
</style>
