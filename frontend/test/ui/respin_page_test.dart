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
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:testcase_dashboard/models/environment.dart';
import 'package:testcase_dashboard/models/family_name.dart';
import 'package:testcase_dashboard/providers/api.dart';
import 'package:testcase_dashboard/providers/image_respin.dart';
import 'package:testcase_dashboard/repositories/api_repository.dart';
import 'package:testcase_dashboard/ui/respin_page/respin_page.dart';

import '../dummy_data.dart';

class ApiRepositoryMock extends Mock implements ApiRepository {}

final _server = dummyArtefact.copyWith(
  id: 1,
  name: 'stonking-live-server-amd64.iso',
  os: 'ubuntu-server',
  release: 'stonking',
  family: 'image',
  version: '20260920',
);

ApiRepositoryMock _apiWithOneImage() {
  final api = ApiRepositoryMock();
  var rerunRequested = false;
  when(() => api.getFamilyArtefacts(FamilyName.image))
      .thenAnswer((_) async => {_server.id: _server});
  when(() => api.getArtefactBuilds(_server.id)).thenAnswer(
    (_) async => [
      dummyArtefactBuild.copyWith(
        id: 101,
        testExecutions: [
          dummyTestExecution.copyWith(
            id: 1001,
            testPlan: imageBuildTestPlan,
            environment: const Environment(
              id: 10,
              name: cdimageEnvironment,
              architecture: 'amd64',
            ),
            isRerunRequested: rerunRequested,
          ),
        ],
      ),
    ],
  );
  when(() => api.requestReruns(any())).thenAnswer((_) async {
    rerunRequested = true;
    return {101};
  });
  return api;
}

Future<void> _pumpPage(WidgetTester tester, ApiRepository api) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [apiProvider.overrideWith((ref) => api)],
      child: const MaterialApp(
        home: Scaffold(body: RespinPage(release: 'stonking')),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

ElevatedButton _requestButton(WidgetTester tester) => tester
    .widget(find.widgetWithText(ElevatedButton, 'Request respin of 1 image'));

void main() {
  setUpAll(() => registerFallbackValue(<int>[]));

  testWidgets('asks signed out users to log in before requesting',
      (tester) async {
    final api = _apiWithOneImage();
    when(() => api.getCurrentUser()).thenAnswer((_) async => null);

    await _pumpPage(tester, api);

    expect(find.text('Respin images — Stonking'), findsOneWidget);
    expect(find.text('Sign in to request respins'), findsOneWidget);
    expect(find.text('Log in'), findsOneWidget);
    expect(_requestButton(tester).onPressed, isNull);
  });

  testWidgets('requests respins only after confirmation', (tester) async {
    final api = _apiWithOneImage();
    when(() => api.getCurrentUser()).thenAnswer((_) async => dummyUser);

    await _pumpPage(tester, api);
    expect(find.text('Signed in as ${dummyUser.name}'), findsOneWidget);

    await tester.tap(find.text('Request respin of 1 image'));
    await tester.pumpAndSettle();
    expect(find.text('Confirm respin'), findsOneWidget);
    verifyNever(() => api.requestReruns(any()));

    await tester.tap(find.text('respin'));
    await tester.pumpAndSettle();

    verify(() => api.requestReruns([1001])).called(1);
    expect(
      find.text('Respin requested for 1 image. You can close this tab.'),
      findsOneWidget,
    );

    // The status column shows what Test Observer reports after re-reading.
    await tester.tap(find.text('Show images (1)'));
    await tester.pumpAndSettle();
    expect(find.text('Queued'), findsOneWidget);
  });

  testWidgets('does not request anything when the confirmation is cancelled',
      (tester) async {
    final api = _apiWithOneImage();
    when(() => api.getCurrentUser()).thenAnswer((_) async => dummyUser);

    await _pumpPage(tester, api);
    await tester.tap(find.text('Request respin of 1 image'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('cancel'));
    await tester.pumpAndSettle();

    verifyNever(() => api.requestReruns(any()));
    expect(_requestButton(tester).onPressed, isNotNull);
  });

  testWidgets('explains when the signed in account lacks permission',
      (tester) async {
    final api = _apiWithOneImage();
    when(() => api.getCurrentUser()).thenAnswer((_) async => dummyUser);
    final requestOptions = RequestOptions(path: '/v1/test-executions/reruns');
    when(() => api.requestReruns(any())).thenThrow(
      DioException(
        requestOptions: requestOptions,
        response: Response(
          requestOptions: requestOptions,
          statusCode: 403,
          data: {'detail': 'Insufficient permissions'},
        ),
      ),
    );

    await _pumpPage(tester, api);
    await tester.tap(find.text('Request respin of 1 image'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('respin'));
    await tester.pumpAndSettle();

    expect(
      find.text(
        "Signed in as ${dummyUser.name}, but this account can't request "
        'respins. Nothing was queued.',
      ),
      findsOneWidget,
    );
  });
}
