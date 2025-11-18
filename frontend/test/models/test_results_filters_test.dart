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

import 'package:test/test.dart';
import 'package:testcase_dashboard/models/test_results_filters.dart';

void main() {
  group('IssuesFilter', () {
    group('factory constructors', () {
      test('list creates a filter with issue IDs', () {
        const filter = IssuesFilter.list([1, 2, 3]);
        expect(filter.isList, isTrue);
        expect(filter.issuesList, equals([1, 2, 3]));
      });

      test('any creates a filter for any issues', () {
        const filter = IssuesFilter.any();
        expect(filter.isAny, isTrue);
        expect(filter.issuesList, isEmpty);
      });

      test('none creates a filter for no issues', () {
        const filter = IssuesFilter.none();
        expect(filter.isNone, isTrue);
        expect(filter.issuesList, isEmpty);
      });

      test('list can be created with an empty list', () {
        const filter = IssuesFilter.list([]);
        expect(filter.isList, isTrue);
        expect(filter.issuesList, isEmpty);
      });
    });

    group('helper getters', () {
      test('issuesList returns issues for list filter', () {
        const filter = IssuesFilter.list([10, 20, 30]);
        expect(filter.issuesList, equals([10, 20, 30]));
      });

      test('issuesList returns empty list for any filter', () {
        const filter = IssuesFilter.any();
        expect(filter.issuesList, isEmpty);
      });

      test('issuesList returns empty list for none filter', () {
        const filter = IssuesFilter.none();
        expect(filter.issuesList, isEmpty);
      });

      test('isAny returns true only for any filter', () {
        expect(const IssuesFilter.any().isAny, isTrue);
        expect(const IssuesFilter.none().isAny, isFalse);
        expect(const IssuesFilter.list([1]).isAny, isFalse);
      });

      test('isNone returns true only for none filter', () {
        expect(const IssuesFilter.none().isNone, isTrue);
        expect(const IssuesFilter.any().isNone, isFalse);
        expect(const IssuesFilter.list([1]).isNone, isFalse);
      });

      test('isList returns true only for list filter', () {
        expect(const IssuesFilter.list([1]).isList, isTrue);
        expect(const IssuesFilter.list([]).isList, isTrue);
        expect(const IssuesFilter.any().isList, isFalse);
        expect(const IssuesFilter.none().isList, isFalse);
      });
    });

    group('JSON serialization', () {
      test('list filter serializes to JSON', () {
        const filter = IssuesFilter.list([1, 2, 3]);
        final json = filter.toJson();
        expect(json, contains('runtimeType'));
        expect(json, contains('issues'));
      });

      test('any filter serializes to JSON', () {
        const filter = IssuesFilter.any();
        final json = filter.toJson();
        expect(json, contains('runtimeType'));
      });

      test('none filter serializes to JSON', () {
        const filter = IssuesFilter.none();
        final json = filter.toJson();
        expect(json, contains('runtimeType'));
      });

      test('list filter deserializes from JSON', () {
        const original = IssuesFilter.list([4, 5, 6]);
        final json = original.toJson();
        final deserialized = IssuesFilter.fromJson(json);
        expect(deserialized, equals(original));
        expect(deserialized.issuesList, equals([4, 5, 6]));
      });

      test('any filter deserializes from JSON', () {
        const original = IssuesFilter.any();
        final json = original.toJson();
        final deserialized = IssuesFilter.fromJson(json);
        expect(deserialized, equals(original));
        expect(deserialized.isAny, isTrue);
      });

      test('none filter deserializes from JSON', () {
        const original = IssuesFilter.none();
        final json = original.toJson();
        final deserialized = IssuesFilter.fromJson(json);
        expect(deserialized, equals(original));
        expect(deserialized.isNone, isTrue);
      });

      test('round-trip serialization preserves list filter', () {
        const original = IssuesFilter.list([100, 200, 300]);
        final json = original.toJson();
        final deserialized = IssuesFilter.fromJson(json);
        expect(deserialized, equals(original));
      });

      test('round-trip serialization preserves any filter', () {
        const original = IssuesFilter.any();
        final json = original.toJson();
        final deserialized = IssuesFilter.fromJson(json);
        expect(deserialized, equals(original));
      });

      test('round-trip serialization preserves none filter', () {
        const original = IssuesFilter.none();
        final json = original.toJson();
        final deserialized = IssuesFilter.fromJson(json);
        expect(deserialized, equals(original));
      });
    });

    group('equality', () {
      test('list filters with same issues are equal', () {
        const filter1 = IssuesFilter.list([1, 2, 3]);
        const filter2 = IssuesFilter.list([1, 2, 3]);
        expect(filter1, equals(filter2));
      });

      test('list filters with different issues are not equal', () {
        const filter1 = IssuesFilter.list([1, 2, 3]);
        const filter2 = IssuesFilter.list([4, 5, 6]);
        expect(filter1, isNot(equals(filter2)));
      });

      test('any filters are equal', () {
        const filter1 = IssuesFilter.any();
        const filter2 = IssuesFilter.any();
        expect(filter1, equals(filter2));
      });

      test('none filters are equal', () {
        const filter1 = IssuesFilter.none();
        const filter2 = IssuesFilter.none();
        expect(filter1, equals(filter2));
      });

      test('different filter types are not equal', () {
        const listFilter = IssuesFilter.list([1]);
        const anyFilter = IssuesFilter.any();
        const noneFilter = IssuesFilter.none();

        expect(listFilter, isNot(equals(anyFilter)));
        expect(listFilter, isNot(equals(noneFilter)));
        expect(anyFilter, isNot(equals(noneFilter)));
      });
    });
  });
}
