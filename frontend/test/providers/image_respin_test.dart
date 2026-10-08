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
import 'package:mocktail/mocktail.dart';
import 'package:test/test.dart';
import 'package:testcase_dashboard/models/artefact.dart';
import 'package:testcase_dashboard/models/artefact_build.dart';
import 'package:testcase_dashboard/models/environment.dart';
import 'package:testcase_dashboard/models/family_name.dart';
import 'package:testcase_dashboard/models/test_execution.dart';
import 'package:testcase_dashboard/providers/api.dart';
import 'package:testcase_dashboard/providers/image_respin.dart';
import 'package:testcase_dashboard/repositories/api_repository.dart';

import '../dummy_data.dart';
import '../utilities.dart';

class ApiRepositoryMock extends Mock implements ApiRepository {}

const _cdimage = Environment(
  id: 10,
  name: cdimageEnvironment,
  architecture: 'amd64',
);
const _manualTests = Environment(
  id: 11,
  name: 'user manual tests',
  architecture: 'amd64',
);

Artefact _image(
  int id,
  String name, {
  String os = 'ubuntu',
  String release = 'stonking',
}) =>
    dummyArtefact.copyWith(
      id: id,
      name: name,
      os: os,
      release: release,
      family: 'image',
      version: '20260920',
    );

TestExecution _execution(
  int id, {
  String testPlan = imageBuildTestPlan,
  Environment environment = _cdimage,
  bool isRerunRequested = false,
}) =>
    dummyTestExecution.copyWith(
      id: id,
      testPlan: testPlan,
      environment: environment,
      isRerunRequested: isRerunRequested,
    );

ArtefactBuild _build(int id, List<TestExecution> executions) =>
    dummyArtefactBuild.copyWith(id: id, testExecutions: executions);

ImageRespinTarget _target(int buildId, int testExecutionId) =>
    ImageRespinTarget(
      artefact: _image(buildId, 'image-$buildId'),
      architecture: 'amd64',
      artefactBuildId: buildId,
      testExecutionId: testExecutionId,
      isRerunRequested: false,
    );

DioException _httpError(int statusCode, {Object? data}) {
  final requestOptions = RequestOptions(path: '/v1/test-executions/reruns');
  return DioException(
    requestOptions: requestOptions,
    response: Response(
      requestOptions: requestOptions,
      statusCode: statusCode,
      data: data,
    ),
  );
}

