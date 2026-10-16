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

/**
 * Backend API base URL.
 * In development the backend runs on port 30000.
 * This exact string gets replaced by nginx in production by the frontend charm;
 * please do not modify it.
 */
export const API_BASE = "http://localhost:30000/";

/** Returns API_BASE, properly normalized. */
export function getApiRoot(): string {
  return API_BASE.replace(/\/$/, "");
}
