// Copyright 2026 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:freezed_annotation/freezed_annotation.dart';

part 'rerun_details.freezed.dart';
part 'rerun_details.g.dart';

@freezed
abstract class RerunPrioritySummary with _$RerunPrioritySummary {
  const factory RerunPrioritySummary({
    required int priority,
    required int count,
  }) = _RerunPrioritySummary;

  factory RerunPrioritySummary.fromJson(Map<String, Object?> json) =>
      _$RerunPrioritySummaryFromJson(json);
}

@freezed
abstract class RerunDetail with _$RerunDetail {
  const factory RerunDetail({
    @JsonKey(name: 'test_plan_name') required String testPlanName,
    @JsonKey(name: 'created_at') required DateTime createdAt,
    required int priority,
    required String architecture,
    @JsonKey(name: 'environment_name') required String environmentName,
  }) = _RerunDetail;

  factory RerunDetail.fromJson(Map<String, Object?> json) =>
      _$RerunDetailFromJson(json);
}

@freezed
abstract class RerunDetailsResponse with _$RerunDetailsResponse {
  const factory RerunDetailsResponse({
    @JsonKey(name: 'priority_summaries')
    required List<RerunPrioritySummary> prioritySummaries,
    @JsonKey(name: 'selected_priority') int? selectedPriority,
    required int count,
    @JsonKey(name: 'selected_count') required int selectedCount,
    required int limit,
    required int offset,
    required List<RerunDetail> reruns,
  }) = _RerunDetailsResponse;

  factory RerunDetailsResponse.fromJson(Map<String, Object?> json) =>
      _$RerunDetailsResponseFromJson(json);
}
