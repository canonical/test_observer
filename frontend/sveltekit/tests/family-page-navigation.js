// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

export let retryCount = 0;

export function invalidateAll() {
  retryCount++;
  return Promise.resolve();
}

export function resetRetries() {
  retryCount = 0;
}

/** @param {string} path */
export function goto(path) {
  window.history.pushState({}, "", path);
  return Promise.resolve();
}
