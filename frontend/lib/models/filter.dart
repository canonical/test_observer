import 'artefact.dart';

class Filter {
  final String name;
  final bool Function(Artefact) shouldInclude;

  const Filter({required this.name, required this.shouldInclude});
}
