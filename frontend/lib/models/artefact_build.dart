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

import 'test_execution.dart';

part 'artefact_build.freezed.dart';

@freezed
class ArtefactBuild with _$ArtefactBuild {
  const ArtefactBuild._();

  const factory ArtefactBuild({
    required int id,
    required String architecture,
    required int? revision,
    required List<TestExecution> testExecutions,
  }) = _ArtefactBuild;

  factory ArtefactBuild.fromJson(Map<String, Object?> json) {
    return ArtefactBuild(
      architecture: json['architecture'] as String,
      id: json['id'] as int,
      revision: json['revision'] as int?,
      testExecutions: [
        for (final te in json['test_executions'] as List)
          TestExecution.fromJson({...te, 'artefact_build_id': json['id']}),
      ],
    );
  }
}
