export interface User {
  id: number;
  email: string;
  name: string;
  launchpad_handle: string | null;
}

export const FAMILIES = ['snaps', 'debs', 'charms', 'images'] as const;
export type Family = (typeof FAMILIES)[number];
