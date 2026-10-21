// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { userStore } from "$lib/stores/user.svelte";
import type { Capability } from "$lib/testResultsBulk";

export type BulkPermissionAction =
  | "issueAttachment"
  | "rerun"
  | "attachmentRule"
  | "createIssue"
  | "lookupIssue";
export interface BulkPermissions {
  /** Recheck after opening a dialog AND before submission. This gate is revoked
   * on cancellation or any subsequent session refresh, not a durable token. */
  check(action: BulkPermissionAction, bulk?: boolean): Capability<true>;
}

/** /me team permissions are GLOBAL (backend has_general_permission), including
 * reruns. AMR-only grants and server IGNORE_PERMISSIONS configuration are not
 * exposed by /me and cannot safely be inferred by this client. Server remains
 * final authority; later transport must handle 401/403 without automatic retry. */
export async function refreshBulkPermissions(
  fetch: typeof globalThis.fetch,
  signal?: AbortSignal,
): Promise<BulkPermissions> {
  const pending = userStore.refresh(fetch, signal);
  const version = userStore.authorizationVersion;
  const status = await pending;
  return Object.freeze({
    check(action: BulkPermissionAction, bulk = true): Capability<true> {
      if (
        signal?.aborted ||
        version !== userStore.authorizationVersion ||
        status === "unknown"
      )
        return {
          ok: false,
          reason:
            "Session authorization is unknown, cancelled or superseded. Refresh permissions and try again.",
        };
      if (status !== "authenticated" || !userStore.current)
        return { ok: false, reason: "Log in again before using this action." };
      const user = userStore.current;
      if (user.is_admin && userStore.isConfirmedAdmin)
        return { ok: true, value: true };
      const required: string[] = [];
      switch (action) {
        case "issueAttachment":
          required.push("change_issue_attachment");
          if (bulk) required.push("change_issue_attachment_bulk");
          break;
        case "rerun":
          required.push("change_rerun");
          if (bulk) required.push("change_rerun_bulk");
          break;
        case "attachmentRule":
          required.push("change_attachment_rule");
          break;
        case "createIssue":
          required.push("change_issue");
          break;
        case "lookupIssue":
          required.push("view_issue");
          break;
        default:
          return { ok: false, reason: "Unknown action permission." };
      }
      const granted = Array.isArray(user.teams)
        ? user.teams.flatMap((team) =>
            Array.isArray(team.permissions) ? team.permissions : [],
          )
        : [];
      const missing = required.filter(
        (permission) => !granted.includes(permission),
      );
      return missing.length
        ? {
            ok: false,
            reason: `Missing confirmed global permission: ${missing.join(", ")}. Artefact-matching-rule-only grants are not exposed by this session API and cannot be inferred.`,
          }
        : { ok: true, value: true };
    },
  });
}
