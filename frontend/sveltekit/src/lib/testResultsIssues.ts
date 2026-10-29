// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { FetchError, silentApi } from "$lib/api/client";
import { positiveId } from "$lib/testResultsPredicate";
import { formatIdLabel } from "$lib/searchFilterLabels";
import type { BulkTarget, Capability } from "$lib/testResultsBulk";

export type IssueOperation = "attach" | "detach";
export type IssueReviewStatus =
  | "checking"
  | "review"
  | "submitting"
  | "error"
  | "partial"
  | "unknown"
  | "invalidated";
export interface PickedIssue {
  id: number;
  label: string;
}
export type IssueChoice =
  { kind: "existing"; issue: PickedIssue } | { kind: "external"; url: string };
export type IssueReference =
  { kind: "internal"; id: number } | { kind: "external"; url: string };

/** Only supported tracker shapes, or same-origin exact internal routes. Never
 * extract an internal ID from an arbitrary URL's last path segment. The server
 * remains authoritative for its supported tracker parser. */
export function parseIssueReference(
  input: string,
  origin: string,
  base: string,
): Capability<IssueReference> {
  const invalid = {
    ok: false as const,
    reason:
      "Enter one positive issue ID, a same-origin internal issue link, or a supported GitHub, Jira or Launchpad HTTP(S) issue URL.",
  };
  const text = input.trim();
  if (/^#?\d+$/.test(text)) {
    const id = Number(text.replace(/^#/, ""));
    return positiveId(id)
      ? { ok: true, value: { kind: "internal", id } }
      : invalid;
  }
  if (
    !text ||
    /[\s\\%]/.test(text) ||
    text.startsWith("//") ||
    /\/(?:\.|\.\.)(?:\/|$)/.test(text)
  )
    return invalid;
  let url: URL;
  try {
    url = new URL(text, origin);
  } catch {
    return invalid;
  }
  if (!/^https?:$/.test(url.protocol) || url.username || url.password)
    return invalid;
  const root = base.replace(/\/$/, "");
  if (url.origin === origin) {
    if (url.search) return invalid;
    const prefix = `${root}/issues/`;
    const current =
      !url.hash && url.pathname.startsWith(prefix)
        ? url.pathname.slice(prefix.length)
        : null;
    const legacy =
      (url.pathname === "/" || url.pathname === `${root}/`) &&
      /^#\/issues\/\d+$/.test(url.hash)
        ? url.hash.slice("#/issues/".length)
        : null;
    const candidate = current ?? legacy;
    const id = candidate && /^\d+$/.test(candidate) ? Number(candidate) : 0;
    return positiveId(id)
      ? { ok: true, value: { kind: "internal", id } }
      : invalid;
  }
  if (url.port || url.search || url.hash) return invalid;
  let path: string | undefined;
  if (url.hostname === "github.com") {
    const match = /^\/([\w.-]+\/[\w.-]+)\/issues\/(\d+)$/.exec(url.pathname);
    if (match) path = `/${match[1].toLowerCase()}/issues/${match[2]}`;
  } else if (url.hostname === "warthogs.atlassian.net") {
    const match = /^\/browse\/([A-Za-z]+)-(\d+)$/.exec(url.pathname);
    if (match) path = `/browse/${match[1].toUpperCase()}-${match[2]}`;
  } else if (url.hostname === "bugs.launchpad.net") {
    const match = /^\/([\w.-]+)(?:\/\+source\/[\w.-]+)?\/\+bug\/(\d+)$/.exec(
      url.pathname,
    );
    if (match) path = `/${match[1].toLowerCase()}/+bug/${match[2]}`;
  }
  return path
    ? {
        ok: true,
        value: { kind: "external", url: `https://${url.hostname}${path}` },
      }
    : invalid;
}

export function pickedIssue(body: unknown): PickedIssue {
  if (
    !body ||
    typeof body !== "object" ||
    !("id" in body) ||
    !positiveId(body.id)
  )
    throw new Error("The server returned an invalid issue.");
  return {
    id: body.id,
    label: formatIdLabel("issues", body.id, body),
  };
}

/** One bounded search, exact canonical URL equality, no enumeration or fuzzy
 * first-result fallback. An incomplete result set cannot prove uniqueness. */
export async function resolveExistingIssue(
  reference: IssueReference,
  signal: AbortSignal,
): Promise<PickedIssue> {
  if (reference.kind === "internal") {
    const issue = pickedIssue(
      await silentApi(`issues/${reference.id}`, { signal }),
    );
    if (issue.id !== reference.id)
      throw new Error("The server returned a different issue ID.");
    return issue;
  }
  const params = new URLSearchParams({ q: reference.url, limit: "10" });
  const body = await silentApi<{
    issues: Record<string, unknown>[];
    count: number;
  }>(`issues?${params}`, { signal });
  if (
    !body ||
    !Array.isArray(body.issues) ||
    !Number.isSafeInteger(body.count) ||
    body.count < 0
  )
    throw new Error("The server returned an invalid issue search.");
  if (body.count > 10 || body.issues.length !== body.count)
    throw new Error(
      "This bounded search cannot prove a unique existing issue. Select an issue suggestion or enter its internal ID instead.",
    );
  const matches = body.issues.filter((issue) => issue.url === reference.url);
  if (matches.length !== 1)
    throw new Error(
      matches.length
        ? "More than one exact issue matched. Enter an internal issue ID instead."
        : "No exact existing issue matches this URL. Detach never creates an issue; choose an existing issue or internal ID.",
    );
  return pickedIssue(matches[0]);
}

export const bulkTargetCount = (target: BulkTarget) =>
  target.kind === "query" ? target.count : target.resultIds.length;
export const attachmentIsBulk = (target: BulkTarget) =>
  target.kind === "query" || target.resultIds.length > 1;
export const bulkTargetIdentity = (target: BulkTarget) =>
  JSON.stringify(
    target.kind === "query"
      ? [target.kind, target.queryKey, target.filters, target.count]
      : [target.kind, target.queryKey, target.resultIds],
  );

export async function issueRequestError(error: unknown): Promise<string> {
  if (error instanceof FetchError) {
    if (error.status === 401)
      return "Your session expired. Log in again, then refresh permissions.";
    if (error.status === 403)
      return "The server denied this action (403). Your permissions may have changed. Refresh permissions before trying again.";
    try {
      const body: unknown = await error.res.json();
      if (body && typeof body === "object" && "detail" in body)
        return `Request failed (${error.status}): ${typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail)}`;
    } catch {
      /* No JSON error body. */
    }
    return `Request failed (${error.status}).`;
  }
  return error instanceof Error
    ? error.message
    : "Could not complete the request.";
}

export const ambiguousMutationError = (error: unknown) =>
  !(error instanceof FetchError) || error.status >= 500 || error.status < 400;
