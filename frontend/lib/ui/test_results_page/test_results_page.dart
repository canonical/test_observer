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

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru/widgets.dart';
import 'package:go_router/go_router.dart';

import '../../models/test_results_filters.dart';
import '../../routing.dart';
import '../spacing.dart';
import 'bulk_operations/bulk_operation_buttons.dart';
import 'test_results_body.dart';
import 'test_results_filters_view.dart';

class TestResultsPage extends ConsumerStatefulWidget {
  const TestResultsPage({super.key});

  @override
  ConsumerState<TestResultsPage> createState() => _TestResultsPageState();
}

class _TestResultsPageState extends ConsumerState<TestResultsPage> {
  bool showFilters = true;
  late TestResultsFilters appliedFilters;
  bool filtersModified = false;

  void _onApplyFilters(TestResultsFilters filters) {
    context.go(filters.toTestResultsUri().toString());
    setState(() {
      filtersModified = false;
    });
  }

  void _onFiltersChanged(TestResultsFilters filters) {
    setState(() {
      filtersModified = filters != appliedFilters;
    });
  }

  @override
  Widget build(BuildContext context) {
    final uri = AppRoutes.uriFromContext(context);
    appliedFilters = TestResultsFilters.fromQueryParams(uri.queryParametersAll);

    return Padding(
      padding: const EdgeInsets.only(
        left: Spacing.pageHorizontalPadding,
        right: Spacing.pageHorizontalPadding,
        top: Spacing.level5,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        spacing: Spacing.level4,
        children: [
          Row(
            children: [
              Text(
                'Search Test Results',
                style: Theme.of(context).textTheme.headlineLarge,
              ),
              const Spacer(),
              YaruOptionButton(
                child: const Icon(Icons.filter_alt),
                onPressed: () {
                  setState(() {
                    showFilters = !showFilters;
                  });
                },
              ),
            ],
          ),
          if (showFilters)
            TestResultsFiltersView(
              initialFilters: appliedFilters,
              onApplyFilters: _onApplyFilters,
              onChanged: _onFiltersChanged,
            ),
          BulkOperationsButtons(
            filters: appliedFilters,
            disabled: filtersModified,
          ),
          Expanded(
            child: TestResultsBody(filters: appliedFilters),
          ),
        ],
      ),
    );
  }
}
