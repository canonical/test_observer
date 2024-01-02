import 'package:flutter/material.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:yaru/yaru.dart';
import 'package:yaru_icons/yaru_icons.dart';

import 'environment.dart';

part 'test_execution.freezed.dart';
part 'test_execution.g.dart';

@freezed
class TestExecution with _$TestExecution {
  const factory TestExecution({
    required int id,
    @JsonKey(name: 'ci_link') required String? ciLink,
    @JsonKey(name: 'c3_link') required String? c3Link,
    required TestExecutionStatus status,
    required Environment environment,
    @JsonKey(name: 'review_comment') required String reviewComment,
    @JsonKey(name: 'review_decision')
    required List<TestExecutionReviewDecision> reviewDecision,
  }) = _TestExecution;

  factory TestExecution.fromJson(Map<String, Object?> json) =>
      _$TestExecutionFromJson(json);
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
