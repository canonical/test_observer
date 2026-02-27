// Copyright 2025 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/material.dart';
import 'package:yaru/yaru.dart';

import '../../providers/issues.dart';
import '../../providers/issues_filters.dart';
import '../../routing.dart';
import '../blocking_provider_preloader.dart';
import '../spacing.dart';
import 'issues_page_body.dart';
import 'issues_page_side_visibility.dart';
import 'issues_page_side.dart';
import 'issues_page_header.dart';

class IssuesPage extends ConsumerWidget {
  const IssuesPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return BlockingProviderPreloader(
      provider: issuesProvider(),
      builder: (context, issues) {
        final showSide = ref.watch(issuesPageSideVisibilityProvider);
        final pageUri = AppRoutes.uriFromContext(context);
        final filtersState = ref.watch(issuesFiltersProvider(pageUri));
        final searchQuery =
            pageUri.queryParameters[CommonQueryParameters.searchQuery] ?? '';
        final hasActiveFilters = filtersState.selectedSources.isNotEmpty ||
            filtersState.selectedStatuses.isNotEmpty ||
            filtersState.selectedProjects.isNotEmpty ||
            searchQuery.isNotEmpty;

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            IssuesPageHeader(title: 'Linked External Issues'),
            const SizedBox(height: Spacing.level4),
            Expanded(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Padding(
                    padding: const EdgeInsets.all(4),
                    child: Badge(
                      isLabelVisible: hasActiveFilters,
                      smallSize: 8,
                      backgroundColor: YaruColors.orange,
                      child: YaruOptionButton(
                        child: const Icon(Icons.filter_alt),
                        onPressed: () => ref
                            .read(issuesPageSideVisibilityProvider.notifier)
                            .set(!showSide),
                      ),
                    ),
                  ),
                  const SizedBox(width: Spacing.level2),
                  Visibility(
                    visible: showSide,
                    maintainState: true,
                    child: IssuesPageSide(
                      searchHint: 'Search issues...',
                    ),
                  ),
                  const SizedBox(width: Spacing.level5),
                  Expanded(child: IssuesPageBody()),
                ],
              ),
            ),
          ],
        );
      },
    );
  }
}
