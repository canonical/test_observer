// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { apiFetch } from "./client.js";
import type { Artefact, ArtefactHistory, ArtefactSearchResult, ArtefactVersion } from "$lib/types/artefact.js";
import type { ArtefactBuild } from "$lib/types/build.js";
import type { EnvironmentReview } from "$lib/types/environment.js";

export function getArtefacts(
  family: string,
  fetchFn: typeof fetch = fetch,
): Promise<Artefact[]> {
  return apiFetch<Artefact[]>(`/v1/artefacts?family=${encodeURIComponent(family)}`, {}, fetchFn);
}

export function getArtefact(
  id: number,
  fetchFn: typeof fetch = fetch,
): Promise<Artefact> {
  return apiFetch<Artefact>(`/v1/artefacts/${id}`, {}, fetchFn);
}

export function patchArtefact(
  id: number,
  patch: Partial<Artefact>,
  fetchFn: typeof fetch = fetch,
): Promise<Artefact> {
  return apiFetch<Artefact>(`/v1/artefacts/${id}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  }, fetchFn);
}

export function getArtefactBuilds(
  id: number,
  fetchFn: typeof fetch = fetch,
): Promise<ArtefactBuild[]> {
  return apiFetch<ArtefactBuild[]>(`/v1/artefacts/${id}/builds`, {}, fetchFn);
}

export function getArtefactVersions(
  id: number,
  fetchFn: typeof fetch = fetch,
): Promise<ArtefactVersion[]> {
  return apiFetch<ArtefactVersion[]>(`/v1/artefacts/${id}/versions`, {}, fetchFn);
}

export function getArtefactEnvironmentReviews(
  id: number,
  fetchFn: typeof fetch = fetch,
): Promise<EnvironmentReview[]> {
  return apiFetch<EnvironmentReview[]>(`/v1/artefacts/${id}/environment-reviews`, {}, fetchFn);
}

export function patchEnvironmentReview(
  artefactId: number,
  reviewId: number,
  patch: Partial<EnvironmentReview>,
  fetchFn: typeof fetch = fetch,
): Promise<EnvironmentReview> {
  return apiFetch<EnvironmentReview>(
    `/v1/artefacts/${artefactId}/environment-reviews/${reviewId}`,
    { method: "PATCH", body: JSON.stringify(patch) },
    fetchFn,
  );
}

export function bulkPatchEnvironmentReviews(
  artefactId: number,
  reviews: Partial<EnvironmentReview>[],
  fetchFn: typeof fetch = fetch,
): Promise<EnvironmentReview[]> {
  return apiFetch<EnvironmentReview[]>(
    `/v1/artefacts/${artefactId}/environment-reviews`,
    { method: "PATCH", body: JSON.stringify(reviews) },
    fetchFn,
  );
}

export function searchArtefacts(
  params: Record<string, string>,
  fetchFn: typeof fetch = fetch,
): Promise<ArtefactSearchResult> {
  const qs = new URLSearchParams(params).toString();
  return apiFetch<ArtefactSearchResult>(`/v1/artefacts/search?${qs}`, {}, fetchFn);
}

export function getArtefactHistory(
  params: Record<string, string>,
  fetchFn: typeof fetch = fetch,
): Promise<ArtefactHistory> {
  const qs = new URLSearchParams(params).toString();
  return apiFetch<ArtefactHistory>(`/v1/artefacts/history?${qs}`, {}, fetchFn);
}
