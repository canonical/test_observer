import 'package:testcase_dashboard/models/artefact.dart';
import 'package:testcase_dashboard/models/artefact_build.dart';
import 'package:testcase_dashboard/models/environment.dart';
import 'package:testcase_dashboard/models/stage_name.dart';
import 'package:testcase_dashboard/models/test_execution.dart';
import 'package:testcase_dashboard/models/user.dart';

const dummyUser = User(
  id: 1,
  name: 'Omar Abou Selo',
  launchpadEmail: 'omar.selo@canonical.com',
  launchpadHandle: 'omar-selo',
);

const dummyArtefact = Artefact(
  id: 1,
  name: 'core',
  version: '16-2.61',
  track: 'latest',
  store: 'ubuntu',
  series: '',
  repo: '',
  status: ArtefactStatus.undecided,
  stage: StageName.beta,
  assignee: dummyUser,
  bugLink: '',
  allEnvironmentReviewsCount: 1,
  completedEnvironmentReviewsCount: 0,
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
  reviewComment: '',
  reviewDecision: [],
  artefactBuildId: dummyArtefactBuild.id,
);
