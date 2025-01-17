// Copyright (C) 2024 Canonical Ltd.
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

import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mocktail/mocktail.dart';
import 'package:testcase_dashboard/app.dart';
import 'package:testcase_dashboard/models/artefact.dart';
import 'package:testcase_dashboard/models/artefact_build.dart';
import 'package:testcase_dashboard/models/environment.dart';
import 'package:testcase_dashboard/models/family_name.dart';
import 'package:testcase_dashboard/models/stage_name.dart';
import 'package:testcase_dashboard/models/test_execution.dart';
import 'package:testcase_dashboard/models/test_result.dart';
import 'package:testcase_dashboard/providers/api.dart';
import 'package:testcase_dashboard/repositories/api_repository.dart';
import 'package:web_benchmarks/client.dart';

abstract class AppRecorder extends WidgetRecorder {
  AppRecorder({required this.benchmarkName}) : super(name: benchmarkName);

  final String benchmarkName;

  Future<void> start();

  Future<void> animationStops() async {
    while (WidgetsBinding.instance.hasScheduledFrame) {
      await Future.delayed(const Duration(milliseconds: 200));
    }
  }

  @override
  Widget createWidget() {
    Future.delayed(const Duration(milliseconds: 400), start);
    return ProviderScope(
      // ignore: scoped_providers_should_specify_dependencies
      overrides: [apiProvider.overrideWithValue(ApiRepositoryMock())],
      child: const App(),
    );
  }
}

class ApiRepositoryMock extends Mock implements ApiRepository {
  @override
  Future<Map<int, Artefact>> getFamilyArtefacts(FamilyName family) async {
    const dummyArtefact = Artefact(
      id: 1,
      name: 'artefact',
      version: '1',
      track: 'latest',
      store: 'ubuntu',
      series: '',
      repo: '',
      status: ArtefactStatus.undecided,
      stage: StageName.beta,
      bugLink: '',
      allEnvironmentReviewsCount: 1,
      completedEnvironmentReviewsCount: 0,
    );

    return {
      for (int i = 0; i < 100; i++)
        i: dummyArtefact.copyWith(id: i, name: 'artefact $i'),
    };
  }

  @override
  Future<List<ArtefactBuild>> getArtefactBuilds(int artefactId) async {
    return [
      ArtefactBuild(
        id: 1,
        architecture: 'amd64',
        revision: 1,
        testExecutions: [
          for (int i = 0; i < 200; i++)
            TestExecution(
              id: i,
              ciLink: 'ciLink',
              c3Link: 'c3Link',
              status: TestExecutionStatus.failed,
              environment: Environment(
                id: i,
                name: 'Environment $i',
                architecture: 'amd64',
              ),
              artefactBuildId: 1,
              testPlan: 'test plan',
            ),
        ],
      ),
      ArtefactBuild(
        id: 2,
        architecture: 'armhf',
        revision: 1,
        testExecutions: [
          for (int i = 200; i < 400; i++)
            TestExecution(
              id: i,
              ciLink: 'ciLink',
              c3Link: 'c3Link',
              status: TestExecutionStatus.failed,
              environment: Environment(
                id: i,
                name: 'Environment $i',
                architecture: 'armhf',
              ),
              artefactBuildId: i,
              testPlan: 'test plan',
            ),
        ],
      ),
    ];
  }

  @override
  Future<List<TestResult>> getTestExecutionResults(int testExecutionId) async {
    return [
      for (int i = 0; i < 300; i++)
        TestResult(name: 'result $i', status: TestResultStatus.passed),
    ];
  }
}
