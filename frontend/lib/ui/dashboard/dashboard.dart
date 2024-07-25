import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru_widgets/yaru_widgets.dart';

import '../../models/family_name.dart';
import '../../providers/family_artefacts.dart';
import '../../providers/artefact_side_filters_visibility.dart';
import '../../routing.dart';
import '../page_filters/page_filters.dart';
import '../spacing.dart';
import 'artefacts_columns_view.dart';
import 'artefacts_list_view/artefacts_list_view.dart';
import 'dashboard_header.dart';

class Dashboard extends ConsumerWidget {
  const Dashboard({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final showFilters = ref.watch(artefactSideFiltersVisibilityProvider);
    final pageUri = AppRoutes.uriFromContext(context);
    final family = AppRoutes.familyFromUri(pageUri);

    final viewType =
        pageUri.queryParameters['view'] == 'list' ? 'list' : 'dashboard';

    return Padding(
      padding: const EdgeInsets.only(
        left: Spacing.pageHorizontalPadding,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          DashboardHeader(
            title: '${family.name.capitalize()} Update Verification',
          ),
          Expanded(
            child: _ArtefactsLoader(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  YaruOptionButton(
                    child: const Icon(Icons.filter_alt),
                    onPressed: () => ref
                        .read(artefactSideFiltersVisibilityProvider.notifier)
                        .set(!showFilters),
                  ),
                  Visibility(
                    visible: showFilters,
                    maintainState: true,
                    child: const PageFiltersView(searchHint: 'Search by name'),
                  ),
                  const SizedBox(width: Spacing.level5),
                  Expanded(
                    child: switch ((family, viewType)) {
                      (FamilyName.snap, 'list') =>
                        const ArtefactsListView.snaps(),
                      (FamilyName.deb, 'list') =>
                        const ArtefactsListView.debs(),
                      (_, _) => const ArtefactsColumnsView(),
                    },
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ArtefactsLoader extends ConsumerWidget {
  const _ArtefactsLoader({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final family = AppRoutes.familyFromUri(AppRoutes.uriFromContext(context));
    final artefacts = ref.watch(familyArtefactsProvider(family));

    return artefacts.when(
      data: (_) => child,
      error: (e, stack) =>
          Center(child: Text('Error:\n$e\nStackTrace:\n$stack')),
      loading: () => const Center(child: YaruCircularProgressIndicator()),
    );
  }
}
