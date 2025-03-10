import 'package:dartx/dartx.dart';

class MultiOptionFilter<T> {
  const MultiOptionFilter({
    required this.name,
    required this.filter,
    required this.extractOptions,
  });

  final String name;
  final List<T> Function(List<T> items, Set<String> options) filter;
  final Set<String> Function(List<T> items) extractOptions;
}

MultiOptionFilter<T> createMultiOptionFilterFromExtractor<T>(
  String name,
  String Function(T) extractOption,
) =>
    MultiOptionFilter(
      name: name,
      extractOptions: (items) => items.map(extractOption).toSet(),
      filter: (items, options) => items
          .filter((item) => options.contains(extractOption(item)))
          .toList(),
    );
