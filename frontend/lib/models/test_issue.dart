// Copyright 2024 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:freezed_annotation/freezed_annotation.dart';

part 'test_issue.freezed.dart';
part 'test_issue.g.dart';

@freezed
abstract class TestIssue with _$TestIssue {
  const factory TestIssue({
    required int id,
    @JsonKey(name: 'template_id') required String templateId,
    @JsonKey(name: 'case_name') required String caseName,
    required String description,
    required String url,
  }) = _TestIssue;

  factory TestIssue.fromJson(Map<String, Object?> json) =>
      _$TestIssueFromJson(json);
}
