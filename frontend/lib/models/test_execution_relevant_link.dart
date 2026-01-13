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

import 'package:freezed_annotation/freezed_annotation.dart';

part 'test_execution_relevant_link.freezed.dart';
part 'test_execution_relevant_link.g.dart';

@freezed
abstract class TestExecutionRelevantLink with _$TestExecutionRelevantLink {
  const factory TestExecutionRelevantLink({
    required int id,
    required String label,
    required String url,
  }) = _TestExecutionRelevantLink;

  factory TestExecutionRelevantLink.fromJson(Map<String, dynamic> json) =>
      _$TestExecutionRelevantLinkFromJson(json);
}
