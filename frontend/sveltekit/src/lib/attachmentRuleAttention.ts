// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

interface RuleAttention {
  // Identity changes only for a new issue, target or session, not rule updates.
  target: object | null;
  ready: boolean;
}

/** One-shot native disclosure attention, after route/data/DOM readiness.
 * An open dialog owns focus: reveal the rule, but never steal its focus/scroll
 * or queue a surprise focus transfer for when that dialog eventually closes.
 */
export function attachmentRuleAttention(
  node: HTMLDetailsElement,
  initial: RuleAttention,
) {
  let consumed: object | null = null;
  let frame: number | undefined;
  const cancel = () => {
    if (frame !== undefined) cancelAnimationFrame(frame);
    frame = undefined;
  };
  const update = ({ target, ready }: RuleAttention) => {
    cancel();
    if (!target || !ready || consumed === target) return;
    // Let navigation finish removing inert and restoring its focus/scroll, and
    // let the newly loaded keyed disclosure reach the DOM before attention.
    frame = requestAnimationFrame(() => {
      frame = undefined;
      if (!node.isConnected || node.closest("[inert]")) return;
      const summary = node.querySelector("summary");
      if (!summary) return;
      consumed = target;
      node.open = true;
      if (node.ownerDocument.querySelector("dialog[open]")) return;
      summary.focus({ preventScroll: true });
      if (node.ownerDocument.activeElement === summary)
        summary.scrollIntoView({ block: "center", behavior: "instant" });
    });
  };
  update(initial);
  return { update, destroy: cancel };
}
