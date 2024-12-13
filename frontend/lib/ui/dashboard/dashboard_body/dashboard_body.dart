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
      },
    );
  }
}
