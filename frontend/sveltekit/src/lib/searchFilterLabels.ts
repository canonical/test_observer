// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { fetchApi } from "$lib/api/client";
import { getApiRoot } from "$lib/config";
import { userStore } from "$lib/stores/user.svelte";

export type IdFilterKey = "issues" | "reviewer_ids";
export const idLabelKey = (kind: IdFilterKey, id: number) => `${kind}:${id}`;
export const loadingIdLabel = (id: number) => `#${id} loading…`;
const unavailable = (id: number) => `#${id} details unavailable`;

/** Shared by detail hydration and rich lookup results; IDs remain identity. */
export function formatIdLabel(
  kind: IdFilterKey,
  id: number,
  body: Record<string, unknown>,
): string {
  const text = (key: string) =>
    typeof body[key] === "string" ? body[key].trim() : "";
  const detail =
    kind === "issues"
      ? [
          text("source"),
          [text("project"), text("key")].filter(Boolean).join("/"),
          text("title"),
        ]
          .filter(Boolean)
          .join(" — ")
      : [
          [
            text("name"),
            text("launchpad_handle") ? `@${text("launchpad_handle")}` : "",
          ]
            .filter(Boolean)
            .join(" "),
          text("email"),
        ]
          .filter(Boolean)
          .join(" — ");
  return detail ? `#${id} ${detail}` : unavailable(id);
}

interface PendingLabel {
  controller: AbortController;
  consumers: Set<AbortSignal>;
  result: Promise<string | undefined>;
}

/** In-memory detail lookups only: never suggestions, persistence or filter identity.
 * Each consumer can cancel independently; the last cancellation aborts the request.
 * Completed failures are cached too, so permission failures cannot retry/toast-loop. */
export class SearchFilterLabelCache {
  private labels = new Map<string, string>();
  private pending = new Map<string, PendingLabel>();

  peek(kind: IdFilterKey, id: number): string | undefined {
    return this.labels.get(idLabelKey(kind, id));
  }

  prime(kind: IdFilterKey, id: number, label: string): void {
    const key = idLabelKey(kind, id);
    // A lookup result is already a detail response. Do not fetch it again.
    const pending = this.pending.get(key);
    pending?.controller.abort();
    this.pending.delete(key);
    const oldest = this.labels.keys().next().value;
    if (this.labels.size >= 500 && oldest !== undefined)
      this.labels.delete(oldest);
    this.labels.set(key, label);
  }

  clear(): void {
    for (const request of this.pending.values()) request.controller.abort();
    this.pending.clear();
    this.labels.clear();
  }

  async load(
    kind: IdFilterKey,
    id: number,
    signal: AbortSignal,
  ): Promise<string | undefined> {
    if (signal.aborted) return undefined;
    const key = idLabelKey(kind, id);
    const cached = this.labels.get(key);
    if (cached !== undefined) return cached;
    let request = this.pending.get(key);
    if (!request) {
      const controller = new AbortController();
      const entry: PendingLabel = {
        controller,
        consumers: new Set(),
        result: Promise.resolve(undefined),
      };
      this.pending.set(key, entry);
      entry.result = this.fetchLabel(kind, id, controller.signal).then(
        (label) => {
          if (controller.signal.aborted || this.pending.get(key) !== entry)
            return undefined;
          this.pending.delete(key);
          // Bound a long browser session without persisting private labels.
          const oldest = this.labels.keys().next().value;
          if (this.labels.size >= 500 && oldest !== undefined)
            this.labels.delete(oldest);
          this.labels.set(key, label);
          return label;
        },
      );
      request = entry;
    }
    const entry = request;
    entry.consumers.add(signal);
    const cancel = () => {
      entry.consumers.delete(signal);
      if (!entry.consumers.size && this.pending.get(key) === entry) {
        this.pending.delete(key);
        entry.controller.abort();
      }
    };
    signal.addEventListener("abort", cancel, { once: true });
    try {
      const label = await entry.result;
      // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- AbortSignal can change while awaiting the response/body.
      return signal.aborted ? undefined : label;
    } finally {
      signal.removeEventListener("abort", cancel);
      entry.consumers.delete(signal);
    }
  }

  private async fetchLabel(
    kind: IdFilterKey,
    id: number,
    signal: AbortSignal,
  ): Promise<string> {
    try {
      const res = await fetchApi(
        `${kind === "issues" ? "issues" : "users"}/${id}`,
        { signal },
      );
      if (!res.ok) return unavailable(id);
      const body: unknown = await res.json();
      if (
        !body ||
        typeof body !== "object" ||
        !("id" in body) ||
        body.id !== id
      )
        return unavailable(id);
      return formatIdLabel(kind, id, body);
    } catch {
      return unavailable(id);
    }
  }
}

let sessionScope = "";
const sessionCache = new SearchFilterLabelCache();

/** Re-evaluated reactively by the editor, invalidating labels on login/logout,
 * permission/profile or API-root changes. No extra /me calls or authorization claims. */
export function searchFilterLabelCache(): SearchFilterLabelCache {
  const scope = `${getApiRoot()}:${JSON.stringify(userStore.current)}`;
  if (scope !== sessionScope) {
    sessionCache.clear();
    sessionScope = scope;
  }
  return sessionCache;
}
