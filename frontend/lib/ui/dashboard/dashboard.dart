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

import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru/widgets.dart';

import '../../providers/family_artefacts.dart';
import '../../providers/dashboard_page_side_visibility.dart';
import '../../routing.dart';
import '../blocking_provider_preloader.dart';
import '../page_filters/page_filters.dart';
import '../spacing.dart';
import 'dashboard_body/dashboard_body.dart';
import 'dashboard_header/dashboard_header.dart';

class Dashboard extends ConsumerWidget {
  const Dashboard({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final showFilters = ref.watch(dashboardPageSideVisibilityProvider);
    final family = AppRoutes.familyFromUri(AppRoutes.uriFromContext(context));

    return Padding(
      padding: const EdgeInsets.only(
        left: Spacing.pageHorizontalPadding,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(
              right: Spacing.pageHorizontalPadding,
            ),
            child: DashboardHeader(
              title: '${family.name.capitalize()} Update Verification',
            ),
          ),
          Expanded(
            child: BlockingProviderPreloader(
              provider: familyArtefactsProvider(family),
              builder: (_, __) => Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  YaruOptionButton(
                    child: const Icon(Icons.filter_alt),
                    onPressed: () => ref
                        .read(dashboardPageSideVisibilityProvider.notifier)
                        .set(!showFilters),
                  ),
                  Visibility(
                    visible: showFilters,
                    maintainState: true,
                    child: const PageFiltersView(searchHint: 'Search by name'),
                  ),
                  const SizedBox(width: Spacing.level5),
                  const Expanded(child: DashboardBody()),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
