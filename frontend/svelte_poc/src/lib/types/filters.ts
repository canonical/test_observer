import type { Artefact, Family } from './index';

export type FilterKey =
  | 'Assignee' | 'Status' | 'Due date' | 'Risk'
  | 'Series' | 'Pocket' | 'OS type' | 'Release' | 'Owner';

export interface FilterDefinition {
  key: FilterKey;
  extract: (a: Artefact) => string;
}

export const FAMILY_FILTERS: Record<Family, FilterDefinition[]> = {
  snaps: [
    { key: 'Assignee', extract: (a) => a.assignee?.name ?? 'Unassigned' },
    { key: 'Status', extract: (a) => a.status },
    { key: 'Due date', extract: (a) => dueDateCategory(a.due_date) },
    { key: 'Risk', extract: (a) => a.stage },
  ],
  debs: [
    { key: 'Assignee', extract: (a) => a.assignee?.name ?? 'Unassigned' },
    { key: 'Status', extract: (a) => a.status },
    { key: 'Due date', extract: (a) => dueDateCategory(a.due_date) },
    { key: 'Series', extract: (a) => a.series },
    { key: 'Pocket', extract: (a) => a.stage },
  ],
  charms: [
    { key: 'Assignee', extract: (a) => a.assignee?.name ?? 'Unassigned' },
    { key: 'Status', extract: (a) => a.status },
    { key: 'Due date', extract: (a) => dueDateCategory(a.due_date) },
    { key: 'Risk', extract: (a) => a.stage },
  ],
  images: [
    { key: 'OS type', extract: (a) => a.os },
    { key: 'Release', extract: (a) => a.release },
    { key: 'Owner', extract: (a) => a.owner },
    { key: 'Assignee', extract: (a) => a.assignee?.name ?? 'Unassigned' },
    { key: 'Status', extract: (a) => a.status },
    { key: 'Due date', extract: (a) => dueDateCategory(a.due_date) },
  ],
};

function dueDateCategory(dueDate: string | null): string {
  if (!dueDate) return 'No due date';
  const due = new Date(dueDate);
  const now = new Date();
  if (due < now) return 'Overdue';
  const diffDays = (due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);
  if (diffDays < 7) return 'Within a week';
  return 'More than a week';
}
