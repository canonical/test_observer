// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

/**
 * Format an ISO timestamp as UTC `YYYY-MM-DD HH:mm:ss`.
 *
 * UTC accessors avoid environment-locale and local-timezone differences. The
 * grid intentionally displays second precision even when the API timestamp has
 * fractional seconds. Invalid input is preserved rather than rendered as the
 * implementation-dependent string "Invalid Date".
 *
 * @param {string} value
 * @returns {string}
 */
export function formatUtcDateTime(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  /** @param {number} part @param {number} [length] */
  const pad = (part, length = 2) => String(part).padStart(length, "0");
  return `${pad(date.getUTCFullYear(), 4)}-${pad(date.getUTCMonth() + 1)}-${pad(date.getUTCDate())} ${pad(date.getUTCHours())}:${pad(date.getUTCMinutes())}:${pad(date.getUTCSeconds())}`;
}
