// Copyright 2026 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { errorStore } from "$lib/stores/error.svelte";
import { getApiRoot } from "$lib/config";

const API_VERSION = "v1";

// ---------------------------------------------------------------------------
// API request helpers.
//
// Three layers, each building on the previous:
//   fetchApi   - core: URL + fetch defaults, returns the raw Response.
//   silentApi  - parses success bodies, throws FetchError on failure.
//   api        - catches, logs, and reports failures to the error store.
// ---------------------------------------------------------------------------

/** Thrown by silentApi for any non-success (or unexpected) HTTP status. */
export class FetchError extends Error {
  constructor(
    name: "FetchError" | "UnexpectedFetchError",
    public readonly status: number,
    public readonly res: Response,
  ) {
    super(name);
    this.name = name;
  }
}

/**
 * Core request building block: builds the full URL, applies the common backend
 * request defaults, performs the fetch, and returns the raw Response untouched.
 *
 * Does not interpret the status or body. Errors thrown by fetch (e.g. network
 * failures) are allowed to propagate to the caller.
 */
export function fetchApi(
  path: string,
  options: RequestInit = {},
): Promise<Response> {
  // Strip leading slashes, else we'll accidentally double them up below on the fetch call.
  const cleanPath = path.replace(/^\/+/, "");
  const headers = new Headers({
    "Content-Type": "application/json",
    "X-CSRF-Token": "1",
  });
  // Caller-supplied headers win over the defaults above.
  new Headers(options.headers).forEach((value, key) => {
    headers.set(key, value);
  });

  return fetch(`${getApiRoot()}/${API_VERSION}/${cleanPath}`, {
    ...options,
    credentials: "include",
    headers,
  });
}

/**
 * Calls fetchApi and interprets the response:
 *   - 2xx: returns the parsed JSON body, or null for a 204 No Content.
 *   - 4xx/5xx: throws a FetchError.
 *   - anything else (e.g. unexpected 1xx/3xx): throws an UnexpectedFetchError.
 *
 * Does NOT touch the global error store. Callers are responsible for catching
 * and handling the thrown errors (or use api, which does that for you).
 */
export async function silentApi<T>(
  path: string,
  options: RequestInit = {},
): Promise<T | null> {
  const res = await fetchApi(path, options);

  if (res.ok) {
    if (res.status === 204) {
      // For "No Content" responses.  Probably unlikely, but this seems an
      // appropriate return value.
      return null;
    }
    return (await res.json()) as T;
  }

  const name =
    res.status >= 400 && res.status < 500
      ? "FetchError"
      : "UnexpectedFetchError";
  throw new FetchError(name, res.status, res);
}

/**
 * The go-to helper for backend requests. Calls silentApi and, on failure,
 * pushes a message to the global error store so the UI can surface it.
 *
 * The failure is re-thrown after the UI message is set, so callers still see an
 * exception rather than a misleading null.
 */
export async function api<T>(
  path: string,
  options: RequestInit = {},
  reporting: { ignoreForbidden?: boolean } = {},
): Promise<T | null> {
  try {
    return await silentApi<T>(path, options);
  } catch (err) {
    if (
      (!isFetchError(err) || err.status !== 401) &&
      !(reporting.ignoreForbidden && isFetchError(err) && err.status === 403)
    ) {
      errorStore.set(await extractErrorMessage(err));
    }
    throw err;
  }
}

function isFetchError(err: unknown): err is FetchError {
  return err instanceof FetchError;
}

async function extractErrorMessage(err: unknown): Promise<string> {
  if (isFetchError(err)) {
    try {
      const body: unknown = await err.res.json();
      if (typeof body === "object" && body !== null && "detail" in body) {
        const detail: unknown = body.detail;
        return typeof detail === "string" ? detail : JSON.stringify(detail);
      }
    } catch {
      /* non-JSON error body */
    }
    return `Request failed: ${err.status}`;
  }
  if (err instanceof Error) return err.message;
  return "Network error";
}
