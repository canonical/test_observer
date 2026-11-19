// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

/** @typedef {{ signal?: AbortSignal }} RequestOptions */
/** @typedef {{ path: string; options: RequestOptions }} TestRequest */
/** @typedef {(path: string, options: RequestOptions) => Promise<unknown>} ApiHandler */

/** @type {TestRequest[]} */
export const requests = [];
/** @type {ApiHandler} */
let handler = () => Promise.resolve(null);

/** @param {ApiHandler} next */
export function setHandler(next) {
  handler = next;
}

export function resetApi() {
  requests.length = 0;
  handler = () => Promise.resolve(null);
}

/**
 * @param {string} path
 * @param {RequestOptions} [options]
 * @returns {Promise<unknown>}
 */
export function silentApi(path, options = {}) {
  requests.push({ path, options });
  return handler(path, options);
}
