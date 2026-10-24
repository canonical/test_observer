// Copyright 2026 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:testcase_dashboard/models/search_page_results.dart';

Map<String, dynamic> searchPageRowJson({int id = 23, int executionId = 12}) => {
  'test_result': {
    'id': id,
    'name': 'suite/case',
    'category': 'smoke',
    'created_at': '2025-01-02T03:04:05Z',
    'template_id': 'template-1',
    'status': 'FAILED',
    'issues': [],
  },
  'test_execution': {
    'id': executionId,
    'status': 'IN_PROGRESS',
    'is_rerun_requested': false,
    'environment': {'name': 'jammy-amd64'},
    'test_plan': 'daily',
    'execution_metadata': {
      'architecture': ['amd64'],
    },
  },
  'artefact': {
    'id': 7,
    'name': 'example-app',
    'version': '1.2.3',
    'track': 'latest',
    'stage': 'stable',
    'family': 'snap',
    'archived': false,
    'reviewers': [],
  },
  'artefact_build': {'architecture': 'amd64'},
};

Map<String, dynamic> searchPageDetailsJson({int id = 23}) => {
  'test_result': {
    'id': id,
    'name': 'suite/case',
    'category': 'smoke',
    'template_id': 'template-1',
    'status': 'FAILED',
    'io_log': 'one selected result log',
    'issues': [
      {
        'issue': {
          'id': 91,
          'source': 'github',
          'project': 'org/repo',
          'key': '8',
          'title': 'Issue title',
          'status': 'open',
          'url': 'https://github.com/org/repo/issues/8',
        },
      },
    ],
  },
  'test_execution': {
    'id': 12,
    'status': 'IN_PROGRESS',
    'environment': {'name': 'jammy-amd64'},
    'test_plan': 'daily',
    'created_at': '2025-01-02T03:04:05Z',
    'execution_metadata': {
      'architecture': ['amd64'],
    },
  },
  'artefact': {
    'id': 7,
    'name': 'example-app',
    'version': '1.2.3',
    'track': 'latest',
    'family': 'snap',
  },
  'artefact_build': {'architecture': 'amd64'},
};

SearchPageTableResponse searchPageResponse({
  required int? count,
  required int offset,
  List<SearchPageTableRow> rows = const [],
}) {
  return SearchPageTableResponse(
    count: count,
    limit: 100,
    offset: offset,
    rows: rows,
  );
}
