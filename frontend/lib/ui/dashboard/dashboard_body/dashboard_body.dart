import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru/widgets.dart';

import '../../../models/family_name.dart';
import '../../../providers/view_mode.dart';
import '../../../routing.dart';
import 'artefacts_columns_view.dart';
import 'artefacts_list_view/artefacts_list_view.dart';

class DashboardBody extends ConsumerWidget {
  const DashboardBody({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final uri = AppRoutes.uriFromContext(context);
    final family = AppRoutes.familyFromUri(uri);
    final viewMode = ref.watch(viewModeProvider);

    return viewMode.when(
      loading: () => const YaruCircularProgressIndicator(),
      error: (_, __) => const SizedBox.shrink(),
      data: (viewMode) => switch ((family, viewMode)) {
        (_, ViewModes.dashboard) => const ArtefactsColumnsView(),
        (FamilyName.snap, ViewModes.list) => const ArtefactsListView.snaps(),
        (FamilyName.deb, ViewModes.list) => const ArtefactsListView.debs(),
      },
    );
  }
}
