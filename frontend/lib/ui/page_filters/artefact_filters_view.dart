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

import '../../providers/page_filters.dart';
import '../../routing.dart';
import 'base_filters_view.dart';
import 'multi_select_combobox.dart';

/// Artefact filters view that shows Environment and Test plan as comboboxes
class ArtefactFiltersView extends ConsumerWidget {
  const ArtefactFiltersView({super.key, this.width = 300.0});

  final double width;

  // Global key for environment combobox focus
  static final GlobalKey<MultiSelectComboboxState> environmentComboboxKey =
      GlobalKey<MultiSelectComboboxState>();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = AppRoutes.uriFromContext(context);
    final filters = ref.watch(pageFiltersProvider(pageUri));

    return BaseFiltersView(
      pageUri: pageUri,
      filters: filters,
      width: width,
      showSearchBar: false,
      comboboxFilterNames: const {'Environment', 'Test plan'},
      environmentComboboxKey: environmentComboboxKey,
    );
  }
}
