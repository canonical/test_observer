import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:yaru_widgets/yaru_widgets.dart';

import '../models/filter.dart';
import '../providers/page_filters.dart';
import '../providers/search_value.dart';
import '../routing.dart';
import 'page_search_bar.dart';
import 'spacing.dart';

class SideFilters extends ConsumerWidget {
  const SideFilters({super.key, this.searchHint});

  final String? searchHint;

  static const width = 300.0;
  static const spacingBetweenFilters = Spacing.level4;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = AppRoutes.uriFromContext(context);
    final searchQuery = pageUri.queryParameters['q'];
    final filters = ref.watch(pageFiltersProvider(pageUri));

    return SizedBox(
      width: width,
      child: ListView.separated(
        shrinkWrap: true,
        itemBuilder: (_, i) {
          if (i == 0) return PageSearchBar(hintText: searchHint);

          if (i == filters.filters.length + 1) {
            return SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  final searchValue =
                      ref.read(searchValueProvider(searchQuery)).trim();
                  final queryParams = {
                    if (searchValue.isNotEmpty) 'q': searchValue,
                    ...ref.read(pageFiltersProvider(pageUri)).toQueryParams(),
                  };
                  context.go(
                    pageUri.replace(queryParameters: queryParams).toString(),
                  );
                },
                child: const Text('Apply'),
              ),
            );
          }

          return _SideFilter(
            filter: filters.filters[i - 1],
            onOptionChanged: ref
                .read(pageFiltersProvider(pageUri).notifier)
                .handleFilterOptionChange,
          );
        },
        separatorBuilder: (_, __) =>
            const SizedBox(height: spacingBetweenFilters),
        itemCount: filters.filters.length + 2,
      ),
    );
  }
}

class _SideFilter extends StatelessWidget {
  const _SideFilter({required this.filter, required this.onOptionChanged});

  final Filter filter;
  final Function(String, String, bool) onOptionChanged;

  @override
  Widget build(BuildContext context) {
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
        for (final option in filter.detectedOptions)
          Row(
            children: [
              YaruCheckbox(
                value: filter.selectedOptions.contains(option),
                onChanged: (newValue) {
                  if (newValue != null) {
                    onOptionChanged(filter.name, option, newValue);
                  }
                },
              ),
              Text(option),
            ],
          ),
      ],
    );
  }
}
