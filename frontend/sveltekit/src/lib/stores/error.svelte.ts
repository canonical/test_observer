// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

class ErrorStore {
  message = $state<string | null>(null);

  get hasError(): boolean {
    return this.message !== null;
  }

  set(msg: string) {
    this.message = msg;
  }

  clear() {
    this.message = null;
  }
}

export const errorStore = new ErrorStore();
