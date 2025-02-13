// Copyright (C) 2023-2025 Canonical Ltd.
//
// This file is part of Test Observer Frontend.
//
// Test Observer Frontend is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// Test Observer Frontend is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

import 'package:freezed_annotation/freezed_annotation.dart';

import 'environment.dart';

part 'environment_review.freezed.dart';
part 'environment_review.g.dart';

@freezed
class EnvironmentReview with _$EnvironmentReview {
  static const String reviewCommentJsonKey = 'review_comment';
  static const String reviewDecisionJsonKey = 'review_decision';

  const factory EnvironmentReview({
    required int id,
    @JsonKey(name: 'artefact_build')
    required EnvironmentReviewArtefactBuild artefactBuild,
    required Environment environment,
    @JsonKey(name: EnvironmentReview.reviewCommentJsonKey)
    required String reviewComment,
    @JsonKey(name: EnvironmentReview.reviewDecisionJsonKey)
    required List<EnvironmentReviewDecision> reviewDecision,
  }) = _EnvironmentReview;

  factory EnvironmentReview.fromJson(Map<String, Object?> json) =>
      _$EnvironmentReviewFromJson(json);
}

@freezed
class EnvironmentReviewArtefactBuild with _$EnvironmentReviewArtefactBuild {
  const factory EnvironmentReviewArtefactBuild({
    required int id,
    required String architecture,
    required int? revision,
  }) = _EnvironmentReviewArtefactBuild;

  factory EnvironmentReviewArtefactBuild.fromJson(Map<String, Object?> json) =>
      _$EnvironmentReviewArtefactBuildFromJson(json);
}

enum EnvironmentReviewDecision {
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
        return 'Approve (customer provided prerequisite failing)';
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
      default:
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
