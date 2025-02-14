// Copyright (C) 2023 Canonical Ltd.
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

import 'package:flutter/material.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:yaru/yaru.dart';

import 'stage_name.dart';
import 'user.dart';

part 'artefact.freezed.dart';
part 'artefact.g.dart';

@freezed
class Artefact with _$Artefact {
  const Artefact._();

  const factory Artefact({
    required int id,
    required String name,
    required String version,
    required String family,
    @Default('') String track,
    @Default('') String store,
    @Default('') String series,
    @Default('') String repo,
    @Default('') String os,
    @Default('') String release,
    @Default('') String owner,
    @Default('') String sha256,
    @Default('') @JsonKey(name: 'image_url') String imageUrl,
    required ArtefactStatus status,
    required StageName stage,
    @JsonKey(name: 'all_environment_reviews_count')
    required int allEnvironmentReviewsCount,
    @JsonKey(name: 'completed_environment_reviews_count')
    required int completedEnvironmentReviewsCount,
    @Default(emptyUser) User assignee,
    @JsonKey(name: 'bug_link') required String bugLink,
    @JsonKey(name: 'due_date') DateTime? dueDate,
  }) = _Artefact;

  factory Artefact.fromJson(Map<String, Object?> json) =>
      _$ArtefactFromJson(json);

  String? get dueDateString {
    final month = dueDate?.month;
    final day = dueDate?.day;
    if (month != null && day != null) {
      return '${monthNames[month - 1]} $day';
    }
    return null;
  }

  int get remainingTestExecutionCount =>
      allEnvironmentReviewsCount - completedEnvironmentReviewsCount;
}

const List<String> monthNames = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
];

enum ArtefactStatus {
  @JsonValue('APPROVED')
  approved,
  @JsonValue('MARKED_AS_FAILED')
  rejected,
  @JsonValue('UNDECIDED')
  undecided;

  String get name {
    switch (this) {
      case approved:
        return 'Approved';
      case rejected:
        return 'Rejected';
      case undecided:
        return 'Undecided';
    }
  }

  Color get color {
    switch (this) {
      case approved:
        return YaruColors.light.success;
      case rejected:
        return YaruColors.red;
      case undecided:
        return YaruColors.textGrey;
    }
  }

  String toJson() {
    switch (this) {
      case approved:
        return 'APPROVED';
      case rejected:
        return 'MARKED_AS_FAILED';
      case undecided:
        return 'UNDECIDED';
    }
  }
}