void main() {
  group('imageRespinTargetsProvider', () {
    test('resolves the newest cdimage build execution of each release image',
        () async {
      final server = _image(1, 'stonking-live-server-amd64.iso');
      final ubuntuDesktop = _image(2, 'stonking-desktop-amd64.iso');
      final kubuntuDesktop =
          _image(3, 'stonking-desktop-amd64.iso', os: 'kubuntu');
      final nobleServer =
          _image(4, 'noble-live-server-amd64.iso', release: 'noble');
      final withoutCdimageBuild = _image(5, 'stonking-wsl-amd64.wsl');

      final api = ApiRepositoryMock();
      when(() => api.getFamilyArtefacts(FamilyName.image)).thenAnswer(
        (_) async => {
          for (final artefact in [
            server,
            ubuntuDesktop,
            kubuntuDesktop,
            nobleServer,
            withoutCdimageBuild,
          ])
            artefact.id: artefact,
        },
      );
      when(() => api.getArtefactBuilds(1)).thenAnswer(
        (_) async => [
          _build(101, [
            _execution(1001),
            _execution(
              1002,
              testPlan: 'Manual Testing',
              environment: _manualTests,
            ),
          ]),
        ],
      );
      when(() => api.getArtefactBuilds(2)).thenAnswer(
        (_) async => [
          _build(102, [
            _execution(1003),
            _execution(1004, isRerunRequested: true),
          ]),
        ],
      );
      when(() => api.getArtefactBuilds(3)).thenAnswer(
        (_) async => [
          _build(103, [_execution(1005)]),
        ],
      );
      when(() => api.getArtefactBuilds(5)).thenAnswer(
        (_) async => [
          _build(105, [
            _execution(
              1006,
              testPlan: 'Manual Testing',
              environment: _manualTests,
            ),
          ]),
        ],
      );

      final container = createContainer(
        overrides: [apiProvider.overrideWith((ref) => api)],
      );
      final result =
          await container.read(imageRespinTargetsProvider('stonking').future);

      // Sorted by name, then flavour.
      expect(
        result.targets.map((t) => (t.artefact.id, t.testExecutionId)),
        [(3, 1005), (2, 1004), (1, 1001)],
      );
      expect(
        result.targets.map((t) => t.isRerunRequested),
        [false, true, false],
      );
      expect(result.skipped, [withoutCdimageBuild]);
      verifyNever(() => api.getArtefactBuilds(4));
    });

    test('returns nothing for an empty release without calling the API',
        () async {
      final api = ApiRepositoryMock();
      final container = createContainer(
        overrides: [apiProvider.overrideWith((ref) => api)],
      );

      final result =
          await container.read(imageRespinTargetsProvider('').future);

      expect(result.targets, isEmpty);
      expect(result.skipped, isEmpty);
      verifyZeroInteractions(api);
    });
  });

  group('requestImageRespins', () {
    final targets = [_target(101, 1001), _target(102, 1002)];

    setUpAll(() => registerFallbackValue(<int>[]));

    test('reports the builds Test Observer queued', () async {
      final api = ApiRepositoryMock();
      when(() => api.requestReruns(any())).thenAnswer((_) async => {101, 102});

      final outcome = await requestImageRespins(
        api: api,
        targets: targets,
        reloadCurrentUser: () async => dummyUser,
      );

      expect(
        verify(() => api.requestReruns(captureAny())).captured.single,
        [1001, 1002],
      );
      expect(outcome, isA<ImageRespinQueued>());
      outcome as ImageRespinQueued;
      expect(outcome.queuedBuildIds, {101, 102});
      expect(outcome.notFoundBuildIds, isEmpty);
    });

    test('reports builds Test Observer did not queue as not found', () async {
      final api = ApiRepositoryMock();
      when(() => api.requestReruns(any())).thenAnswer((_) async => {101});

      final outcome = await requestImageRespins(
        api: api,
        targets: targets,
        reloadCurrentUser: () async => dummyUser,
      );

      outcome as ImageRespinQueued;
      expect(outcome.queuedBuildIds, {101});
      expect(outcome.notFoundBuildIds, {102});
    });

    test('reports missing permissions of a signed in user', () async {
      final api = ApiRepositoryMock();
      when(() => api.requestReruns(any())).thenThrow(
        _httpError(403, data: {'detail': 'Insufficient permissions'}),
      );

      final outcome = await requestImageRespins(
        api: api,
        targets: targets,
        reloadCurrentUser: () async => dummyUser,
      );

      expect(outcome, isA<ImageRespinForbidden>());
      expect((outcome as ImageRespinForbidden).userName, dummyUser.name);
    });

    test('reports an expired session as not signed in', () async {
      final api = ApiRepositoryMock();
      when(() => api.requestReruns(any())).thenThrow(
        _httpError(403, data: {'detail': 'Insufficient permissions'}),
      );

      final outcome = await requestImageRespins(
        api: api,
        targets: targets,
        reloadCurrentUser: () async => null,
      );

      expect(outcome, isA<ImageRespinNotSignedIn>());
    });

    test('reports other failures with the API error detail', () async {
      final api = ApiRepositoryMock();
      when(() => api.requestReruns(any())).thenThrow(
        _httpError(
          404,
          data: {'detail': "Didn't find test executions with provided ids"},
        ),
      );

      final outcome = await requestImageRespins(
        api: api,
        targets: targets,
        reloadCurrentUser: () async => dummyUser,
      );

      expect(outcome, isA<ImageRespinFailed>());
      expect(
        (outcome as ImageRespinFailed).detail,
        "Didn't find test executions with provided ids",
      );
    });

    test('reports failures without a response body', () async {
      final api = ApiRepositoryMock();
      when(() => api.requestReruns(any())).thenThrow(_httpError(502));

      final outcome = await requestImageRespins(
        api: api,
        targets: targets,
        reloadCurrentUser: () async => dummyUser,
      );

      expect((outcome as ImageRespinFailed).detail, 'HTTP 502');
    });
  });
}
