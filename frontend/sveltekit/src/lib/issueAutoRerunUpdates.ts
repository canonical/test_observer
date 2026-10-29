// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { getApiRoot } from "$lib/config";
import { userStore } from "$lib/stores/user.svelte";

type Owner = Readonly<{ scope: string }>;
type Update = Readonly<{ owner: Owner; issueId: number }>;
type Read = Readonly<{ owner: Owner; issueId: number; revision: number }>;
type Event =
  | { type: "busy"; issueId: number }
  | { type: "confirmed"; issueId: number; enabled: boolean };

/** A session-local journal, not a server cache or an authorization grant. Reads
 * begun before a confirmed write must not overwrite it. A later fresh GET is
 * authoritative again. Identity objects prevent A/B/A sessions reviving A's work.
 */
export class IssueAutoRerunUpdates {
  private currentOwner: Owner | null = null;
  private active = new Map<number, Update>();
  private confirmed = new Map<number, { revision: number; enabled: boolean }>();
  private listeners = new Set<(event: Event) => void>();

  owner(scope: string): Owner {
    if (this.currentOwner?.scope !== scope) {
      this.currentOwner = Object.freeze({ scope });
      this.active.clear();
      this.confirmed.clear();
    }
    return this.currentOwner;
  }

  owns(owner: Owner): boolean {
    return this.currentOwner === owner;
  }

  subscribe(listener: (event: Event) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  busy(owner: Owner, issueId: number): boolean {
    return this.owns(owner) && this.active.has(issueId);
  }

  begin(owner: Owner, issueId: number): Update | null {
    if (!this.owns(owner) || this.busy(owner, issueId)) return null;
    const update = Object.freeze({ owner, issueId });
    this.active.set(issueId, update);
    this.notify({ type: "busy", issueId });
    return update;
  }

  confirm(update: Update, enabled: boolean): void {
    if (!this.owns(update.owner) || this.active.get(update.issueId) !== update)
      return;
    const revision = (this.confirmed.get(update.issueId)?.revision ?? 0) + 1;
    this.confirmed.set(update.issueId, { revision, enabled });
    this.notify({ type: "confirmed", issueId: update.issueId, enabled });
  }

  finish(update: Update): void {
    if (!this.owns(update.owner) || this.active.get(update.issueId) !== update)
      return;
    this.active.delete(update.issueId);
    this.notify({ type: "busy", issueId: update.issueId });
  }

  read(owner: Owner, issueId: number): Read {
    return {
      owner,
      issueId,
      revision: this.confirmed.get(issueId)?.revision ?? 0,
    };
  }

  reconcile(read: Read, enabled: boolean): boolean {
    const update = this.confirmed.get(read.issueId);
    return this.owns(read.owner) && update && update.revision > read.revision
      ? update.enabled
      : enabled;
  }

  private notify(event: Event): void {
    for (const listener of this.listeners) listener(event);
  }
}

export const issueAutoRerunUpdates = new IssueAutoRerunUpdates();

/** Display/session invalidation only. Mutation authorization always refreshes
 * /me separately and checks the version-owned gate immediately before writing. */
export function issueAutoRerunSession() {
  return issueAutoRerunUpdates.owner(
    `${getApiRoot()}:${userStore.sessionVersion}:${JSON.stringify(userStore.current)}`,
  );
}
