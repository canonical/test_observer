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

import '../spacing.dart';
import 'test_results_filters_view.dart';
import 'test_results_body.dart';

class TestResultsPage extends ConsumerStatefulWidget {
  const TestResultsPage({super.key});

  @override
  ConsumerState<TestResultsPage> createState() => _TestResultsPageState();
}

class _TestResultsPageState extends ConsumerState<TestResultsPage> {
  bool showFilters = true;

  @override
  Widget build(BuildContext context) {
    const pagePad = EdgeInsets.all(Spacing.pageHorizontalPadding);

    return Padding(
      padding: pagePad,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                'Test Results',
                style: Theme.of(context).textTheme.headlineLarge,
              ),
              const Spacer(),
              YaruOptionButton(
                child: const Icon(Icons.filter_alt),
                onPressed: () => setState(() => showFilters = !showFilters),
              ),
            ],
          ),
          const SizedBox(height: Spacing.level4),
          if (showFilters) ...[
            const TestResultsFiltersView(),
            const SizedBox(height: Spacing.level4),
          ],
          const Expanded(
            child: TestResultsBody(),
          ),
        ],
      ),
    );
  }
}
