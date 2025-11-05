// Copyright (C) 2023 Canonical Ltd.
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

/**
 * Mock data for testing the frontend without a backend
 * To enable mock data mode, add ?mock=true to the URL
 */

export const MOCK_ARTEFACTS = [
  {
    id: 1,
    name: 'firefox',
    version: '123.0',
    track: 'latest',
    store: 'ubuntu-core',
    series: '22',
    repo: null,
    stage: 'beta',
    status: 'APPROVED',
    bug_link: '',
    due_date: new Date(Date.now() + 86400000 * 7).toISOString(),
    all_environment_reviews_count: 5,
    completed_environment_reviews_count: 5,
    assignee: null
  },
  {
    id: 2,
    name: 'chromium',
    version: '120.0.1',
    track: 'latest',
    store: 'ubuntu-core',
    series: '22',
    repo: null,
    stage: 'candidate',
    status: 'UNDECIDED',
    bug_link: '',
    due_date: new Date(Date.now() + 86400000 * 3).toISOString(),
    all_environment_reviews_count: 8,
    completed_environment_reviews_count: 6,
    assignee: null
  },
  {
    id: 3,
    name: 'thunderbird',
    version: '115.5.0',
    track: 'latest',
    store: 'ubuntu-core',
    series: '22',
    repo: null,
    stage: 'stable',
    status: 'APPROVED',
    bug_link: '',
    due_date: new Date(Date.now() - 86400000 * 2).toISOString(),
    all_environment_reviews_count: 4,
    completed_environment_reviews_count: 4,
    assignee: null
  },
  {
    id: 4,
    name: 'vlc',
    version: '3.0.20',
    track: 'latest',
    store: 'ubuntu-core',
    series: '22',
    repo: null,
    stage: 'edge',
    status: 'UNDECIDED',
    bug_link: '',
    due_date: new Date(Date.now() + 86400000 * 1).toISOString(),
    all_environment_reviews_count: 3,
    completed_environment_reviews_count: 1,
    assignee: null
  }
];

export const MOCK_ARTEFACT_BUILDS = [
  {
    id: 1,
    artefact_id: 1,
    architecture: 'amd64',
    revision: 1234
  },
  {
    id: 2,
    artefact_id: 1,
    architecture: 'arm64',
    revision: 1235
  }
];

export const MOCK_TEST_EXECUTIONS = [
  {
    id: 1,
    artefact_build_id: 1,
    environment: {
      id: 1,
      name: 'Desktop AMD64',
      architecture: 'amd64'
    },
    ci_link: 'https://jenkins.example.com/job/test/123',
    c3_link: null,
    status: 'PASSED',
    review_decision: ['APPROVED'],
    review_comment: ['Tests passed successfully'],
    test_plan: 'snap-functional',
    created_at: new Date(Date.now() - 86400000).toISOString(),
    updated_at: new Date(Date.now() - 3600000).toISOString()
  },
  {
    id: 2,
    artefact_build_id: 2,
    environment: {
      id: 2,
      name: 'Desktop ARM64',
      architecture: 'arm64'
    },
    ci_link: 'https://jenkins.example.com/job/test/124',
    c3_link: null,
    status: 'FAILED',
    review_decision: ['UNDECIDED'],
    review_comment: [],
    test_plan: 'snap-functional',
    created_at: new Date(Date.now() - 86400000).toISOString(),
    updated_at: new Date(Date.now() - 3600000).toISOString()
  }
];

export const MOCK_TEST_RESULTS = {
  count: 2,
  test_results: [
    {
      test_result: {
        id: 1,
        name: 'test_basic_functionality',
        status: 'PASSED',
        comment: null,
        io_log: 'Test passed with no issues',
        created_at: new Date(Date.now() - 3600000).toISOString(),
        updated_at: new Date(Date.now() - 3600000).toISOString()
      },
      test_execution: {
        id: 1,
        status: 'PASSED',
        environment: {
          id: 1,
          name: 'Desktop AMD64',
          architecture: 'amd64'
        },
        ci_link: 'https://jenkins.example.com/job/test/123',
        test_plan: 'snap-functional'
      },
      artefact: {
        id: 1,
        name: 'firefox',
        version: '123.0',
        track: 'latest',
        stage: 'beta',
        status: 'APPROVED'
      },
      artefact_build: {
        id: 1,
        architecture: 'amd64',
        revision: 1234
      }
    },
    {
      test_result: {
        id: 2,
        name: 'test_performance',
        status: 'FAILED',
        comment: 'Performance degradation detected',
        io_log: 'ERROR: Test failed - performance below threshold',
        created_at: new Date(Date.now() - 3600000).toISOString(),
        updated_at: new Date(Date.now() - 3600000).toISOString()
      },
      test_execution: {
        id: 2,
        status: 'FAILED',
        environment: {
          id: 2,
          name: 'Desktop ARM64',
          architecture: 'arm64'
        },
        ci_link: 'https://jenkins.example.com/job/test/124',
        test_plan: 'snap-functional'
      },
      artefact: {
        id: 1,
        name: 'firefox',
        version: '123.0',
        track: 'latest',
        stage: 'beta',
        status: 'UNDECIDED'
      },
      artefact_build: {
        id: 2,
        architecture: 'arm64',
        revision: 1235
      }
    }
  ]
};

export const MOCK_ISSUES = {
  issues: [
    {
      id: 1,
      source: 'github',
      project: 'canonical/test_observer',
      key: '#123',
      title: 'Performance issue in Firefox',
      status: 'open',
      url: 'https://github.com/canonical/test_observer/issues/123',
      attachment_rules: [
        {
          id: 1,
          issue_id: 1,
          test_name: 'test_performance',
          template_id: ''
        }
      ]
    },
    {
      id: 2,
      source: 'launchpad',
      project: 'snapd',
      key: '#1234567',
      title: 'Snap installation fails on ARM64',
      status: 'open',
      url: 'https://bugs.launchpad.net/snapd/+bug/1234567',
      attachment_rules: []
    }
  ]
};

/**
 * Check if mock mode is enabled
 */
export function isMockMode() {
  const params = new URLSearchParams(window.location.search);
  return params.get('mock') === 'true';
}

/**
 * Get mock data based on the URL pattern
 */
export function getMockData(url) {
  if (!isMockMode()) {
    return null;
  }

  // Match API patterns and return appropriate mock data
  if (url.includes('/v1/artefacts')) {
    if (url.match(/\/artefacts\/\d+\/builds/)) {
      return MOCK_ARTEFACT_BUILDS;
    } else if (url.match(/\/artefacts\/\d+$/)) {
      return MOCK_ARTEFACTS[0];
    } else {
      // Return array directly for getFamilyArtefacts
      return MOCK_ARTEFACTS;
    }
  } else if (url.includes('/v1/test-executions')) {
    if (url.includes('/test-results')) {
      return MOCK_TEST_RESULTS;
    } else {
      return MOCK_TEST_EXECUTIONS;
    }
  } else if (url.includes('/v1/test-results')) {
    return MOCK_TEST_RESULTS;
  } else if (url.includes('/v1/issues')) {
    if (url.match(/\/issues\/\d+$/)) {
      return MOCK_ISSUES.issues[0];
    } else {
      return MOCK_ISSUES;
    }
  }

  return null;
}
