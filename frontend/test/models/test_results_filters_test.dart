// Copyright 2025 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter_test/flutter_test.dart';
import 'package:testcase_dashboard/models/execution_metadata.dart';
import 'package:testcase_dashboard/models/test_result.dart';
import 'package:testcase_dashboard/models/test_results_filters.dart';
import 'dart:convert';

void main() {
  group('IntListFilter', () {
    group('JSON serialization', () {
      test('list variant serializes to array', () {
        const filter = IntListFilter.list([1, 2, 3]);
        final json = const IntListFilterConverter().toJson(filter);
        expect(json, equals([1, 2, 3]));
      });

      test('list variant with empty array serializes to empty array', () {
        const filter = IntListFilter.list([]);
        final json = const IntListFilterConverter().toJson(filter);
        expect(json, equals([]));
      });

      test('any variant serializes to "any" string', () {
        const filter = IntListFilter.any();
        final json = const IntListFilterConverter().toJson(filter);
        expect(json, equals('any'));
      });

      test('none variant serializes to "none" string', () {
        const filter = IntListFilter.none();
        final json = const IntListFilterConverter().toJson(filter);
        expect(json, equals('none'));
      });
    });

    group('JSON deserialization', () {
      test('array deserializes to list variant', () {
        final filter = const IntListFilterConverter().fromJson([1, 2, 3]);
        expect(filter.isList, isTrue);
        expect(filter.values, equals([1, 2, 3]));
      });

      test('empty array deserializes to list variant with empty array', () {
        final filter = const IntListFilterConverter().fromJson([]);
        expect(filter.isList, isTrue);
        expect(filter.values, equals([]));
      });

      test('"any" string deserializes to any variant', () {
        final filter = const IntListFilterConverter().fromJson('any');
        expect(filter.isAny, isTrue);
      });

      test('"none" string deserializes to none variant', () {
        final filter = const IntListFilterConverter().fromJson('none');
        expect(filter.isNone, isTrue);
      });

      test('invalid JSON deserializes to empty list variant', () {
        final filter = const IntListFilterConverter().fromJson('invalid');
        expect(filter.isList, isTrue);
        expect(filter.values, equals([]));
      });

      test('null deserializes to empty list variant', () {
        final filter = const IntListFilterConverter().fromJson(null);
        expect(filter.isList, isTrue);
        expect(filter.values, equals([]));
      });
    });

    group('round-trip JSON serialization', () {
      test('list variant round-trips correctly', () {
        const original = IntListFilter.list([5, 10, 15]);
        final json = const IntListFilterConverter().toJson(original);
        final restored = const IntListFilterConverter().fromJson(json);
        expect(restored.values, equals(original.values));
      });

      test('any variant round-trips correctly', () {
        const original = IntListFilter.any();
        final json = const IntListFilterConverter().toJson(original);
        final restored = const IntListFilterConverter().fromJson(json);
        expect(restored.isAny, isTrue);
      });

      test('none variant round-trips correctly', () {
        const original = IntListFilter.none();
        final json = const IntListFilterConverter().toJson(original);
        final restored = const IntListFilterConverter().fromJson(json);
        expect(restored.isNone, isTrue);
      });
    });

    group('query params', () {
      test('fromQueryParam parses comma-separated integers', () {
        final filter = IntListFilter.fromQueryParam(['1', '2', '3']);
        expect(filter.isList, isTrue);
        expect(filter.values, equals([1, 2, 3]));
      });

      test('fromQueryParam parses "any" keyword', () {
        final filter = IntListFilter.fromQueryParam(['any']);
        expect(filter.isAny, isTrue);
      });

      test('fromQueryParam parses "none" keyword', () {
        final filter = IntListFilter.fromQueryParam(['none']);
        expect(filter.isNone, isTrue);
      });

      test('fromQueryParam handles empty list', () {
        final filter = IntListFilter.fromQueryParam([]);
        expect(filter.isList, isTrue);
        expect(filter.values, equals([]));
      });

      test('fromQueryParam filters out non-integers', () {
        final filter = IntListFilter.fromQueryParam(['1', 'invalid', '2']);
        expect(filter.values, equals([1, 2]));
      });

      test('toQueryParam converts list to string list', () {
        const filter = IntListFilter.list([1, 2, 3]);
        expect(filter.toQueryParam(), equals(['1', '2', '3']));
      });

      test('toQueryParam converts any to ["any"]', () {
        const filter = IntListFilter.any();
        expect(filter.toQueryParam(), equals(['any']));
      });

      test('toQueryParam converts none to ["none"]', () {
        const filter = IntListFilter.none();
        expect(filter.toQueryParam(), equals(['none']));
      });

      test('toQueryParam returns empty for empty list', () {
        const filter = IntListFilter.list([]);
        expect(filter.toQueryParam(), equals([]));
      });
    });

    group('helper methods', () {
      test('values returns list for list variant', () {
        const filter = IntListFilter.list([1, 2, 3]);
        expect(filter.values, equals([1, 2, 3]));
      });

      test('values returns empty for any variant', () {
        const filter = IntListFilter.any();
        expect(filter.values, equals([]));
      });

      test('values returns empty for none variant', () {
        const filter = IntListFilter.none();
        expect(filter.values, equals([]));
      });

      test('isAny returns true only for any variant', () {
        expect(const IntListFilter.any().isAny, isTrue);
        expect(const IntListFilter.none().isAny, isFalse);
        expect(const IntListFilter.list([]).isAny, isFalse);
      });

      test('isNone returns true only for none variant', () {
        expect(const IntListFilter.none().isNone, isTrue);
        expect(const IntListFilter.any().isNone, isFalse);
        expect(const IntListFilter.list([]).isNone, isFalse);
      });

      test('isList returns true only for list variant', () {
        expect(const IntListFilter.list([]).isList, isTrue);
        expect(const IntListFilter.any().isList, isFalse);
        expect(const IntListFilter.none().isList, isFalse);
      });

      test('isNotEmpty returns true for any variant', () {
        expect(const IntListFilter.any().isNotEmpty, isTrue);
      });

      test('isNotEmpty returns true for none variant', () {
        expect(const IntListFilter.none().isNotEmpty, isTrue);
      });

      test('isNotEmpty returns true for non-empty list', () {
        expect(const IntListFilter.list([1]).isNotEmpty, isTrue);
      });

      test('isNotEmpty returns false for empty list', () {
        expect(const IntListFilter.list([]).isNotEmpty, isFalse);
      });

      test('isEmpty is opposite of isNotEmpty', () {
        expect(const IntListFilter.any().isEmpty, isFalse);
        expect(const IntListFilter.none().isEmpty, isFalse);
        expect(const IntListFilter.list([1]).isEmpty, isFalse);
        expect(const IntListFilter.list([]).isEmpty, isTrue);
      });
    });
  });

  group('TestResultsFilters', () {
    group('JSON serialization', () {
      test('serializes all fields correctly', () {
        final filters = TestResultsFilters(
          families: ['family1', 'family2'],
          testResultStatuses: [
            TestResultStatus.passed,
            TestResultStatus.failed,
          ],
          artefacts: ['artefact1'],
          environments: ['env1'],
          testCases: ['test1', 'test2'],
          templateIds: ['template1'],
          executionMetadata: ExecutionMetadata(
            data: {
              'key': {'value1', 'value2'},
            },
          ),
          issues: const IntListFilter.list([1, 2]),
          assignees: const IntListFilter.any(),
          fromDate: DateTime.utc(2024, 1, 1),
          untilDate: DateTime.utc(2024, 12, 31),
          offset: 10,
          limit: 50,
        );

        final json = filters.toJson();

        expect(json['families'], equals(['family1', 'family2']));
        expect(json['test_result_statuses'], equals(['PASSED', 'FAILED']));
        expect(json['artefacts'], equals(['artefact1']));
        expect(json['environments'], equals(['env1']));
        expect(json['test_cases'], equals(['test1', 'test2']));
        expect(json['template_ids'], equals(['template1']));
        expect(json['execution_metadata'], isA<Map>());
        expect(json['issues'], equals([1, 2]));
        expect(json['assignees'], equals('any'));
        expect(json['from_date'], equals('2024-01-01T00:00:00.000Z'));
        expect(json['until_date'], equals('2024-12-31T00:00:00.000Z'));
        expect(json['offset'], equals(10));
        expect(json['limit'], equals(50));
      });

      test('serializes IntListFilter variants correctly in JSON', () {
        final filtersWithList = TestResultsFilters(
          issues: const IntListFilter.list([1, 2, 3]),
          assignees: const IntListFilter.list([4, 5]),
        );
        final jsonList = filtersWithList.toJson();
        expect(jsonList['issues'], equals([1, 2, 3]));
        expect(jsonList['assignees'], equals([4, 5]));

        final filtersWithAny = TestResultsFilters(
          issues: const IntListFilter.any(),
          assignees: const IntListFilter.none(),
        );
        final jsonAny = filtersWithAny.toJson();
        expect(jsonAny['issues'], equals('any'));
        expect(jsonAny['assignees'], equals('none'));
      });

      test('omits default values', () {
        const filters = TestResultsFilters();
        final json = filters.toJson();

        // Check that empty lists are present (Freezed default behavior)
        expect(json['families'], isNotNull);
        expect(json['test_result_statuses'], isNotNull);
        expect(json['artefacts'], isNotNull);
        // Null fields are included in JSON by Freezed (with null values)
        expect(json.containsKey('from_date'), isTrue);
        expect(json['from_date'], isNull);
        expect(json.containsKey('offset'), isTrue);
        expect(json['offset'], isNull);
      });
    });

    group('JSON deserialization', () {
      test('deserializes all fields correctly', () {
        final json = {
          'families': ['family1'],
          'test_result_statuses': ['PASSED'],
          'artefacts': ['artefact1'],
          'environments': ['env1'],
          'test_cases': ['test1'],
          'template_ids': ['template1'],
          'execution_metadata': {
            'key': ['value1', 'value2'],
          },
          'issues': [1, 2, 3],
          'assignees': 'any',
          'from_date': '2024-01-01T00:00:00.000Z',
          'until_date': '2024-12-31T00:00:00.000Z',
          'offset': 10,
          'limit': 50,
        };

        final filters = TestResultsFilters.fromJson(json);

        expect(filters.families, equals(['family1']));
        expect(filters.testResultStatuses, equals([TestResultStatus.passed]));
        expect(filters.artefacts, equals(['artefact1']));
        expect(filters.environments, equals(['env1']));
        expect(filters.testCases, equals(['test1']));
        expect(filters.templateIds, equals(['template1']));
        expect(filters.executionMetadata.data, isA<Map<String, Set<String>>>());
        expect(filters.issues.values, equals([1, 2, 3]));
        expect(filters.assignees.isAny, isTrue);
        expect(filters.fromDate, equals(DateTime.utc(2024, 1, 1)));
        expect(filters.untilDate, equals(DateTime.utc(2024, 12, 31)));
        expect(filters.offset, equals(10));
        expect(filters.limit, equals(50));
      });

      test('deserializes IntListFilter variants correctly', () {
        final jsonWithList = {
          'issues': [1, 2],
          'assignees': [],
        };
        final filtersWithList = TestResultsFilters.fromJson(jsonWithList);
        expect(filtersWithList.issues.values, equals([1, 2]));
        expect(filtersWithList.assignees.values, equals([]));

        final jsonWithKeywords = {'issues': 'any', 'assignees': 'none'};
        final filtersWithKeywords =
            TestResultsFilters.fromJson(jsonWithKeywords);
        expect(filtersWithKeywords.issues.isAny, isTrue);
        expect(filtersWithKeywords.assignees.isNone, isTrue);
      });

      test('handles missing optional fields', () {
        final json = <String, dynamic>{};
        final filters = TestResultsFilters.fromJson(json);

        expect(filters.families, equals([]));
        expect(filters.issues.values, equals([]));
        expect(filters.fromDate, isNull);
        expect(filters.offset, isNull);
      });
    });

    group('round-trip JSON serialization', () {
      test('preserves all data through serialization cycle', () {
        final original = TestResultsFilters(
          families: ['family1'],
          testResultStatuses: [TestResultStatus.passed],
          artefacts: ['artefact1'],
          environments: ['env1'],
          testCases: ['test1'],
          templateIds: ['template1'],
          executionMetadata: ExecutionMetadata(
            data: {
              'key': {'value'},
            },
          ),
          issues: const IntListFilter.list([1, 2, 3]),
          assignees: const IntListFilter.none(),
          fromDate: DateTime.utc(2024, 1, 1),
          untilDate: DateTime.utc(2024, 12, 31),
          offset: 10,
          limit: 50,
        );

        final json = original.toJson();
        final restored = TestResultsFilters.fromJson(json);

        expect(restored, equals(original));
      });
    });

    group('query params conversion', () {
      test('fromQueryParams parses all parameters', () {
        final params = {
          'families': ['family1,family2'],
          'test_result_statuses': ['PASSED,FAILED'],
          'artefacts': ['artefact1'],
          'environments': ['env1,env2'],
          'test_cases': ['test1'],
          'template_ids': ['template1,template2'],
          'execution_metadata': [
            '${base64Encode(utf8.encode('key'))}:${base64Encode(utf8.encode('value'))}',
          ],
          'issues': ['1,2,3'],
          'assignee_ids': ['any'],
          'from_date': ['2024-01-01T00:00:00.000Z'],
          'until_date': ['2024-12-31T00:00:00.000Z'],
          'offset': ['10'],
          'limit': ['50'],
        };

        final filters = TestResultsFilters.fromQueryParams(params);

        expect(filters.families, equals(['family1', 'family2']));
        expect(
          filters.testResultStatuses,
          equals([TestResultStatus.passed, TestResultStatus.failed]),
        );
        expect(filters.artefacts, equals(['artefact1']));
        expect(filters.environments, equals(['env1', 'env2']));
        expect(filters.testCases, equals(['test1']));
        expect(filters.templateIds, equals(['template1', 'template2']));
        expect(filters.issues.values, equals([1, 2, 3]));
        expect(filters.assignees.isAny, isTrue);
        expect(filters.fromDate, equals(DateTime.utc(2024, 1, 1)));
        expect(filters.untilDate, equals(DateTime.utc(2024, 12, 31)));
        expect(filters.offset, equals(10));
        expect(filters.limit, equals(50));
      });

      test('fromQueryParams handles IntListFilter variants', () {
        final paramsWithList = {
          'issues': ['1,2,3'],
          'assignee_ids': ['4,5'],
        };
        final filtersWithList =
            TestResultsFilters.fromQueryParams(paramsWithList);
        expect(filtersWithList.issues.values, equals([1, 2, 3]));
        expect(filtersWithList.assignees.values, equals([4, 5]));

        final paramsWithKeywords = {
          'issues': ['any'],
          'assignee_ids': ['none'],
        };
        final filtersWithKeywords =
            TestResultsFilters.fromQueryParams(paramsWithKeywords);
        expect(filtersWithKeywords.issues.isAny, isTrue);
        expect(filtersWithKeywords.assignees.isNone, isTrue);
      });

      test('fromQueryParams handles empty params', () {
        final filters = TestResultsFilters.fromQueryParams({});
        expect(filters.families, equals([]));
        expect(filters.issues.values, equals([]));
        expect(filters.fromDate, isNull);
      });

      test('fromQueryParams trims and filters empty strings', () {
        final params = {
          'families': ['  family1  ,  ,family2  '],
        };
        final filters = TestResultsFilters.fromQueryParams(params);
        expect(filters.families, equals(['family1', 'family2']));
      });

      test('toQueryParams creates correct map', () {
        final filters = TestResultsFilters(
          families: ['family1', 'family2'],
          testResultStatuses: [TestResultStatus.passed],
          artefacts: ['artefact1'],
          environments: ['env1'],
          testCases: ['test1'],
          templateIds: ['template1'],
          executionMetadata: ExecutionMetadata(
            data: {
              'key': {'value'},
            },
          ),
          issues: const IntListFilter.list([1, 2]),
          assignees: const IntListFilter.any(),
          fromDate: DateTime.utc(2024, 1, 1),
          untilDate: DateTime.utc(2024, 12, 31),
          offset: 10,
          limit: 50,
        );

        final params = filters.toQueryParams();

        expect(params['families'], equals(['family1', 'family2']));
        expect(params['test_result_statuses'], equals(['PASSED']));
        expect(params['artefacts'], equals(['artefact1']));
        expect(params['environments'], equals(['env1']));
        expect(params['test_cases'], equals(['test1']));
        expect(params['template_ids'], equals(['template1']));
        expect(
          params['execution_metadata'],
          equals([
            '${base64Encode(utf8.encode('key'))}:${base64Encode(utf8.encode('value'))}',
          ]),
        );
        expect(params['issues'], equals(['1', '2']));
        expect(params['assignee_ids'], equals(['any']));
        expect(params['from_date'], equals(['2024-01-01T00:00:00.000Z']));
        expect(params['until_date'], equals(['2024-12-31T00:00:00.000Z']));
        expect(params['offset'], equals(['10']));
        expect(params['limit'], equals(['50']));
      });

      test('toQueryParams omits empty collections', () {
        const filters = TestResultsFilters();
        final params = filters.toQueryParams();

        expect(params.containsKey('families'), isFalse);
        expect(params.containsKey('test_result_statuses'), isFalse);
        expect(params.containsKey('issues'), isFalse);
        expect(params.containsKey('from_date'), isFalse);
      });

      test('toQueryParams handles IntListFilter variants', () {
        final filtersWithList = TestResultsFilters(
          issues: const IntListFilter.list([1, 2]),
          assignees: const IntListFilter.list([]),
        );
        final paramsWithList = filtersWithList.toQueryParams();
        expect(paramsWithList['issues'], equals(['1', '2']));
        expect(
          paramsWithList.containsKey('assignee_ids'),
          isFalse,
        ); // empty list

        final filtersWithKeywords = TestResultsFilters(
          issues: const IntListFilter.any(),
          assignees: const IntListFilter.none(),
        );
        final paramsWithKeywords = filtersWithKeywords.toQueryParams();
        expect(paramsWithKeywords['issues'], equals(['any']));
        expect(paramsWithKeywords['assignee_ids'], equals(['none']));
      });
    });

    group('round-trip query params conversion', () {
      test('preserves data through query params cycle', () {
        final original = TestResultsFilters(
          families: ['family1', 'family2'],
          testResultStatuses: [
            TestResultStatus.passed,
            TestResultStatus.failed,
          ],
          artefacts: ['artefact1'],
          environments: ['env1'],
          testCases: ['test1'],
          templateIds: ['template1'],
          executionMetadata: ExecutionMetadata(
            data: {
              'key': {'value'},
            },
          ),
          issues: const IntListFilter.list([1, 2, 3]),
          assignees: const IntListFilter.none(),
          fromDate: DateTime.utc(2024, 1, 1),
          untilDate: DateTime.utc(2024, 12, 31),
          offset: 10,
          limit: 50,
        );

        final params = original.toQueryParams();
        final restored = TestResultsFilters.fromQueryParams(params);

        expect(restored.families, equals(original.families));
        expect(
          restored.testResultStatuses,
          equals(original.testResultStatuses),
        );
        expect(restored.artefacts, equals(original.artefacts));
        expect(restored.environments, equals(original.environments));
        expect(restored.testCases, equals(original.testCases));
        expect(restored.templateIds, equals(original.templateIds));
        expect(
          restored.executionMetadata.data,
          equals(original.executionMetadata.data),
        );
        expect(restored.issues.values, equals(original.issues.values));
        expect(restored.assignees.isNone, equals(original.assignees.isNone));
        expect(restored.fromDate, equals(original.fromDate));
        expect(restored.untilDate, equals(original.untilDate));
        expect(restored.offset, equals(original.offset));
        expect(restored.limit, equals(original.limit));
      });
    });

    group('hasFilters', () {
      test('returns false for empty filters', () {
        const filters = TestResultsFilters();
        expect(filters.hasFilters, isFalse);
      });

      test('returns true when families is not empty', () {
        const filters = TestResultsFilters(families: ['family1']);
        expect(filters.hasFilters, isTrue);
      });

      test('returns true when testResultStatuses is not empty', () {
        const filters = TestResultsFilters(
          testResultStatuses: [TestResultStatus.passed],
        );
        expect(filters.hasFilters, isTrue);
      });

      test('returns true when artefacts is not empty', () {
        const filters = TestResultsFilters(artefacts: ['artefact1']);
        expect(filters.hasFilters, isTrue);
      });

      test('returns true when environments is not empty', () {
        const filters = TestResultsFilters(environments: ['env1']);
        expect(filters.hasFilters, isTrue);
      });

      test('returns true when testCases is not empty', () {
        const filters = TestResultsFilters(testCases: ['test1']);
        expect(filters.hasFilters, isTrue);
      });

      test('returns true when templateIds is not empty', () {
        const filters = TestResultsFilters(templateIds: ['template1']);
        expect(filters.hasFilters, isTrue);
      });

      test('returns true when executionMetadata is not empty', () {
        final filters = TestResultsFilters(
          executionMetadata: ExecutionMetadata(
            data: {
              'key': {'value'},
            },
          ),
        );
        expect(filters.hasFilters, isTrue);
      });

      test('returns true when issues is any', () {
        const filters = TestResultsFilters(issues: IntListFilter.any());
        expect(filters.hasFilters, isTrue);
      });

      test('returns true when issues is none', () {
        const filters = TestResultsFilters(issues: IntListFilter.none());
        expect(filters.hasFilters, isTrue);
      });

      test('returns false when issues is empty list', () {
        const filters = TestResultsFilters(issues: IntListFilter.list([]));
        expect(filters.hasFilters, isFalse);
      });

      test('returns true when issues has values', () {
        const filters = TestResultsFilters(issues: IntListFilter.list([1]));
        expect(filters.hasFilters, isTrue);
      });

      test('returns true when assignees is any', () {
        const filters = TestResultsFilters(assignees: IntListFilter.any());
        expect(filters.hasFilters, isTrue);
      });

      test('returns true when assignees is none', () {
        const filters = TestResultsFilters(assignees: IntListFilter.none());
        expect(filters.hasFilters, isTrue);
      });

      test('returns true when fromDate is set', () {
        final filters = TestResultsFilters(fromDate: DateTime.utc(2024, 1, 1));
        expect(filters.hasFilters, isTrue);
      });

      test('returns true when untilDate is set', () {
        final filters =
            TestResultsFilters(untilDate: DateTime.utc(2024, 12, 31));
        expect(filters.hasFilters, isTrue);
      });

      test('returns false when only offset is set', () {
        const filters = TestResultsFilters(offset: 10);
        expect(filters.hasFilters, isFalse);
      });

      test('returns false when only limit is set', () {
        const filters = TestResultsFilters(limit: 50);
        expect(filters.hasFilters, isFalse);
      });
    });

    group('toTestResultsUri', () {
      test('creates URI with correct path', () {
        const filters = TestResultsFilters();
        final uri = filters.toTestResultsUri();
        expect(uri.path, equals('/test-results'));
      });

      test('creates URI with query parameters', () {
        const filters = TestResultsFilters(
          families: ['family1', 'family2'],
          issues: IntListFilter.list([1, 2]),
        );
        final uri = filters.toTestResultsUri();
        expect(uri.queryParameters['families'], equals('family1,family2'));
        expect(uri.queryParameters['issues'], equals('1,2'));
      });

      test('creates URI with IntListFilter variants', () {
        const filters = TestResultsFilters(
          issues: IntListFilter.any(),
          assignees: IntListFilter.none(),
        );
        final uri = filters.toTestResultsUri();
        expect(uri.queryParameters['issues'], equals('any'));
        expect(uri.queryParameters['assignee_ids'], equals('none'));
      });
    });
  });
}
