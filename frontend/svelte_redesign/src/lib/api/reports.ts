// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:30000";

export async function downloadReport(
  params: Record<string, string>,
  fetchFn: typeof fetch = fetch,
): Promise<Blob> {
  const qs = new URLSearchParams(params).toString();
  const path = qs ? `/v1/reports?${qs}` : "/v1/reports";
  const response = await fetchFn(`${API_BASE}${path}`, {
    credentials: "include",
    headers: { "X-CSRF-Token": "1" },
  });
  if (!response.ok) {
    throw new Error(`Report download failed: ${response.status}`);
  }
  return response.blob();
}
