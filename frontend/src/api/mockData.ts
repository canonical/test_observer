// Copyright (C) 2024 Canonical Ltd.
//
// This file is part of Test Observer Frontend.
//
// Test Observer Frontend is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// Test Observer Frontend is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

import type { Artefact } from '../models/types';

export const mockArtefacts: Artefact[] = [
  {
    id: 1,
    name: 'test-snap',
    version: '1.0.0',
    family: 'snap',
    track: 'latest',
    store: 'ubuntu',
    branch: '',
    series: '',
    repo: '',
    source: '',
    os: '',
    release: '',
    owner: '',
    sha256: '',
    image_url: '',
    status: 'approved',
    comment: 'All tests passed',
    stage: 'stable',
    all_environment_reviews_count: 5,
    completed_environment_reviews_count: 5,
    assignee: {
      id: 1,
      launchpad_email: 'test@canonical.com',
      launchpad_handle: 'testuser',
      name: 'Test User',
    },
    bug_link: '',
  },
  {
    id: 2,
    name: 'ubuntu-desktop',
    version: '22.04.1',
    family: 'snap',
    track: 'latest',
    store: 'ubuntu',
    branch: '',
    series: '',
    repo: '',
    source: '',
    os: '',
    release: '',
    owner: '',
    sha256: '',
    image_url: '',
    status: 'undecided',
    comment: 'Testing in progress',
    stage: 'candidate',
    all_environment_reviews_count: 8,
    completed_environment_reviews_count: 3,
    assignee: {
      id: 2,
      launchpad_email: 'qa@canonical.com',
      launchpad_handle: 'qauser',
      name: 'QA User',
    },
    bug_link: '',
  },
  {
    id: 3,
    name: 'firefox',
    version: '118.0',
    family: 'snap',
    track: 'latest',
    store: 'ubuntu',
    branch: '',
    series: '',
    repo: '',
    source: '',
    os: '',
    release: '',
    owner: '',
    sha256: '',
    image_url: '',
    status: 'marked_as_failed',
    comment: 'Memory leak detected',
    stage: 'beta',
    all_environment_reviews_count: 4,
    completed_environment_reviews_count: 4,
    assignee: {
      id: 3,
      launchpad_email: 'dev@canonical.com',
      launchpad_handle: 'devuser',
      name: 'Dev User',
    },
    bug_link: 'https://bugs.launchpad.net/bugs/123456',
    due_date: '2024-12-31T00:00:00Z',
  },
];
