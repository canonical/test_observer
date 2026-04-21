export interface User {
  id: number;
  email: string;
  name: string;
  launchpad_handle: string | null;
}

export const FAMILIES = ['snaps', 'debs', 'charms', 'images'] as const;
export type Family = (typeof FAMILIES)[number];

export const FAMILY_TO_API: Record<Family, string> = {
  snaps: 'snap',
  debs: 'deb',
  charms: 'charm',
  images: 'image',
};

export const FAMILY_STAGES: Record<Family, readonly string[]> = {
  snaps: ['edge', 'beta', 'candidate', 'stable'],
  debs: ['proposed', 'updates', ''],
  charms: ['edge', 'beta', 'candidate', 'stable'],
  images: ['pending', 'current'],
};

export const FAMILY_TITLES: Record<Family, string> = {
  snaps: 'Snap Update Verification',
  debs: 'Deb Update Verification',
  charms: 'Charm Update Verification',
  images: 'Image Update Verification',
};

export type ArtefactStatus = 'APPROVED' | 'MARKED_AS_FAILED' | 'UNDECIDED';
export type ViewMode = 'dashboard' | 'list';

export interface Assignee {
  id: number;
  name: string;
  email: string;
  launchpad_handle: string | null;
}

export interface Artefact {
  id: number;
  name: string;
  version: string;
  track: string;
  store: string;
  branch: string;
  series: string;
  repo: string;
  source: string;
  os: string;
  release: string;
  owner: string;
  sha256: string;
  image_url: string;
  stage: string;
  family: string;
  status: ArtefactStatus;
  comment: string;
  archived: boolean;
  assignee: Assignee | null;
  due_date: string | null;
  created_at: string;
  bug_link: string;
  all_environment_reviews_count: number;
  completed_environment_reviews_count: number;
}

export const STATUS_COLORS: Record<ArtefactStatus, string> = {
  APPROVED: '#0e8420',
  MARKED_AS_FAILED: '#c7162b',
  UNDECIDED: '#666',
};

export const STATUS_LABELS: Record<ArtefactStatus, string> = {
  APPROVED: 'Approved',
  MARKED_AS_FAILED: 'Rejected',
  UNDECIDED: 'Undecided',
};

export function formatDueDate(isoDate: string | null): string | null {
  if (!isoDate) return null;
  const d = new Date(isoDate);
  const month = d.toLocaleString('en-US', { month: 'long' });
  return `${month} ${d.getDate()}`;
}

export function stageDisplayName(stage: string): string {
  if (stage === '') return 'PPAs';
  return stage.charAt(0).toUpperCase() + stage.slice(1);
}

export function userInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }
  return (parts[0]?.[0] ?? '').toUpperCase();
}
