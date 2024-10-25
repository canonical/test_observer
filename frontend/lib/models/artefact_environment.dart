import 'package:dartx/dartx.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

import 'environment.dart';
import 'environment_review.dart';
import 'test_execution.dart';

part 'artefact_environment.freezed.dart';

@freezed
class ArtefactEnvironment with _$ArtefactEnvironment {
  const ArtefactEnvironment._();

  const factory ArtefactEnvironment({
    required SortedList<TestExecution> runsDescending,
    required EnvironmentReview review,
  }) = _ArtefactEnvironment;

  String get name => review.environment.name;
  String get architecture => review.environment.architecture;
  Environment get environment => review.environment;
}
