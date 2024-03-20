import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru_widgets/yaru_widgets.dart';

import '../../providers/family_artefacts.dart';
import '../../providers/artefact_side_filters_visibility.dart';
import '../../routing.dart';
import '../page_filters/page_filters.dart';
import '../spacing.dart';
import 'dashboard_body.dart';
import 'dashboard_header.dart';

class Dashboard extends ConsumerWidget {
  const Dashboard({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final showFilters = ref.watch(artefactSideFiltersVisibilityProvider);
    final family = AppRoutes.familyFromUri(AppRoutes.uriFromContext(context));

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
