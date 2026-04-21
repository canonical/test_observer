import { browser } from '$app/environment';
import type { ViewMode } from '$lib/types';

const STORAGE_KEY = 'test-observer-view-mode';

class ViewModeStore {
  mode = $state<ViewMode>(this.load());

  private load(): ViewMode {
    if (!browser) return 'dashboard';
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === 'list' ? 'list' : 'dashboard';
  }

  set(value: ViewMode) {
    this.mode = value;
    if (browser) {
      localStorage.setItem(STORAGE_KEY, this.mode);
    }
  }
}

export const viewModeStore = new ViewModeStore();
