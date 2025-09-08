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

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:testcase_dashboard/ui/page_filters/multi_select_combobox.dart';
import 'package:yaru/yaru.dart';

void main() {
  group('MultiSelectCombobox', () {
    const testOptions = ['Option 1', 'Option 2', 'Option 3', 'Option 4'];

    Widget createWidget({
      List<String> allOptions = testOptions,
      int maxSuggestions = 10,
      Set<String> initialSelected = const {},
      Function(String, bool)? onChanged,
    }) {
      return MaterialApp(
        home: Scaffold(
          body: MultiSelectCombobox(
            title: 'Test Combobox',
            allOptions: allOptions,
            maxSuggestions: maxSuggestions,
            initialSelected: initialSelected,
            onChanged: onChanged ?? (option, isSelected) {},
          ),
        ),
      );
    }

    testWidgets('displays title with selection count', (tester) async {
      await tester.pumpWidget(createWidget());

      expect(find.text('Test Combobox (0 selected)'), findsOneWidget);
    });

    testWidgets('expands when tapped', (tester) async {
      await tester.pumpWidget(createWidget());

      // Initially collapsed - no VanillaTextInput
      expect(find.byType(TextFormField), findsNothing);

      // Tap to expand
      await tester.tap(find.text('Test Combobox (0 selected)'));
      await tester.pumpAndSettle();

      // Should show search field (VanillaTextInput uses TextFormField internally)
      expect(find.byType(TextFormField), findsOneWidget);
      expect(find.text('Search...'), findsOneWidget);
    });

    testWidgets('filters suggestions based on search input', (tester) async {
      await tester.pumpWidget(createWidget());

      // Expand combobox
      await tester.tap(find.text('Test Combobox (0 selected)'));
      await tester.pumpAndSettle();

      // Type in search field
      await tester.enterText(find.byType(TextFormField), 'Option 1');
      await tester.pumpAndSettle();

      // Should show filtered suggestion in ListTile
      expect(find.widgetWithText(ListTile, 'Option 1'), findsOneWidget);
      expect(find.widgetWithText(ListTile, 'Option 2'), findsNothing);
    });

    testWidgets('limits suggestions to maxSuggestions', (tester) async {
      final manyOptions = List.generate(15, (i) => 'Option $i');

      await tester.pumpWidget(
        createWidget(
          allOptions: manyOptions,
          maxSuggestions: 5,
        ),
      );

      // Expand combobox
      await tester.tap(find.text('Test Combobox (0 selected)'));
      await tester.pumpAndSettle();

      // Type to trigger suggestions (TypeAhead needs input to show suggestions)
      await tester.enterText(find.byType(TextFormField), 'Option');
      await tester.pumpAndSettle();

      // Check that only maxSuggestions items are shown in ListTiles
      for (int i = 0; i < 5; i++) {
        expect(find.widgetWithText(ListTile, 'Option $i'), findsOneWidget);
      }
      for (int i = 5; i < 15; i++) {
        expect(find.widgetWithText(ListTile, 'Option $i'), findsNothing);
      }
    });

    testWidgets('calls onChanged when option is selected', (tester) async {
      String? selectedOption;
      bool? isSelected;

      await tester.pumpWidget(
        createWidget(
          onChanged: (option, selected) {
            selectedOption = option;
            isSelected = selected;
          },
        ),
      );

      // Expand combobox
      await tester.tap(find.text('Test Combobox (0 selected)'));
      await tester.pumpAndSettle();

      // Start typing to trigger suggestions
      await tester.enterText(find.byType(TextFormField), 'Option');
      await tester.pumpAndSettle();

      // Now we should see suggestions - tap on the ListTile containing Option 1
      expect(find.widgetWithText(ListTile, 'Option 1'), findsOneWidget);
      await tester.tap(find.widgetWithText(ListTile, 'Option 1'));
      await tester.pumpAndSettle();

      expect(selectedOption, equals('Option 1'));
      expect(isSelected, isTrue);
    });

    testWidgets('shows selected items with checkboxes', (tester) async {
      await tester.pumpWidget(createWidget());

      // Expand combobox
      await tester.tap(find.text('Test Combobox (0 selected)'));
      await tester.pumpAndSettle();

      // Start typing to trigger suggestions
      await tester.enterText(find.byType(TextFormField), 'Option');
      await tester.pumpAndSettle();

      // Tap on the ListTile containing Option 1
      expect(find.widgetWithText(ListTile, 'Option 1'), findsOneWidget);
      await tester.tap(find.widgetWithText(ListTile, 'Option 1'));
      await tester.pumpAndSettle();

      // Should show selected item with YaruCheckbox and updated count
      expect(find.text('Test Combobox (1 selected)'), findsOneWidget);
      expect(find.byType(YaruCheckbox), findsOneWidget);
    });

    testWidgets('initializes with pre-selected values', (tester) async {
      await tester.pumpWidget(
        createWidget(
          initialSelected: {'Option 1', 'Option 2'},
        ),
      );

      // Should show correct count and be expanded with YaruCheckboxes
      expect(find.text('Test Combobox (2 selected)'), findsOneWidget);
      expect(find.byType(YaruCheckbox), findsNWidgets(2));
    });

    testWidgets('auto-expands when initialized with selections',
        (tester) async {
      await tester.pumpWidget(
        createWidget(
          initialSelected: {'Option 1'},
        ),
      );

      // Should be expanded by default
      expect(find.byType(TextFormField), findsOneWidget);
      expect(find.text('Search...'), findsOneWidget);
    });

    testWidgets('remains collapsed when no initial selections', (tester) async {
      await tester.pumpWidget(
        createWidget(
          initialSelected: {},
        ),
      );

      // Should be collapsed by default
      expect(find.byType(TextFormField), findsNothing);
    });

    testWidgets('removes items when checkbox is unchecked', (tester) async {
      await tester.pumpWidget(
        createWidget(
          initialSelected: {'Option 1'},
        ),
      );

      // Should start with 1 selected
      expect(find.text('Test Combobox (1 selected)'), findsOneWidget);
      expect(find.byType(YaruCheckbox), findsOneWidget);

      // Tap the checkbox to remove the item
      await tester.tap(find.byType(YaruCheckbox));
      await tester.pumpAndSettle();

      // Should now show 0 selected
      expect(find.text('Test Combobox (0 selected)'), findsOneWidget);
      expect(find.byType(YaruCheckbox), findsNothing);
    });
  });
}
