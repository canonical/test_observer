import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../providers/test_execution_filters.dart';
import '../side_filters.dart';

class TestExecutionsSideFilters extends ConsumerWidget {
  const TestExecutionsSideFilters({super.key, required this.artefactId});

  final int artefactId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final filters = ref.watch(testExecutionFiltersProvider(artefactId));

    return SideFilters(
      filters: filters,
      onOptionChanged: ref
          .read(testExecutionFiltersProvider(artefactId).notifier)
          .handleFilterOptionChange,
    );
  }
}
