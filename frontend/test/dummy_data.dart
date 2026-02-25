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

import 'package:testcase_dashboard/models/artefact.dart';
import 'package:testcase_dashboard/models/artefact_build.dart';
import 'package:testcase_dashboard/models/environment.dart';
import 'package:testcase_dashboard/models/environment_review.dart';
import 'package:testcase_dashboard/models/stage_name.dart';
import 'package:testcase_dashboard/models/test_execution.dart';
import 'package:testcase_dashboard/models/user.dart';

const dummyUser = User(
  id: 1,
  name: 'Omar Abou Selo',
  email: 'omar.selo@canonical.com',
  launchpadHandle: 'omar-selo',
);

const dummyUser2 = User(
  id: 2,
  name: 'John Doe',
  email: 'john.doe@canonical.com',
  launchpadHandle: 'john-doe',
);

const dummyUser3 = User(
  id: 3,
  name: 'Jane Smith',
  email: 'jane.smith@canonical.com',
  launchpadHandle: 'jane-smith',
);

const dummyArtefact = Artefact(
  id: 1,
  name: 'core',
  version: '16-2.61',
  family: 'snap',
  track: 'latest',
  store: 'ubuntu',
  series: '',
  repo: '',
  status: ArtefactStatus.undecided,
  stage: StageName.beta,
  reviewers: [dummyUser, dummyUser2, dummyUser3],
  bugLink: '',
  allEnvironmentReviewsCount: 1,
  completedEnvironmentReviewsCount: 0,
  comment: '',
);

const dummyEnvironment = Environment(
  id: 1,
  name: 'laptop',
  architecture: 'amd64',
);

const dummyArtefactBuild = ArtefactBuild(
  id: 1,
  architecture: 'amd64',
  revision: 1,
  testExecutions: [],
);

final dummyTestExecution = TestExecution(
  id: 1,
  ciLink: 'ci-link',
  c3Link: 'c3-link',
  status: TestExecutionStatus.passed,
  environment: dummyEnvironment,
  artefactBuildId: dummyArtefactBuild.id,
  testPlan: 'test plan',
  createdAt: DateTime.now(),
  isTriaged: false,
);

final dummyEnvironmentReview = EnvironmentReview(
  id: 1,
  artefactBuild: EnvironmentReviewArtefactBuild(
    id: dummyArtefactBuild.id,
    architecture: dummyArtefactBuild.architecture,
    revision: dummyArtefactBuild.revision,
  ),
  environment: dummyEnvironment,
  reviewComment: '',
  reviewDecision: [],
);
