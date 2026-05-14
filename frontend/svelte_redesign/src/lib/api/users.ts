// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { apiFetch } from "./client.js";
import type { User } from "$lib/types/user.js";

export function getCurrentUser(
  fetchFn: typeof fetch = fetch,
): Promise<User | null> {
  return apiFetch<User>("/v1/users/me", {}, fetchFn).catch(() => null);
}

export function getUsers(
  params: Record<string, string>,
  fetchFn: typeof fetch = fetch,
): Promise<User[]> {
  const qs = new URLSearchParams(params).toString();
  const path = qs ? `/v1/users?${qs}` : "/v1/users";
  return apiFetch<User[]>(path, {}, fetchFn);
}

export function getUser(
  id: number,
  fetchFn: typeof fetch = fetch,
): Promise<User> {
  return apiFetch<User>(`/v1/users/${id}`, {}, fetchFn);
}
