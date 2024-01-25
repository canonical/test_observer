import 'artefact.dart';

class Filter {
  final String name;
  final bool Function(Artefact) shouldInclude;
  final List<String> options;

  const Filter({
    required this.name,
    required this.shouldInclude,
    required this.options,
  });
}
