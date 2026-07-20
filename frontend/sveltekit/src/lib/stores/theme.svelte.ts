// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

export type Theme = 'light' | 'dark' | 'system';

const THEMES: Theme[] = ['light', 'dark', 'system'];
const STORAGE_KEY = 'test-observer-theme';

export const THEME_LABELS: Record<Theme, string> = {
  light: 'Theme: Light',
  dark: 'Theme: Dark',
  system: 'Theme: System',
};

class ThemeStore {
  current = $state<Theme>('system');

  get label(): string {
    return THEME_LABELS[this.current];
  }

  /** Read stored preference from localStorage and apply the class (call once in browser context). */
  init() {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (THEMES.includes(stored as Theme)) {
      this.current = stored as Theme;
    }
    this.#applyClass();
  }

  /** Cycle through light → dark → system → light. */
  cycle() {
    const idx = THEMES.indexOf(this.current);
    this.current = THEMES[(idx + 1) % THEMES.length];
    localStorage.setItem(STORAGE_KEY, this.current);
    this.#applyClass();
  }

  #applyClass() {
    const el = document.documentElement;
    el.classList.remove('light', 'dark');
    if (this.current !== 'system') {
      el.classList.add(this.current);
    }
  }
}

export const themeStore = new ThemeStore();
