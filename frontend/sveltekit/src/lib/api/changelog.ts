// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0
import { silentApi } from "$lib/api/client";
import type { Artefact } from "$lib/types";
import type {
  ArtefactBuildEnvironmentReviewResponse,
  AuditHistoryResponse,
} from "$lib/types/openapi";
import { PAGE_SIZE } from "$lib/utils/changelog";

export async function fetchChangelog(
  id: number,
  family: string,
  review: number | undefined,
  offset: number,
  request = silentApi,
): Promise<AuditHistoryResponse | null> {
  const artefact = await request<Artefact>(`/artefacts/${id}`);
  if (artefact?.family !== family) return null;
  if (review !== undefined) {
    const reviews = await request<ArtefactBuildEnvironmentReviewResponse[]>(
      `/artefacts/${id}/environment-reviews`,
    );
    if (!reviews?.some((item) => item.id === review)) return null;
  }
  const endpoint =
    review === undefined ? `artefacts/${id}` : `environment-reviews/${review}`;
  const result = await request<AuditHistoryResponse>(
    `/audit/${endpoint}?limit=${PAGE_SIZE}&offset=${offset}`,
  );
  if (!result) throw new Error("Missing audit response");
  return result;
}
