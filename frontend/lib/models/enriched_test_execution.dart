import 'package:freezed_annotation/freezed_annotation.dart';

import 'environment_review.dart';
import 'test_execution.dart';

part 'enriched_test_execution.freezed.dart';

@freezed
class EnrichedTestExecution with _$EnrichedTestExecution {
  const factory EnrichedTestExecution({
    required TestExecution testExecution,
    required EnvironmentReview environmentReview,
  }) = _EnrichedTestExecution;
}
