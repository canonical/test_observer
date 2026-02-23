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
import 'package:yaru/yaru.dart';

import '../../providers/artefact.dart';
import '../../providers/artefact_page_side_visibility.dart';
import '../../providers/page_filters.dart';
import '../../routing.dart';
import '../blocking_provider_preloader.dart';
import '../spacing.dart';
import 'artefact_page_body.dart';
import 'artefact_page_header.dart';
import 'artefact_page_side.dart';

class ArtefactPage extends ConsumerWidget {
  const ArtefactPage({super.key, required this.artefactId});

  final int artefactId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Padding(
      padding: const EdgeInsets.only(
        left: Spacing.pageHorizontalPadding,
        right: Spacing.pageHorizontalPadding,
        top: Spacing.level5,
      ),
      child: BlockingProviderPreloader(
        provider: artefactProvider(artefactId),
        builder: (context, artefact) {
          final showSide = ref.watch(artefactPageSideVisibilityProvider);
          final pageUri = AppRoutes.uriFromContext(context);
          final filters = ref.watch(pageFiltersProvider(pageUri));
          final hasActiveFilters =
              filters.any((f) => f.options.any((o) => o.isSelected));

          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ArtefactPageHeader(artefact: artefact),
              const SizedBox(height: Spacing.level4),
              Expanded(
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Badge(
                      isLabelVisible: hasActiveFilters,
                      smallSize: 8,
                      backgroundColor: YaruColors.orange,
                      child: YaruOptionButton(
                        child: const Icon(Icons.filter_alt),
                        onPressed: () => ref
                            .read(artefactPageSideVisibilityProvider.notifier)
                            .set(!showSide),
                      ),
                    ),
                    const SizedBox(width: Spacing.level2),
                    Visibility(
                      visible: showSide,
                      maintainState: true,
                      child: ArtefactPageSide(artefact: artefact),
                    ),
                    Expanded(child: ArtefactPageBody(artefact: artefact)),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}
