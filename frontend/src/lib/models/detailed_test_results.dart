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
import 'artefact.dart';
import 'test_result.dart';
import 'test_execution.dart';

part 'detailed_test_results.freezed.dart';
part 'detailed_test_results.g.dart';

@freezed
abstract class TestResultsSearchResult with _$TestResultsSearchResult {
  const factory TestResultsSearchResult({
    required int count,
    @JsonKey(name: 'test_results')
    required List<TestResultWithContext> testResults,
  }) = _TestResultsSearchResult;

  const TestResultsSearchResult._();

  bool get hasMore => count > testResults.length;

  factory TestResultsSearchResult.fromJson(Map<String, dynamic> json) =>
      _$TestResultsSearchResultFromJson(json);

  factory TestResultsSearchResult.empty() {
    return const TestResultsSearchResult(
      count: 0,
      testResults: [],
    );
  }
}

@freezed
abstract class TestResultWithContext with _$TestResultWithContext {
  const factory TestResultWithContext({
    @JsonKey(name: 'test_result') required TestResult testResult,
    @JsonKey(name: 'test_execution') required TestExecution testExecution,
    @JsonKey(name: 'artefact') required Artefact artefact,
    @JsonKey(name: 'artefact_build')
    required ArtefactBuildMinimal artefactBuild,
  }) = _TestResultWithContext;

  factory TestResultWithContext.fromJson(Map<String, dynamic> json) =>
      _$TestResultWithContextFromJson(json);
}

@freezed
abstract class ArtefactBuildMinimal with _$ArtefactBuildMinimal {
  const factory ArtefactBuildMinimal({
    required int id,
    required String architecture,
    @JsonKey(name: 'revision') @Default(null) int? revision,
  }) = _ArtefactBuildMinimal;

  factory ArtefactBuildMinimal.fromJson(Map<String, dynamic> json) =>
      _$ArtefactBuildMinimalFromJson(json);
}
