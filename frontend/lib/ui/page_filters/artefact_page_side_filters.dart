import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../providers/filters_state.dart';
import '../../routing.dart';
import '../spacing.dart';
import 'checkbox_list_expandable.dart';

class ArtefactPageSideFilters extends ConsumerWidget {
  const ArtefactPageSideFilters({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = AppRoutes.uriFromContext(context);
    final filters = ref.watch(filtersStateProvider(pageUri)).value ?? [];

    return SizedBox(
      width: 300.0,
      child: ListView.separated(
        shrinkWrap: true,
        itemCount: filters.length,
        separatorBuilder: (_, __) => const SizedBox(height: Spacing.level4),
        itemBuilder: (_, i) {
          if (i == filters.length) {
            return SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () => context.go(
                  pageUri.replace(
                    queryParameters: {
                      ...pageUri.queryParametersAll,
                      ...FiltersState.toQueryParams(filters),
                    },
                  ).toString(),
                ),
                child: const Text('Apply'),
              ),
            );
          }

          return CheckboxListExpandable(
            title: filters[i].name,
            options: filters[i].options,
            onChanged: (option, isSelected) => ref
                .read(filtersStateProvider(pageUri).notifier)
                .onChanged(filters[i].name, option, isSelected),
          );
        },
      ),
    );
  }
}
