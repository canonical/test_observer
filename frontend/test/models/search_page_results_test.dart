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

import 'package:flutter_test/flutter_test.dart';
import 'package:testcase_dashboard/models/search_page_results.dart';

import '../search_page_test_data.dart';

void main() {
  test('decodes compact Search table row fields including category', () {
    final json = searchPageRowJson();
    json['test_result']['io_log'] = 'must not be part of the table model';
    json['test_result']['comment'] = 'must not be part of the table model';

    final response = SearchPageTableResponse.fromJson({
      'count': 42,
      'limit': 100,
      'offset': 0,
      'rows': [json],
    });

    expect(response.count, 42);
    expect(response.rows.single.testResult.category, 'smoke');
    expect(response.rows.single.testResult.status.name, 'Failed');
    expect(response.rows.single.testExecution.id, 12);
    expect(response.rows.single.testExecution.environment.name, 'jammy-amd64');
    expect(response.rows.single.artefact.name, 'example-app');
    expect(response.rows.single.artefactBuild.architecture, 'amd64');
  });

  test('decodes single-result modal data and issue tracker URL', () {
    final details = SearchPageDetailsResponse.fromJson(searchPageDetailsJson());

    expect(details.testResult.ioLog, 'one selected result log');
    expect(details.testResult.category, 'smoke');
    expect(details.testExecution.createdAt, DateTime.utc(2025, 1, 2, 3, 4, 5));
    expect(
      details.testExecution.executionMetadata.data,
      {
        'architecture': {'amd64'}
      },
    );
    expect(
      details.testResult.issues.single.url,
      'https://github.com/org/repo/issues/8',
    );
    expect(details.testResult.issues.single.source.name, 'github');
    expect(details.artefact.family.name, 'snap');
  });
}
