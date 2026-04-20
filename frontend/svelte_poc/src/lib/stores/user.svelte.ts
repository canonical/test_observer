import type { User } from '$lib/types';

class UserStore {
  current = $state<User | null>(null);

  get isLoggedIn(): boolean {
    return this.current !== null;
  }

  get initials(): string {
    if (!this.current) return '';
    const parts = this.current.name.split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return (parts[0]?.[0] ?? '').toUpperCase();
  }

  set(user: User | null) {
    this.current = user;
  }
}

export const userStore = new UserStore();
