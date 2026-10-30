// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { mount, unmount, flushSync } from "svelte";
import Disclosure from "./attachment-rule-attention.fixture.svelte";

/** @param {HTMLElement} target
 * @param {{ target: object | null; ready: boolean }} attention */
export function mountDisclosure(target, attention) {
  // Match the route's derived event identity, without deep-proxying each new
  // options wrapper into a different target object.
  let value = $state.raw(attention);
  const props = {
    get attention() {
      return value;
    },
  };
  const component = mount(Disclosure, { target, props });
  flushSync();
  return {
    update: (/** @type {typeof attention} */ next) => {
      value = next;
      flushSync();
    },
    destroy: () => unmount(component),
  };
}
