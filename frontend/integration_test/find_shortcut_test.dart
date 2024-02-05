import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:testcase_dashboard/app.dart';
import 'package:testcase_dashboard/models/artefact.dart';
import 'package:testcase_dashboard/models/family_name.dart';
import 'package:testcase_dashboard/providers/api.dart';
import 'package:testcase_dashboard/repositories/api_repository.dart';
import 'package:testcase_dashboard/ui/dashboard/artefact_search_bar.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('Ctrl+F opens side filters and focuses on artefact search bar',
      (tester) async {
    final apiMock = ApiRepositoryMock();
    await tester.pumpWidget(
      ProviderScope(
        // ignore: scoped_providers_should_specify_dependencies
        overrides: [apiProvider.overrideWithValue(apiMock)],
        child: const App(),
      ),
    );

    await tester.pumpAndSettle();

    await tester.sendKeyDownEvent(LogicalKeyboardKey.control);
    await tester.sendKeyEvent(LogicalKeyboardKey.keyF);

    await tester.pumpAndSettle();

    expect(find.byKey(artefactSearchBarKey), findsOneWidget);
    expect(artefactSearchBarKey.currentState?.focusNode.hasFocus, isTrue);
  });
}

class ApiRepositoryMock extends Mock implements ApiRepository {
  @override
  Future<Map<int, Artefact>> getFamilyArtefacts(FamilyName family) async => {};
}
