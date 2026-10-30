// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

/** A component-owned, one-operation focus return. The caller owns lifecycle and
 * dataset/navigation validity; this helper remembers intervening focus intent,
 * including a destination that subsequently blurs to body because of inert. */
export class FocusIntent {
  private pending: (() => void) | null = null;

  cancel() {
    this.pending?.();
  }

  begin(source: HTMLElement | null, current: () => boolean) {
    this.cancel();
    const document = source?.ownerDocument;
    let owns = !!source && document?.activeElement === source;
    const cancel = () => {
      owns = false;
      document?.removeEventListener("focusin", onFocus, true);
      if (this.pending === cancel) this.pending = null;
    };
    const onFocus = (event: FocusEvent) => {
      if (
        event.target !== source &&
        event.target !== document?.body &&
        event.target !== document?.documentElement
      )
        cancel();
    };
    this.pending = cancel;
    if (owns) document?.addEventListener("focusin", onFocus, true);

    return {
      cancel,
      restore: (fallback?: () => HTMLElement | null | undefined) => {
        try {
          if (!owns || !document || !current()) return;
          const active = document.activeElement;
          if (
            active !== source &&
            active !== document.body &&
            active !== document.documentElement
          )
            return;
          const available = (element: HTMLElement | null | undefined) =>
            element?.isConnected &&
            !element.closest("[hidden], [inert]") &&
            !element.matches(":disabled");
          const target = available(source) ? source : fallback?.();
          if (available(target)) target?.focus({ preventScroll: true });
        } finally {
          cancel();
        }
      },
    };
  }
}
