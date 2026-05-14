// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { User } from "$lib/types/user.js";

let currentUser: User | null = $state(null);
const isAuthenticated: boolean = $derived(currentUser !== null);

export function getUser(): User | null {
  return currentUser;
}

export function setUser(user: User | null): void {
  currentUser = user;
}

export function getIsAuthenticated(): boolean {
  return isAuthenticated;
}
