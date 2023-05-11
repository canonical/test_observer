import 'package:riverpod_annotation/riverpod_annotation.dart' hide Family;

import '../models/family.dart';

part 'providers.g.dart';

@riverpod
Future<List<Family>> fetchFamilies(FetchFamiliesRef ref) {
  return Future.delayed(
    const Duration(seconds: 2),
    () => const [
      Family(name: 'Family 1'),
      Family(name: 'Family 2'),
      Family(name: 'Family 3')
    ],
  );
}
