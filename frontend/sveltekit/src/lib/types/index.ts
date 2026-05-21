// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

export interface User {
  id: number;
  email: string;
  name: string;
  launchpad_handle: string | null;
}

export const FAMILIES = ['snaps', 'debs', 'charms', 'images'] as const;
export type Family = (typeof FAMILIES)[number];

export const FAMILY_TITLES: Record<Family, string> = {
  snaps: 'Snap Testing',
  debs: 'Deb Testing',
  charms: 'Charm Testing',
  images: 'Image Testing',
};
