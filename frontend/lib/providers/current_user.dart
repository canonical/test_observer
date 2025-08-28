import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/user.dart';
import 'api.dart';

part 'current_user.g.dart';

@riverpod
Future<User?> currentUser(Ref ref) {
  final api = ref.watch(apiProvider);
  return api.getCurrentUser();
}
