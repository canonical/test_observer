// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { apiFetch } from "./client.js";
import type { Team } from "$lib/types/team.js";

export function getTeams(
  fetchFn: typeof fetch = fetch,
): Promise<Team[]> {
  return apiFetch<Team[]>("/v1/teams", {}, fetchFn);
}

export function createTeam(
  data: Record<string, unknown>,
  fetchFn: typeof fetch = fetch,
): Promise<Team> {
  return apiFetch<Team>("/v1/teams", {
    method: "POST",
    body: JSON.stringify(data),
  }, fetchFn);
}

export function getTeam(
  id: number,
  fetchFn: typeof fetch = fetch,
): Promise<Team> {
  return apiFetch<Team>(`/v1/teams/${id}`, {}, fetchFn);
}

export function patchTeam(
  id: number,
  patch: Record<string, unknown>,
  fetchFn: typeof fetch = fetch,
): Promise<Team> {
  return apiFetch<Team>(`/v1/teams/${id}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  }, fetchFn);
}
