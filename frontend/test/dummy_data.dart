import 'package:testcase_dashboard/models/artefact.dart';
import 'package:testcase_dashboard/models/stage_name.dart';
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
);
