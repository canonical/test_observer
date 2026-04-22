import type { Artefact, Family } from './index';

export type FilterKey =
  | 'Reviewers' | 'Status' | 'Due date' | 'Risk'
  | 'Series' | 'Pocket' | 'OS type' | 'Release' | 'Owner';

export interface FilterDefinition {
  key: FilterKey;
  extract: (a: Artefact) => string;
}

function reviewersFilterValue(reviewers: { name: string }[] | undefined | null): string {
  if (!reviewers || reviewers.length === 0) return 'Unassigned';
  if (reviewers.length === 1) return reviewers[0].name;
  return `${reviewers.length} reviewers`;
}

export const FAMILY_FILTERS: Record<Family, FilterDefinition[]> = {
  snaps: [
    { key: 'Reviewers', extract: (a) => reviewersFilterValue(a.reviewers) },
    { key: 'Status', extract: (a) => a.status },
    { key: 'Due date', extract: (a) => dueDateCategory(a.due_date) },
    { key: 'Risk', extract: (a) => a.stage },
  ],
  debs: [
    { key: 'Reviewers', extract: (a) => reviewersFilterValue(a.reviewers) },
    { key: 'Status', extract: (a) => a.status },
    { key: 'Due date', extract: (a) => dueDateCategory(a.due_date) },
    { key: 'Series', extract: (a) => a.series },
    { key: 'Pocket', extract: (a) => a.stage },
  ],
  charms: [
    { key: 'Reviewers', extract: (a) => reviewersFilterValue(a.reviewers) },
    { key: 'Status', extract: (a) => a.status },
    { key: 'Due date', extract: (a) => dueDateCategory(a.due_date) },
    { key: 'Risk', extract: (a) => a.stage },
  ],
  images: [
    { key: 'OS type', extract: (a) => a.os },
    { key: 'Release', extract: (a) => a.release },
    { key: 'Owner', extract: (a) => a.owner },
    { key: 'Reviewers', extract: (a) => reviewersFilterValue(a.reviewers) },
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
