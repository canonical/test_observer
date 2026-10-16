// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { mount, unmount } from "svelte";
import ArtefactInfoSection from "../src/lib/components/artefact/ArtefactInfoSection.svelte";
import ArtefactPage from "../src/routes/[family]/[artefactId]/+page.svelte";

/**
 * @param {import("svelte").MountOptions["target"]} target
 * @param {import("svelte").ComponentProps<typeof ArtefactPage>} props
 */
export function mountArtefactPage(target, props) {
  return mount(ArtefactPage, { target, props });
}

/**
 * @param {import("svelte").MountOptions["target"]} target
 * @param {import("svelte").ComponentProps<typeof ArtefactInfoSection>} props
 */
export function mountCommentEditor(target, props) {
  return mount(ArtefactInfoSection, { target, props });
}

/** @param {Record<string, any>} component */
export function unmountCommentEditor(component) {
  return unmount(component);
}
