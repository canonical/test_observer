import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:yaru/widgets.dart';

import '../../models/filter.dart';
import '../../providers/page_filters.dart';
import '../../providers/search_value.dart';
import '../../routing.dart';
import '../expandable.dart';
import 'page_search_bar.dart';
import '../spacing.dart';

class PageFiltersView extends ConsumerWidget {
  const PageFiltersView({super.key, this.searchHint, this.width = 300.0});

  final String? searchHint;
  final double width;

  static const spacingBetweenFilters = Spacing.level4;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = AppRoutes.uriFromContext(context);
    final searchQuery =
        pageUri.queryParameters[CommonQueryParameters.searchQuery];
    final filters = ref.watch(pageFiltersProvider(pageUri));

    return SizedBox(
      width: width,
      child: ListView.separated(
        shrinkWrap: true,
        itemBuilder: (_, i) {
          if (i == 0) {
            return PageSearchBar(
              hintText: searchHint,
              onSubmitted: (_) =>
                  submitFilters(ref, searchQuery, pageUri, context),
            );
          }

          if (i == filters.filters.length + 1) {
            return SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () =>
                    submitFilters(ref, searchQuery, pageUri, context),
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

  void submitFilters(
    WidgetRef ref,
    String? searchQuery,
    Uri pageUri,
    BuildContext context,
  ) {
    final sortBy = pageUri.queryParameters[CommonQueryParameters.sortBy];
    final sortDirection =
        pageUri.queryParameters[CommonQueryParameters.sortDirection];
    final searchValue = ref.read(searchValueProvider(searchQuery)).trim();
    final queryParams = {
      if (searchValue.isNotEmpty)
        CommonQueryParameters.searchQuery: searchValue,
      ...ref.read(pageFiltersProvider(pageUri)).toQueryParams(),
      if (sortBy != null) CommonQueryParameters.sortBy: sortBy,
      if (sortDirection != null)
        CommonQueryParameters.sortDirection: sortDirection,
    };
    context.go(
      pageUri.replace(queryParameters: queryParams).toString(),
    );
  }
}

class _SideFilter extends StatelessWidget {
  const _SideFilter({required this.filter, required this.onOptionChanged});

  final Filter filter;
  final Function(String, String, bool) onOptionChanged;

  @override
  Widget build(BuildContext context) {
    return Expandable(
      initiallyExpanded: true,
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
