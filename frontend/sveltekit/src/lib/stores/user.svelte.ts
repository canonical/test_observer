// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import type { User } from '$lib/types';

class UserStore {
  current = $state<User | null>(null);

  get isLoggedIn(): boolean {
    return this.current !== null;
  }

  set(user: User | null) {
    this.current = user;
  }
}

export const userStore = new UserStore();
