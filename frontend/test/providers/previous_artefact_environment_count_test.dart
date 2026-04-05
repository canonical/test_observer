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

import 'package:dio/dio.dart';
import 'package:test/test.dart';
import 'package:testcase_dashboard/models/artefact.dart';
import 'package:testcase_dashboard/models/artefact_version.dart';
import 'package:testcase_dashboard/providers/api.dart';
import 'package:testcase_dashboard/providers/previous_artefact_environment_count.dart';
import 'package:testcase_dashboard/repositories/api_repository.dart';

import '../dummy_data.dart';
import '../utilities.dart';

void main() {
  test('it returns environment count from previous artefact version', () async {
    final apiStub = ApiRepositoryStub();
    final container = createContainer(
      overrides: [apiProvider.overrideWith((ref) => apiStub)],
    );

    final count = await container.read(
      previousArtefactEnvironmentCountProvider(3).future,
    );

    expect(count, 90);
    expect(apiStub.getArtefactVersionsCalls, [3]);
    expect(apiStub.getArtefactCalls, [2]);
  });

  test('it returns null when artefact is already the oldest version', () async {
    final apiStub = ApiRepositoryStub();
    final container = createContainer(
      overrides: [apiProvider.overrideWith((ref) => apiStub)],
    );

    final count = await container.read(
      previousArtefactEnvironmentCountProvider(1).future,
    );

    expect(count, isNull);
    expect(apiStub.getArtefactVersionsCalls, [1]);
    expect(apiStub.getArtefactCalls, isEmpty);
  });

  test('it returns null when current artefact is absent in versions list',
      () async {
    final apiStub = ApiRepositoryStub();
    final container = createContainer(
      overrides: [apiProvider.overrideWith((ref) => apiStub)],
    );

    final count = await container.read(
      previousArtefactEnvironmentCountProvider(42).future,
    );

    expect(count, isNull);
    expect(apiStub.getArtefactVersionsCalls, [42]);
    expect(apiStub.getArtefactCalls, isEmpty);
  });
}

class ApiRepositoryStub extends ApiRepository {
  ApiRepositoryStub() : super(dio: Dio());

  final List<int> getArtefactVersionsCalls = [];
  final List<int> getArtefactCalls = [];

  @override
  Future<List<ArtefactVersion>> getArtefactVersions(int artefactId) async {
    getArtefactVersionsCalls.add(artefactId);

    if (artefactId == 42) {
      return const [
        ArtefactVersion(artefactId: 3, version: '2.73'),
        ArtefactVersion(artefactId: 2, version: '2.72'),
      ];
    }

    return const [
      ArtefactVersion(artefactId: 3, version: '2.73'),
      ArtefactVersion(artefactId: 2, version: '2.72'),
      ArtefactVersion(artefactId: 1, version: '2.71'),
    ];
  }

  @override
  Future<Artefact> getArtefact(int artefactId) async {
    getArtefactCalls.add(artefactId);

    if (artefactId == 2) {
      return dummyArtefact.copyWith(
        id: artefactId,
        version: '2.72',
        allEnvironmentReviewsCount: 90,
      );
    }

    return dummyArtefact.copyWith(
      id: artefactId,
      version: '2.73',
      allEnvironmentReviewsCount: 45,
    );
  }
}
