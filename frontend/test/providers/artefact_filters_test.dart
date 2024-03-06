import 'package:mocktail/mocktail.dart';
import 'package:test/test.dart';
import 'package:testcase_dashboard/models/artefact.dart';
import 'package:testcase_dashboard/models/family_name.dart';
import 'package:testcase_dashboard/providers/api.dart';
import 'package:testcase_dashboard/providers/family_artefacts.dart';
import 'package:testcase_dashboard/providers/artefact_filters.dart';
import 'package:testcase_dashboard/repositories/api_repository.dart';

import '../dummy_data.dart';
import '../utilities.dart';

void main() {
  test('it collects options from fetched artefacts', () async {
    final container = createContainer(
      overrides: [apiProvider.overrideWith((ref) => ApiRepositoryMock())],
    );
    const family = FamilyName.snap;

    // Wait on artefacts to load cause artefactFiltersProvider uses requireValue
    await container.read(familyArtefactsProvider(family).future);

    final filters = container.read(artefactFiltersProvider(family)).filters;

    expect(filters[0].name, 'Assignee');
    expect(
      filters[0].options,
      [(name: dummyArtefact.assignee?.name, value: false)],
    );
    expect(filters[1].name, 'Status');
    expect(
      filters[1].options,
      [(name: dummyArtefact.status.name, value: false)],
    );
  });
}

class ApiRepositoryMock extends Mock implements ApiRepository {
  @override
  Future<Map<int, Artefact>> getFamilyArtefacts(FamilyName family) async {
    return {dummyArtefact.id: dummyArtefact};
  }
}
