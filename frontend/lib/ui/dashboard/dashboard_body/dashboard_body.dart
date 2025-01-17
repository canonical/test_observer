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

import 'package:flutter/widgets.dart';

import '../../../models/family_name.dart';
import '../../../models/view_modes.dart';
import '../../../providers/view_mode.dart';
import '../../../routing.dart';
import '../../blocking_provider_preloader.dart';
import 'artefacts_columns_view.dart';
import 'artefacts_list_view/artefacts_list_view.dart';

class DashboardBody extends StatelessWidget {
  const DashboardBody({super.key});

  @override
  Widget build(BuildContext context) {
    final uri = AppRoutes.uriFromContext(context);
    final family = AppRoutes.familyFromUri(uri);

    return BlockingProviderPreloader(
      provider: viewModeProvider,
      builder: (_, viewMode) => switch ((family, viewMode)) {
        (_, ViewModes.dashboard) => const ArtefactsColumnsView(),
        (FamilyName.snap, ViewModes.list) => const ArtefactsListView.snaps(),
        (FamilyName.deb, ViewModes.list) => const ArtefactsListView.debs(),
        (FamilyName.charm, ViewModes.list) => const ArtefactsListView.charms(),
        (FamilyName.image, ViewModes.list) => const ArtefactsListView.images(),
      },
    );
  }
}
