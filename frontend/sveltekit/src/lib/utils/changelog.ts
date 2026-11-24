// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

export const PAGE_SIZE = 50;

export function pageOffset(value: string | null): number {
  if (!value || !/^[1-9]\d*$/.test(value)) return 0;
  const page = Number(value);
  const offset = (page - 1) * PAGE_SIZE;
  return Number.isSafeInteger(offset) ? offset : 0;
}

export function operationLabel(operation: string): string {
  return (
    ({ I: "Created", U: "Updated", D: "Deleted" } as Record<string, string>)[
      operation
    ] ?? operation
  );
}

export function pageHref(url: string, page: number): string {
  const next = new URL(url);
  if (page <= 1) next.searchParams.delete("page");
  else next.searchParams.set("page", String(page));
  return `${next.pathname}${next.search}${next.hash}`;
}
