import 'package:mocktail/mocktail.dart';
import 'package:test/test.dart';
import 'package:testcase_dashboard/models/artefact.dart';
import 'package:testcase_dashboard/models/family_name.dart';
import 'package:testcase_dashboard/providers/api.dart';
import 'package:testcase_dashboard/providers/family_artefacts.dart';
import 'package:testcase_dashboard/providers/filtered_family_artefacts.dart';
import 'package:testcase_dashboard/repositories/api_repository.dart';

import '../dummy_data.dart';
import '../utilities.dart';

void main() {
  test('it returns all artefacts if no filter is set', () async {
    final apiMock = ApiRepositoryMock();
    final container = createContainer(
      overrides: [apiProvider.overrideWith((ref) => apiMock)],
    );
    const family = FamilyName.snap;

    // Wait on artefacts to load cause filtersProvider uses requireValue
    await container.read(familyArtefactsProvider(family).future);

    final allArtefacts = await apiMock.getFamilyArtefacts(family);
    final filteredArtefacts =
        container.read(filteredFamilyArtefactsProvider(family));

    expect(filteredArtefacts, allArtefacts);
  });
}

class ApiRepositoryMock extends Mock implements ApiRepository {
  @override
  Future<Map<int, Artefact>> getFamilyArtefacts(FamilyName family) async {
    return {dummyArtefact.id: dummyArtefact};
  }
}
