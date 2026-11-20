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

import 'dart:async';

import 'package:mocktail/mocktail.dart';
import 'package:test/test.dart';
import 'package:testcase_dashboard/models/family.dart';
import 'package:testcase_dashboard/models/issue.dart';
import 'package:testcase_dashboard/providers/api.dart';
import 'package:testcase_dashboard/providers/families.dart';
import 'package:testcase_dashboard/providers/issues_filters.dart';
import 'package:testcase_dashboard/repositories/api_repository.dart';

import '../utilities.dart';

void main() {
  test('family URL selections survive loading and errors until data arrives',
      () async {
    var pending = Completer<List<Family>>();
    final api = ApiRepositoryMock();
    final container = createContainer(
      overrides: [
        apiProvider.overrideWith((ref) => api),
        familiesProvider.overrideWith((ref) => pending.future),
      ],
    );
    final provider = issuesFiltersProvider(
      Uri.parse('/issues?family=alpha&family=unknown'),
    );
    final subscription = container.listen(provider, (_, __) {});

    expect(subscription.read().selectedFamilies, {'alpha', 'unknown'});
    expect(subscription.read().possibleFamilies, isEmpty);

    pending.completeError(StateError('unavailable'));
    await container.read(familiesProvider.future).catchError((_) => <Family>[]);
    expect(subscription.read().selectedFamilies, {'alpha', 'unknown'});

    pending = Completer<List<Family>>();
    container.invalidate(familiesProvider);
    await container.pump();
    expect(subscription.read().selectedFamilies, {'alpha', 'unknown'});

    pending.complete([const Family(name: 'alpha'), const Family(name: 'beta')]);
    await container.read(familiesProvider.future);
    await container.pump();
    expect(subscription.read().possibleFamilies, {'alpha', 'beta'});
    expect(subscription.read().selectedFamilies, {'alpha'});

    pending = Completer<List<Family>>();
    container.invalidate(familiesProvider);
    await container.pump();
    expect(subscription.read().selectedFamilies, {'alpha', 'unknown'});
    pending.complete([]);
    await container.read(familiesProvider.future);
    await container.pump();
    expect(subscription.read().possibleFamilies, isEmpty);
    expect(subscription.read().selectedFamilies, isEmpty);
  });
}

class ApiRepositoryMock extends Mock implements ApiRepository {
  @override
  Future<List<Issue>> getIssues({
    String? source,
    String? project,
    List<IssueStatus>? statuses,
    List<String>? families,
    int? limit,
    int? offset,
    String? q,
  }) async =>
      [];
}
