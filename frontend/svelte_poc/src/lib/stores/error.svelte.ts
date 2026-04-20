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
