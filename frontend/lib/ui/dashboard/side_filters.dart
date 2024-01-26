import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru_widgets/yaru_widgets.dart';

import '../../models/filter.dart';
import '../../providers/filters.dart';
import '../../routing.dart';
import '../spacing.dart';

class SideFilters extends ConsumerWidget {
  const SideFilters({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final family = AppRoutes.familyFromContext(context);
    final filters = ref.watch(filtersProvider(family)).requireValue;

    return SizedBox(
      width: 400,
      child: ListView.separated(
        itemBuilder: (_, i) => _SideFilter(filter: filters[i]),
        separatorBuilder: (_, __) => const SizedBox(height: Spacing.level4),
        itemCount: filters.length,
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
      childrenPadding: const EdgeInsets.only(left: Spacing.level3),
      title: Text(filter.name),
      children: [
        for (final option in filter.options)
          Row(
            children: [
              YaruCheckbox(
                value: option.value,
                onChanged: (newValue) {
                  if (newValue != null) {
                    ref
                        .read(filtersProvider(family).notifier)
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
