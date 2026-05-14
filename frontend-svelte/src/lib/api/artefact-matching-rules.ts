// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { apiFetch } from "./client.js";
import type { ArtefactMatchingRule, ArtefactMatchingRulePatch } from "$lib/types/artefact-matching-rule.js";

export function getArtefactMatchingRules(
  fetchFn: typeof fetch = fetch,
): Promise<ArtefactMatchingRule[]> {
  return apiFetch<ArtefactMatchingRule[]>("/v1/artefact-matching-rules", {}, fetchFn);
}

export function createArtefactMatchingRule(
  data: Record<string, unknown>,
  fetchFn: typeof fetch = fetch,
): Promise<ArtefactMatchingRule> {
  return apiFetch<ArtefactMatchingRule>("/v1/artefact-matching-rules", {
    method: "POST",
    body: JSON.stringify(data),
  }, fetchFn);
}

export function patchArtefactMatchingRule(
  id: number,
  patch: ArtefactMatchingRulePatch,
  fetchFn: typeof fetch = fetch,
): Promise<ArtefactMatchingRule> {
  return apiFetch<ArtefactMatchingRule>(`/v1/artefact-matching-rules/${id}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  }, fetchFn);
}

export function deleteArtefactMatchingRule(
  id: number,
  fetchFn: typeof fetch = fetch,
): Promise<void> {
  return apiFetch<void>(`/v1/artefact-matching-rules/${id}`, {
    method: "DELETE",
  }, fetchFn);
}
