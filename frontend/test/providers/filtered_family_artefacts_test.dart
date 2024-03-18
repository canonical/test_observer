import 'package:mocktail/mocktail.dart';
import 'package:test/test.dart';
import 'package:testcase_dashboard/models/artefact.dart';
import 'package:testcase_dashboard/models/family_name.dart';
import 'package:testcase_dashboard/providers/api.dart';
import 'package:testcase_dashboard/providers/family_artefacts.dart';
import 'package:testcase_dashboard/providers/filtered_family_artefacts.dart';
import 'package:testcase_dashboard/repositories/api_repository.dart';
import 'package:testcase_dashboard/routing.dart';

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
    final filteredArtefacts = container
        .read(filteredFamilyArtefactsProvider(Uri(path: AppRoutes.snaps)));

    expect(filteredArtefacts, allArtefacts);
  });

  test('it filters artefacts by assignees', () async {
    final apiMock = ApiRepositoryMock();
    final container = createContainer(
      overrides: [apiProvider.overrideWith((ref) => apiMock)],
    );
    const family = FamilyName.snap;

    // Wait on artefacts to load cause filtersProvider uses requireValue
    await container.read(familyArtefactsProvider(family).future);

    final firstArtefact =
        (await apiMock.getFamilyArtefacts(family)).values.first;

    final filteredArtefacts = container.read(
      filteredFamilyArtefactsProvider(
        Uri(
          path: AppRoutes.snaps,
          queryParameters: {'Assignee': firstArtefact.assignee!.name},
        ),
      ),
    );

    expect(filteredArtefacts, {firstArtefact.id: firstArtefact});
  });

  test('it filters artefacts by status', () async {
    final apiMock = ApiRepositoryMock();
    final container = createContainer(
      overrides: [apiProvider.overrideWith((ref) => apiMock)],
    );
    const family = FamilyName.snap;

    // Wait on artefacts to load cause filtersProvider uses requireValue
    await container.read(familyArtefactsProvider(family).future);

    final firstArtefact =
        (await apiMock.getFamilyArtefacts(family)).values.first;

    final filteredArtefacts = container.read(
      filteredFamilyArtefactsProvider(
        Uri(
          path: AppRoutes.snaps,
          queryParameters: {'Status': firstArtefact.status.name},
        ),
      ),
    );

    expect(filteredArtefacts, {firstArtefact.id: firstArtefact});
  });

  test('it finds artefacts by name', () async {
    final apiMock = ApiRepositoryMock();
    final container = createContainer(
      overrides: [apiProvider.overrideWith((ref) => apiMock)],
    );
    const family = FamilyName.snap;

    // Wait on artefacts to load cause filtersProvider uses requireValue
    await container.read(familyArtefactsProvider(family).future);

    final firstArtefact =
        (await apiMock.getFamilyArtefacts(family)).values.first;

    final filteredArtefacts = container.read(
      filteredFamilyArtefactsProvider(
        Uri(
          path: AppRoutes.snaps,
          queryParameters: {'q': firstArtefact.name},
        ),
      ),
    );

    expect(filteredArtefacts, {firstArtefact.id: firstArtefact});
  });
}

class ApiRepositoryMock extends Mock implements ApiRepository {
  @override
  Future<Map<int, Artefact>> getFamilyArtefacts(FamilyName family) async {
    final artefacts = [
      dummyArtefact,
      dummyArtefact.copyWith(
        id: 2,
        assignee: null,
        name: 'snapd',
        status: ArtefactStatus.approved,
      ),
    ];
    return {for (final a in artefacts) a.id: a};
  }
}
