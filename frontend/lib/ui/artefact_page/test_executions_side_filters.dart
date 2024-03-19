import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../providers/test_execution_filters.dart';
import '../side_filters.dart';

class TestExecutionsSideFilters extends ConsumerWidget {
  const TestExecutionsSideFilters({super.key, required this.artefactId});

  final int artefactId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = GoRouterState.of(context).uri;
    final filters =
        ref.watch(testExecutionFiltersProvider(artefactId, pageUri));

    return SideFilters(
      filters: filters,
      onOptionChanged: ref
          .read(testExecutionFiltersProvider(artefactId, pageUri).notifier)
          .handleFilterOptionChange,
      onSubmit: () {
        final newQueryParams = {
          ...ref
              .read(testExecutionFiltersProvider(artefactId, pageUri))
              .toQueryParams(),
        };
        context.go(
          pageUri.replace(queryParameters: newQueryParams).toString(),
        );
      },
    );
  }
}
