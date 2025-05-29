import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:testcase_dashboard/ui/submittable_text_field.dart';
import 'package:testcase_dashboard/ui/vanilla/vanilla_text_input.dart';

void main() {
  group('SubmittableTextField', () {
    testWidgets('Shows title', (tester) async {
      final title = Text('title');

      await _execute(
        tester,
        SubmittableTextField(
          title: title,
          onSubmit: (_) {},
          initialValue: '',
        ),
      );

      expect(find.byWidget(title), findsOneWidget);
    });

    testWidgets('Shows initial value', (tester) async {
      final initialValue = 'Initial value';

      await _execute(
        tester,
        SubmittableTextField(
          title: Text(''),
          onSubmit: (_) {},
          initialValue: initialValue,
        ),
      );

      expect(find.text(initialValue), findsOneWidget);
    });

    testWidgets('Input is disabled by default', (tester) async {
      await _execute(
        tester,
        SubmittableTextField(
          title: Text(''),
          onSubmit: (_) {},
          initialValue: '',
        ),
      );

      final vanillaTextInput = tester.widget<VanillaTextInput>(
        find.byType(VanillaTextInput),
      );

      expect(vanillaTextInput.enabled, false);
    });

    testWidgets('Initially shows edit icon', (tester) async {
      await _execute(
        tester,
        SubmittableTextField(
          title: Text(''),
          onSubmit: (_) {},
          initialValue: '',
        ),
      );

      expect(find.byIcon(Icons.edit), findsOneWidget);
    });

    testWidgets('Clicking on edit enables the input', (tester) async {
      await _execute(
        tester,
        SubmittableTextField(
          title: Text(''),
          onSubmit: (_) {},
          initialValue: '',
        ),
      );

      await tester.tap(find.byIcon(Icons.edit));
      await tester.pumpAndSettle();

      final vanillaTextInput = tester.widget<VanillaTextInput>(
        find.byType(VanillaTextInput),
      );
      expect(vanillaTextInput.enabled, true);
    });

    testWidgets('Clicking on edit shows done icon & cancel icons',
        (tester) async {
      await _execute(
        tester,
        SubmittableTextField(
          title: Text(''),
          onSubmit: (_) {},
          initialValue: '',
        ),
      );

      await tester.tap(find.byIcon(Icons.edit));
      await tester.pumpAndSettle();

      expect(find.byIcon(Icons.done), findsOneWidget);
      expect(find.byIcon(Icons.cancel), findsOneWidget);
    });

    testWidgets('Edit write then submit', (tester) async {
      String submittedValue = '';
      final valueToSubmit = 'hi';

      await _execute(
        tester,
        SubmittableTextField(
          title: Text(''),
          onSubmit: (value) {
            submittedValue = value;
          },
          initialValue: '',
        ),
      );

      await tester.tap(find.byIcon(Icons.edit));
      await tester.pumpAndSettle();

      await tester.enterText(find.byType(VanillaTextInput), valueToSubmit);

      await tester.tap(find.byIcon(Icons.done));
      await tester.pumpAndSettle();

      expect(submittedValue, valueToSubmit);
    });

    testWidgets('Edit write then cancel', (tester) async {
      final initialValue = 'initial';
      final editedValue = 'edited';

      await _execute(
        tester,
        SubmittableTextField(
          title: Text(''),
          onSubmit: (_) {},
          initialValue: initialValue,
        ),
      );

      await tester.tap(find.byIcon(Icons.edit));
      await tester.pumpAndSettle();

      await tester.enterText(find.byType(VanillaTextInput), editedValue);

      await tester.tap(find.byIcon(Icons.cancel));
      await tester.pumpAndSettle();

      expect(find.text(initialValue), findsOneWidget);
    });

    testWidgets('Clicking on done switches back to initial state',
        (tester) async {
      await _execute(
        tester,
        SubmittableTextField(
          title: Text(''),
          onSubmit: (_) {},
          initialValue: '',
        ),
      );

      await tester.tap(find.byIcon(Icons.edit));
      await tester.pumpAndSettle();

      await tester.tap(find.byIcon(Icons.done));
      await tester.pumpAndSettle();

      expect(find.byIcon(Icons.edit), findsOneWidget);
      final vanillaTextInput = tester.widget<VanillaTextInput>(
        find.byType(VanillaTextInput),
      );
      expect(vanillaTextInput.enabled, false);
    });

    testWidgets('Clicking on cancel switches back to initial state',
        (tester) async {
      await _execute(
        tester,
        SubmittableTextField(
          title: Text(''),
          onSubmit: (_) {},
          initialValue: '',
        ),
      );

      await tester.tap(find.byIcon(Icons.edit));
      await tester.pumpAndSettle();

      await tester.tap(find.byIcon(Icons.cancel));
      await tester.pumpAndSettle();

      expect(find.byIcon(Icons.edit), findsOneWidget);
      final vanillaTextInput = tester.widget<VanillaTextInput>(
        find.byType(VanillaTextInput),
      );
      expect(vanillaTextInput.enabled, false);
    });
  });
}

_execute(WidgetTester tester, SubmittableTextField submittableTextField) async {
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        body: submittableTextField,
      ),
    ),
  );
}
