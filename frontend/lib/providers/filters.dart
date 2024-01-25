import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/filter.dart';

part 'filters.g.dart';

@riverpod
List<Filter> filters(FiltersRef ref) {
  return [Filter(name: 'Pass All', shouldInclude: (_) => true)];
}
