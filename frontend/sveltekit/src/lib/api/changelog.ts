// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0
import { silentApi } from "$lib/api/client";
import type { Artefact } from "$lib/types";
import type {
  ArtefactBuildEnvironmentReviewResponse,
  AuditDetailResponse,
  AuditHistoryResponse,
} from "$lib/types/openapi";
import { auditPath, PAGE_SIZE } from "$lib/utils/changelog";

async function matchesArtefact(
  id: number,
  family: string,
  review: number | undefined,
  request: typeof silentApi,
): Promise<boolean> {
  const artefact = await request<Artefact>(`/artefacts/${id}`);
  if (artefact?.family !== family) return false;
  if (review !== undefined) {
    const reviews = await request<ArtefactBuildEnvironmentReviewResponse[]>(
      `/artefacts/${id}/environment-reviews`,
    );
    if (!reviews?.some((item) => item.id === review)) return false;
  }
  return true;
}

export async function fetchChangelog(
  id: number,
  family: string,
  review: number | undefined,
  offset: number,
  request = silentApi,
): Promise<AuditHistoryResponse | null> {
  if (!(await matchesArtefact(id, family, review, request))) return null;
  const result = await request<AuditHistoryResponse>(
    `/audit/${auditPath(id, review)}?limit=${PAGE_SIZE}&offset=${offset}`,
  );
  if (!result) throw new Error("Missing audit response");
  return result;
}

export async function fetchChangelogEntry(
  id: number,
  family: string,
  review: number | undefined,
  auditId: number,
  request = silentApi,
): Promise<AuditDetailResponse | null> {
  if (!(await matchesArtefact(id, family, review, request))) return null;
  const result = await request<AuditDetailResponse>(
    `/audit/${auditPath(id, review)}/${auditId}`,
  );
  if (!result) throw new Error("Missing audit response");
  return result;
}
