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
