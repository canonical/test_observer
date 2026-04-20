import { base } from '$app/paths';

export interface NavTab {
  href: string;
  label: string;
}

export const configuredTabs: NavTab[] = [
  { href: `${base}/snaps`, label: 'Snap Testing' },
  { href: `${base}/debs`, label: 'Deb Testing' },
  { href: `${base}/charms`, label: 'Charm Testing' },
  { href: `${base}/images`, label: 'Image Testing' },
];

export const helpLinks = [
  { label: 'Docs', href: 'https://canonical-test-observer.readthedocs-hosted.com/en/latest/' },
  { label: 'Feedback', href: 'https://github.com/canonical/test_observer/issues' },
  { label: 'Source Code', href: 'https://github.com/canonical/test_observer' },
] as const;

export const spacing = {
  level1: '2px',
  level2: '4px',
  level3: '8px',
  level4: '16px',
  level5: '32px',
  level6: '64px',
  pageHorizontalPadding: '32px',
  maxPageContentWidth: '1800px',
} as const;
