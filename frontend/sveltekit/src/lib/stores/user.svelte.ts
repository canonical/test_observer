// Copyright 2026 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { getApiRoot } from "$lib/config";
import type { User } from "$lib/types";

// Result of re-checking the session against the backend. "unknown" means the
// check failed (transport/server error) or was superseded by a newer check,
// so it cannot confirm the login state either way.
export type AuthStatus = "authenticated" | "unauthenticated" | "unknown";

// Single source of truth for client-side login state. Nothing else fetches
// /v1/users/me directly: any code that needs to know (or act on) whether the
// user is logged in calls `refresh()`, so the cached `current` value can never
// drift from the backend. Reading `current` / `isLoggedIn` for rendering is a
// cache read and is fine; code making an authorization decision must call
// `refresh()` and branch on its returned status, not on `current`.
class UserStore {
  current = $state<User | null>(null);
  private sessionConfirmedAdmin = $state(false);
  private refreshGeneration = $state(0);

  /** Authorization gates are invalidated by ANY later refresh, including a
   * failed or cancelled one that leaves the cached display profile intact. */
  get authorizationVersion(): number {
    return this.refreshGeneration;
  }

  get isConfirmedAdmin(): boolean {
    return Boolean(this.sessionConfirmedAdmin && this.current?.is_admin);
  }

  get isLoggedIn(): boolean {
    return this.current !== null;
  }

  hasPermission(permission: string): boolean {
    return (
      this.current !== null &&
      (this.isConfirmedAdmin ||
        this.current.teams.some((team) =>
          team.permissions.includes(permission),
        ))
    );
  }

  // Re-checks the session against the backend, updates the cached user, and
  // returns the confirmed status. On an "unknown" result the cached user is
  // preserved (so a transient failure doesn't falsely log the user out), but
  // callers must not treat that preserved value as proof of an active
  // session — branch on the returned status instead.
  async refresh(
    fetch: typeof globalThis.fetch,
    signal?: AbortSignal,
  ): Promise<AuthStatus> {
    const generation = ++this.refreshGeneration;
    this.sessionConfirmedAdmin = false;
    const result = await fetchMe(fetch, signal);
    // A superseded or cancelled response is not authorization evidence for its
    // caller, even if cancellation happened while the response body was read.
    if (generation !== this.refreshGeneration || signal?.aborted)
      return "unknown";
    if (result.status === "authenticated") {
      this.current = result.user;
      this.sessionConfirmedAdmin = result.user.is_admin;
    } else if (result.status === "unauthenticated") {
      this.current = null;
    }
    // On "unknown", keep the cached profile for display, but the flag stays
    // false so stale admin status cannot expose mutation controls.
    return result.status;
  }
}

type MeResult =
  | { status: "authenticated"; user: User }
  | { status: "unauthenticated" }
  | { status: "unknown" };

const fetchMe = async (
  fetch: typeof globalThis.fetch,
  signal?: AbortSignal,
): Promise<MeResult> => {
  try {
    const response = await fetch(`${getApiRoot()}/v1/users/me`, {
      signal,
      credentials: "include",
      headers: { "X-CSRF-Token": "1" },
    });
    if (response.ok) {
      // With REQUIRE_AUTHENTICATION=false the backend returns 200 with a null
      // body for anonymous requests, so a 2xx alone doesn't mean logged in.
      const user = (await response.json()) as User | null;
      return user
        ? { status: "authenticated", user }
        : { status: "unauthenticated" };
    }
    // /me returns 401/403 for an unauthenticated session (an authenticated
    // user can always read their own profile), so these are the only statuses
    // that definitively mean "logged out". Anything else (5xx, etc.) is an
    // inconclusive failure.
    if (response.status === 401 || response.status === 403) {
      return { status: "unauthenticated" };
    }
    return { status: "unknown" };
  } catch (error) {
    console.error("Error fetching user:", error);
    return { status: "unknown" };
  }
};

export const userStore = new UserStore();
