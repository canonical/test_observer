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
          body: MultiSelectCombobox<String>(
            title: 'Test Combobox',
            allOptions: allOptions,
            itemToString: (item) => item,
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

    testWidgets('works with custom itemBuilder', (tester) async {
      Widget customItemBuilder(String item) {
        return Row(
          children: [
            const Icon(Icons.star),
            const SizedBox(width: 8),
            Text(item),
          ],
        );
      }

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: MultiSelectCombobox<String>(
              title: 'Custom Builder',
              allOptions: testOptions,
              itemToString: (item) => item,
              itemBuilder: customItemBuilder,
              initialSelected: {'Option 1'},
              onChanged: (option, isSelected) {},
            ),
          ),
        ),
      );

      // Should show custom builder with icon for selected items
      expect(find.byIcon(Icons.star), findsOneWidget);
      expect(find.text('Option 1'), findsOneWidget);
    });

    testWidgets('works with async suggestions callback', (tester) async {
      Future<List<String>> asyncSuggestions(String pattern) async {
        await Future.delayed(const Duration(milliseconds: 100));
        return testOptions
            .where(
              (option) => option.toLowerCase().contains(pattern.toLowerCase()),
            )
            .toList();
      }

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: MultiSelectCombobox<String>(
              title: 'Async Combobox',
              asyncSuggestionsCallback: asyncSuggestions,
              itemToString: (item) => item,
              minCharsForAsyncSearch: 2,
              onChanged: (option, isSelected) {},
            ),
          ),
        ),
      );

      // Expand combobox
      await tester.tap(find.text('Async Combobox (0 selected)'));
      await tester.pumpAndSettle();

      // Type enough characters to trigger async search
      await tester.enterText(find.byType(TextFormField), 'Option 1');
      await tester.pump(const Duration(milliseconds: 100));
      await tester.pumpAndSettle();

      // Should show filtered suggestion
      expect(find.widgetWithText(ListTile, 'Option 1'), findsOneWidget);
    });

    testWidgets('displays and handles meta options', (tester) async {
      dynamic selectedMetaValue;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: MultiSelectCombobox<String>(
              title: 'Meta Options Test',
              allOptions: testOptions,
              itemToString: (item) => item,
              metaOptions: const [
                MetaOption(value: 'any', label: 'Any'),
                MetaOption(value: 'none', label: 'None'),
              ],
              selectedMetaOption: null,
              onMetaOptionChanged: (value) {
                selectedMetaValue = value;
              },
              onChanged: (option, isSelected) {},
            ),
          ),
        ),
      );

      // Expand combobox
      await tester.tap(find.text('Meta Options Test (0 selected)'));
      await tester.pumpAndSettle();

      // Should show meta options
      expect(find.text('Any'), findsOneWidget);
      expect(find.text('None'), findsOneWidget);

      // Tap on 'Any' meta option
      await tester.tap(find.text('Any'));
      await tester.pumpAndSettle();

      expect(selectedMetaValue, equals('any'));
    });

    testWidgets('auto-expands when initialized with meta option',
        (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: MultiSelectCombobox<String>(
              title: 'Meta Selected',
              allOptions: testOptions,
              itemToString: (item) => item,
              metaOptions: const [
                MetaOption(value: 'any', label: 'Any'),
              ],
              selectedMetaOption: 'any',
              onMetaOptionChanged: (value) {},
              onChanged: (option, isSelected) {},
            ),
          ),
        ),
      );

      // Should be expanded by default when meta option is selected
      expect(find.byType(TextFormField), findsOneWidget);
      expect(find.text('Search...'), findsOneWidget);
      expect(find.text('Any'), findsOneWidget);
    });

    testWidgets('meta options are mutually exclusive with selections',
        (tester) async {
      String? selectedOption;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: MultiSelectCombobox<String>(
              title: 'Exclusive Test',
              allOptions: testOptions,
              itemToString: (item) => item,
              metaOptions: const [
                MetaOption(value: 'any', label: 'Any'),
              ],
              selectedMetaOption: 'any',
              onMetaOptionChanged: (value) {},
              onChanged: (option, isSelected) {
                selectedOption = option;
              },
            ),
          ),
        ),
      );

      // Should show 'Any' as selected
      expect(find.text('Any'), findsOneWidget);

      // Start typing to show suggestions
      await tester.enterText(find.byType(TextFormField), 'Option');
      await tester.pumpAndSettle();

      // Selecting a regular option should call onChanged
      await tester.tap(find.widgetWithText(ListTile, 'Option 1'));
      await tester.pumpAndSettle();

      expect(selectedOption, equals('Option 1'));
    });

    testWidgets('respects minCharsForAsyncSearch threshold', (tester) async {
      Future<List<String>> asyncSuggestions(String pattern) async {
        await Future.delayed(const Duration(milliseconds: 50));
        return testOptions
            .where(
              (option) => option.toLowerCase().contains(pattern.toLowerCase()),
            )
            .toList();
      }

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: MultiSelectCombobox<String>(
              title: 'Min Chars Test',
              asyncSuggestionsCallback: asyncSuggestions,
              itemToString: (item) => item,
              minCharsForAsyncSearch: 3,
              onChanged: (option, isSelected) {},
            ),
          ),
        ),
      );

      // Expand combobox
      await tester.tap(find.text('Min Chars Test (0 selected)'));
      await tester.pumpAndSettle();

      // Should show hint about minimum characters
      expect(find.text('Type 3+ characters to search...'), findsOneWidget);

      // Type only 2 characters (below threshold)
      await tester.enterText(find.byType(TextFormField), 'Op');
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      // Should not show any suggestions (below threshold)
      expect(find.widgetWithText(ListTile, 'Option 1'), findsNothing);

      // Type 3 characters (meets threshold)
      await tester.enterText(find.byType(TextFormField), 'Opt');
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));
      await tester.pumpAndSettle();

      // Now should show suggestions
      expect(find.widgetWithText(ListTile, 'Option 1'), findsOneWidget);
    });

    group('showAllOptionsWithoutSearch mode', () {
      Widget createWidgetWithAllOptionsMode({
        List<String> allOptions = testOptions,
        Set<String> initialSelected = const {},
        Function(String, bool)? onChanged,
      }) {
        return MaterialApp(
          home: Scaffold(
            body: MultiSelectCombobox<String>(
              title: 'All Options Mode',
              allOptions: allOptions,
              itemToString: (item) => item,
              showAllOptionsWithoutSearch: true,
              initialSelected: initialSelected,
              onChanged: onChanged ?? (option, isSelected) {},
            ),
          ),
        );
      }

      testWidgets('displays all options when expanded without search box',
          (tester) async {
        await tester.pumpWidget(createWidgetWithAllOptionsMode());

        // Initially collapsed
        expect(find.text('All Options Mode (0 selected)'), findsOneWidget);

        // Expand combobox
        await tester.tap(find.text('All Options Mode (0 selected)'));
        await tester.pumpAndSettle();

        // Should NOT show search field
        expect(find.byType(TextFormField), findsNothing);

        // Should show all options with checkboxes
        expect(find.text('Option 1'), findsOneWidget);
        expect(find.text('Option 2'), findsOneWidget);
        expect(find.text('Option 3'), findsOneWidget);
        expect(find.text('Option 4'), findsOneWidget);

        // Should have 4 checkboxes (one for each option)
        expect(find.byType(YaruCheckbox), findsNWidgets(4));
      });

      testWidgets('shows initial selections correctly', (tester) async {
        final initialSelected = {'Option 1', 'Option 3'};

        await tester.pumpWidget(
          StatefulBuilder(
            builder: (context, setState) {
              return MaterialApp(
                home: Scaffold(
                  body: MultiSelectCombobox<String>(
                    title: 'Selection Test',
                    allOptions: testOptions,
                    itemToString: (item) => item,
                    showAllOptionsWithoutSearch: true,
                    initialSelected: initialSelected,
                    onChanged: (option, isSelected) {},
                  ),
                ),
              );
            },
          ),
        );

        // Should auto-expand with initial selections
        await tester.pumpAndSettle();

        // Verify that 4 checkboxes exist
        expect(find.byType(YaruCheckbox), findsNWidgets(4));

        // Verify selected options are shown
        expect(find.text('Option 1'), findsOneWidget);
        expect(find.text('Option 3'), findsOneWidget);
      });

      testWidgets('toggles selection when checkbox is clicked', (tester) async {
        final selectedOptions = <String>{};

        await tester.pumpWidget(
          createWidgetWithAllOptionsMode(
            onChanged: (option, isSelected) {
              if (isSelected) {
                selectedOptions.add(option);
              } else {
                selectedOptions.remove(option);
              }
            },
          ),
        );

        // Expand combobox
        await tester.tap(find.text('All Options Mode (0 selected)'));
        await tester.pumpAndSettle();

        // Verify checkboxes exist
        expect(find.byType(YaruCheckbox), findsNWidgets(4));

        // Select Option 2 by tapping its checkbox
        await tester.tap(find.byType(YaruCheckbox).at(1));
        await tester.pumpAndSettle();

        expect(selectedOptions, contains('Option 2'));
        expect(selectedOptions.length, equals(1));
      });

      testWidgets('allows multiple selections', (tester) async {
        final selectedOptions = <String>{};

        await tester.pumpWidget(
          createWidgetWithAllOptionsMode(
            onChanged: (option, isSelected) {
              if (isSelected) {
                selectedOptions.add(option);
              } else {
                selectedOptions.remove(option);
              }
            },
          ),
        );

        // Expand combobox
        await tester.tap(find.text('All Options Mode (0 selected)'));
        await tester.pumpAndSettle();

        // Select multiple options
        await tester.tap(find.byType(YaruCheckbox).at(0)); // Option 1
        await tester.pumpAndSettle();
        await tester.tap(find.byType(YaruCheckbox).at(2)); // Option 3
        await tester.pumpAndSettle();

        expect(selectedOptions, containsAll(['Option 1', 'Option 3']));
        expect(selectedOptions.length, equals(2));
      });

      testWidgets('deselects when clicking selected checkbox', (tester) async {
        final selectedOptions = {'Option 2'};

        await tester.pumpWidget(
          StatefulBuilder(
            builder: (context, setState) {
              return MaterialApp(
                home: Scaffold(
                  body: MultiSelectCombobox<String>(
                    title: 'Deselect Test',
                    allOptions: testOptions,
                    itemToString: (item) => item,
                    showAllOptionsWithoutSearch: true,
                    initialSelected: selectedOptions,
                    onChanged: (option, isSelected) {
                      setState(() {
                        if (isSelected) {
                          selectedOptions.add(option);
                        } else {
                          selectedOptions.remove(option);
                        }
                      });
                    },
                  ),
                ),
              );
            },
          ),
        );

        // Should auto-expand with initial selections
        await tester.pumpAndSettle();

        // Verify checkboxes exist
        expect(find.byType(YaruCheckbox), findsNWidgets(4));

        // Click Option 2's checkbox to deselect
        await tester.tap(find.byType(YaruCheckbox).at(1));
        await tester.pumpAndSettle();

        expect(selectedOptions, isEmpty);
      });

      testWidgets('updates display count when selections change',
          (tester) async {
        final selectedOptions = <String>{};

        await tester.pumpWidget(
          StatefulBuilder(
            builder: (context, setState) {
              return MaterialApp(
                home: Scaffold(
                  body: MultiSelectCombobox<String>(
                    title: 'Counter Test',
                    allOptions: testOptions,
                    itemToString: (item) => item,
                    showAllOptionsWithoutSearch: true,
                    initialSelected: selectedOptions,
                    onChanged: (option, isSelected) {
                      setState(() {
                        if (isSelected) {
                          selectedOptions.add(option);
                        } else {
                          selectedOptions.remove(option);
                        }
                      });
                    },
                  ),
                ),
              );
            },
          ),
        );

        // Initially shows 0 selected
        expect(find.text('Counter Test (0 selected)'), findsOneWidget);

        // Expand and select an option
        await tester.tap(find.text('Counter Test (0 selected)'));
        await tester.pumpAndSettle();
        await tester.tap(find.byType(YaruCheckbox).first);
        await tester.pumpAndSettle();

        // Collapse to see updated count
        await tester.tap(find.textContaining('Counter Test'));
        await tester.pumpAndSettle();

        expect(find.text('Counter Test (1 selected)'), findsOneWidget);
      });

      testWidgets('works with meta options', (tester) async {
        String? selectedMetaOption;

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: MultiSelectCombobox<String>(
                title: 'Meta Options Test',
                allOptions: testOptions,
                itemToString: (item) => item,
                showAllOptionsWithoutSearch: true,
                metaOptions: const [
                  MetaOption(value: 'any', label: 'Any'),
                  MetaOption(value: 'none', label: 'None'),
                ],
                selectedMetaOption: selectedMetaOption,
                onMetaOptionChanged: (value) {
                  selectedMetaOption = value;
                },
                onChanged: (option, isSelected) {},
              ),
            ),
          ),
        );

        // Expand combobox
        await tester.tap(find.text('Meta Options Test (0 selected)'));
        await tester.pumpAndSettle();

        // Should show meta options
        expect(find.text('Any'), findsOneWidget);
        expect(find.text('None'), findsOneWidget);

        // Should also show all regular options
        expect(find.text('Option 1'), findsOneWidget);
        expect(find.text('Option 2'), findsOneWidget);
      });

      testWidgets('displays all options without pagination', (tester) async {
        final manyOptions = List.generate(5, (i) => 'Option $i');

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: MultiSelectCombobox<String>(
                title: 'Many Options',
                allOptions: manyOptions,
                itemToString: (item) => item,
                showAllOptionsWithoutSearch: true,
                onChanged: (option, isSelected) {},
              ),
            ),
          ),
        );

        // Expand combobox
        await tester.tap(find.text('Many Options (0 selected)'));
        await tester.pumpAndSettle();

        // All 5 checkboxes should be present
        expect(find.byType(YaruCheckbox), findsNWidgets(5));

        // Verify first and last options are visible
        expect(find.text('Option 0'), findsOneWidget);
        expect(find.text('Option 4'), findsOneWidget);
      });
    });
  });
}
