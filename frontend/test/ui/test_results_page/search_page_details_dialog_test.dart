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

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:testcase_dashboard/models/search_page_results.dart';
import 'package:testcase_dashboard/providers/api.dart';
import 'package:testcase_dashboard/repositories/api_repository.dart';
import 'package:testcase_dashboard/ui/test_results_page/search_page_results_table.dart';
import 'package:testcase_dashboard/ui/test_results_page/test_results_details_dialog.dart';

import '../../search_page_test_data.dart';

void main() {
  testWidgets('Does not start loading after dialog route is disposed', (
    tester,
  ) async {
    final api = _DetailsApiFake([]);
    final navigatorKey = GlobalKey<NavigatorState>();
    final row = SearchPageTableRow.fromJson(searchPageRowJson());

    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiProvider.overrideWith((ref) => api)],
        child: MaterialApp(
          navigatorKey: navigatorKey,
          home: const Scaffold(body: Text('Base route')),
        ),
      ),
    );

    navigatorKey.currentState!.push<void>(
      MaterialPageRoute<void>(
        builder: (_) => _RemoveRouteBeforeDetailsLoad(
          child: Scaffold(
            body: SearchPageTestResultDetailsDialog(result: row),
          ),
        ),
      ),
    );
    await tester.pump();

    expect(api.requestedIds, isEmpty);
    expect(tester.takeException(), isNull);
    expect(find.text('Base route'), findsOneWidget);
  });

  testWidgets(
    'Details lazily loads selected result, retries errors, and renders',
    (tester) async {
      tester.view.physicalSize = const Size(1400, 900);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      final failedRequest = Completer<SearchPageDetailsResponse>();
      final api = _DetailsApiFake([
        failedRequest.future,
        Future.value(
          SearchPageDetailsResponse.fromJson(searchPageDetailsJson()),
        ),
      ]);
      final row = SearchPageTableRow.fromJson(searchPageRowJson());

      await tester.pumpWidget(
        ProviderScope(
          overrides: [apiProvider.overrideWith((ref) => api)],
          child: MaterialApp(
            home: Scaffold(body: SearchPageResultsTable(testResults: [row])),
          ),
        ),
      );
      expect(api.requestedIds, isEmpty);
      expect(find.text('smoke'), findsOneWidget);

      await tester.tap(find.text('Details'));
      await tester.pump();
      expect(api.requestedIds, [23]);
      expect(find.text('Loading test result details…'), findsOneWidget);

      failedRequest.completeError(Exception('network unavailable'));
      await tester.pumpAndSettle();
      expect(find.text('Error loading test result details'), findsOneWidget);
      expect(find.text('Retry'), findsOneWidget);

      await tester.tap(find.text('Retry'));
      await tester.pumpAndSettle();

      expect(api.requestedIds, [23, 23]);
      expect(find.text('one selected result log'), findsOneWidget);
      expect(find.text('Issue title'), findsOneWidget);
      expect(find.text('#8'), findsOneWidget);
      expect(find.text('View Run'), findsNothing);
    },
  );
}

class _RemoveRouteBeforeDetailsLoad extends StatefulWidget {
  const _RemoveRouteBeforeDetailsLoad({required this.child});

  final Widget child;

  @override
  State<_RemoveRouteBeforeDetailsLoad> createState() =>
      _RemoveRouteBeforeDetailsLoadState();
}

class _RemoveRouteBeforeDetailsLoadState
    extends State<_RemoveRouteBeforeDetailsLoad> {
  bool _removalScheduled = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_removalScheduled) return;
    _removalScheduled = true;

    final route = ModalRoute.of(context);
    if (route == null) return;
    final navigator = Navigator.of(context);
    Future<void>.microtask(() => navigator.removeRoute(route));
  }

  @override
  Widget build(BuildContext context) => widget.child;
}

class _DetailsApiFake extends Mock implements ApiRepository {
  _DetailsApiFake(this.responses);

  final List<Future<SearchPageDetailsResponse>> responses;
  final requestedIds = <int>[];

  @override
  Future<SearchPageDetailsResponse> getSearchPageTestResultDetails(
    int testResultId,
  ) {
    requestedIds.add(testResultId);
    return responses.removeAt(0);
  }
}
