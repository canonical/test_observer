import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru_widgets/yaru_widgets.dart';

import '../../models/filter.dart';
import '../../providers/artefact_filters.dart';
import '../../routing.dart';
import '../spacing.dart';
import 'artefact_search_bar.dart';

class SideFilters extends ConsumerWidget {
  const SideFilters({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final family = AppRoutes.familyFromContext(context);
    final filters = ref.watch(artefactFiltersProvider(family));

    return SizedBox(
      width: 300,
      child: ListView.separated(
        itemBuilder: (_, i) => (i == 0)
            ? ArtefactSearchBar()
            : _SideFilter(filter: filters[i - 1]),
        separatorBuilder: (_, __) => const SizedBox(height: Spacing.level4),
        itemCount: filters.length + 1,
      ),
    );
  }
}

class _SideFilter extends ConsumerWidget {
  const _SideFilter({required this.filter});

  final Filter filter;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final family = AppRoutes.familyFromContext(context);

    return ExpansionTile(
      initiallyExpanded: true,
      controlAffinity: ListTileControlAffinity.leading,
      childrenPadding: const EdgeInsets.only(left: Spacing.level4),
      shape: const Border(),
      collapsedShape: const Border(),
      title: Text(
        filter.name,
        style: Theme.of(context).textTheme.headlineSmall,
      ),
      children: [
        for (final option in filter.options)
          Row(
            children: [
              YaruCheckbox(
                value: option.value,
                onChanged: (newValue) {
                  if (newValue != null) {
                    ref
                        .read(artefactFiltersProvider(family).notifier)
                        .handleFilterOptionChange(
                          filter.name,
                          option.name,
                          newValue,
                        );
                  }
                },
              ),
              Text(option.name),
            ],
          ),
      ],
    );
  }
}
