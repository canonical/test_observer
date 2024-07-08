import 'package:flutter/material.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:yaru/yaru.dart';
import 'package:yaru_icons/yaru_icons.dart';

import 'environment.dart';

part 'test_execution.freezed.dart';
part 'test_execution.g.dart';

@freezed
class TestExecution with _$TestExecution {
  static const String reviewCommentJsonKey = 'review_comment';
  static const String reviewDecisionJsonKey = 'review_decision';

  const factory TestExecution({
    required int id,
    @JsonKey(name: 'ci_link') required String? ciLink,
    @JsonKey(name: 'c3_link') required String? c3Link,
    required TestExecutionStatus status,
    required Environment environment,
    @JsonKey(name: TestExecution.reviewCommentJsonKey)
    required String reviewComment,
    @JsonKey(name: TestExecution.reviewDecisionJsonKey)
    required List<TestExecutionReviewDecision> reviewDecision,
    @Default(false) @JsonKey(name: 'is_rerun_requested') bool isRerunRequested,
  }) = _TestExecution;

  factory TestExecution.fromJson(Map<String, Object?> json) =>
      _$TestExecutionFromJson(json);

  static Object updateReviewDecisionRequestData(
    String reviewComment,
    List<TestExecutionReviewDecision> reviewDecision,
  ) {
    return {
      reviewCommentJsonKey: reviewComment,
      reviewDecisionJsonKey: reviewDecision,
    };
  }
}

enum TestExecutionStatus {
  @JsonValue('FAILED')
  failed,
  @JsonValue('NOT_STARTED')
  notStarted,
  @JsonValue('NOT_TESTED')
  notTested,
  @JsonValue('IN_PROGRESS')
  inProgress,
  @JsonValue('PASSED')
  passed;

  bool get isCompleted {
    switch (this) {
      case notStarted:
      case inProgress:
      case notTested:
        return false;
      case passed:
      case failed:
        return true;
    }
  }

  String get name {
    switch (this) {
      case notStarted:
        return 'Not Started';
      case inProgress:
        return 'In Progress';
      case passed:
        return 'Passed';
      case failed:
        return 'Failed';
      case notTested:
        return 'Not Tested';
    }
  }

  Icon get icon {
    const size = 20.0;
    switch (this) {
      case notStarted:
        return const Icon(YaruIcons.media_play, size: size);
      case inProgress:
        return const Icon(YaruIcons.refresh, size: size);
      case passed:
        return Icon(YaruIcons.ok, color: YaruColors.light.success, size: size);
      case failed:
        return const Icon(YaruIcons.error, color: YaruColors.red, size: size);
      case notTested:
        return const Icon(YaruIcons.information, size: size);
    }
  }
}

enum TestExecutionReviewDecision {
  @JsonValue('REJECTED')
  rejected,
  @JsonValue('APPROVED_INCONSISTENT_TEST')
  approvedInconsistentTest,
  @JsonValue('APPROVED_UNSTABLE_PHYSICAL_INFRA')
  approvedUnstablePhysicalInfra,
  @JsonValue('APPROVED_CUSTOMER_PREREQUISITE_FAIL')
  approvedCustomerPrerequisiteFail,
  @JsonValue('APPROVED_FAULTY_HARDWARE')
  approvedFaultyHardware,
  @JsonValue('APPROVED_ALL_TESTS_PASS')
  approvedAllTestsPass;

  String get name {
    switch (this) {
      case rejected:
        return 'Reject';
      case approvedInconsistentTest:
        return 'Approve (inconsistent test definition)';
      case approvedUnstablePhysicalInfra:
        return 'Approve (unstable physical infrastructure)';
      case approvedCustomerPrerequisiteFail:
        return 'Approve (customer provided prerequsite failing)';
      case approvedFaultyHardware:
        return 'Approve (faulty hardware)';
      case approvedAllTestsPass:
        return 'Approve (all tests pass)';
    }
  }

  bool get isDeprecated {
    switch (this) {
      case approvedFaultyHardware:
      case approvedUnstablePhysicalInfra:
        return true;
      case rejected:
      case approvedInconsistentTest:
      case approvedCustomerPrerequisiteFail:
      case approvedAllTestsPass:
        return false;
    }
  }

  String toJson() {
    switch (this) {
      case rejected:
        return 'REJECTED';
      case approvedInconsistentTest:
        return 'APPROVED_INCONSISTENT_TEST';
      case approvedUnstablePhysicalInfra:
        return 'APPROVED_UNSTABLE_PHYSICAL_INFRA';
      case approvedCustomerPrerequisiteFail:
        return 'APPROVED_CUSTOMER_PREREQUISITE_FAIL';
      case approvedFaultyHardware:
        return 'APPROVED_FAULTY_HARDWARE';
      case approvedAllTestsPass:
        return 'APPROVED_ALL_TESTS_PASS';
    }
  }
}
