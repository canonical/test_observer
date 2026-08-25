// Copyright 2026 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter_test/flutter_test.dart';
import 'package:testcase_dashboard/models/attachment_rule_filters.dart';
import 'package:testcase_dashboard/models/test_result.dart';
import 'package:testcase_dashboard/models/test_results_filters.dart';

void main() {
  group('AttachmentRuleFilters', () {
    const filters = AttachmentRuleFilters(
      families: ['snap'],
      artefacts: ['artefact1'],
      artefactVersions: ['1.0'],
      artefactStages: ['beta'],
      artefactTracks: ['latest'],
      environmentNames: ['env1'],
      testPlans: ['plan1'],
      testCaseNames: ['test1'],
      templateIds: ['template1'],
      testResultStatuses: [TestResultStatus.passed],
    );

    group('JSON serialization', () {
      test('serializes all fields to JSON', () {
        final json = filters.toJson();

        expect(json['families'], equals(['snap']));
        expect(json['artefacts'], equals(['artefact1']));
        expect(json['artefact_versions'], equals(['1.0']));
        expect(json['artefact_stages'], equals(['beta']));
        expect(json['artefact_tracks'], equals(['latest']));
        expect(json['environment_names'], equals(['env1']));
        expect(json['test_plans'], equals(['plan1']));
        expect(json['test_case_names'], equals(['test1']));
        expect(json['template_ids'], equals(['template1']));
        expect(json['test_result_statuses'], equals(['PASSED']));
      });

      test('deserializes all fields from JSON', () {
        final restored = AttachmentRuleFilters.fromJson(filters.toJson());

        expect(restored, equals(filters));
      });

      test('deserializes with missing optional fields', () {
        final restored = AttachmentRuleFilters.fromJson({});

        expect(restored.families, equals([]));
        expect(restored.artefactVersions, equals([]));
        expect(restored.artefactStages, equals([]));
        expect(restored.artefactTracks, equals([]));
        expect(restored.testPlans, equals([]));
      });
    });

    group('TestResultsFilters conversion', () {
      test('fromTestResultsFilters copies all matching fields', () {
        const testResultsFilters = TestResultsFilters(
          families: ['snap'],
          artefacts: ['artefact1'],
          artefactVersions: ['1.0'],
          artefactStages: ['beta'],
          artefactTracks: ['latest'],
          environments: ['env1'],
          testPlans: ['plan1'],
          testCases: ['test1'],
          templateIds: ['template1'],
          testResultStatuses: [TestResultStatus.passed],
        );

        final converted = AttachmentRuleFilters.fromTestResultsFilters(
          testResultsFilters,
        );

        expect(converted.families, equals(testResultsFilters.families));
        expect(converted.artefacts, equals(testResultsFilters.artefacts));
        expect(
          converted.artefactVersions,
          equals(testResultsFilters.artefactVersions),
        );
        expect(
          converted.artefactStages,
          equals(testResultsFilters.artefactStages),
        );
        expect(
          converted.artefactTracks,
          equals(testResultsFilters.artefactTracks),
        );
        expect(
          converted.environmentNames,
          equals(testResultsFilters.environments),
        );
        expect(converted.testPlans, equals(testResultsFilters.testPlans));
        expect(converted.testCaseNames, equals(testResultsFilters.testCases));
        expect(
          converted.templateIds,
          equals(testResultsFilters.templateIds),
        );
        expect(
          converted.testResultStatuses,
          equals(testResultsFilters.testResultStatuses),
        );
      });

      test('toTestResultsFilters copies all matching fields back', () {
        final converted = filters.toTestResultsFilters();

        expect(converted.families, equals(filters.families));
        expect(converted.artefacts, equals(filters.artefacts));
        expect(converted.artefactVersions, equals(filters.artefactVersions));
        expect(converted.artefactStages, equals(filters.artefactStages));
        expect(converted.artefactTracks, equals(filters.artefactTracks));
        expect(converted.environments, equals(filters.environmentNames));
        expect(converted.testPlans, equals(filters.testPlans));
        expect(converted.testCases, equals(filters.testCaseNames));
        expect(converted.templateIds, equals(filters.templateIds));
        expect(
          converted.testResultStatuses,
          equals(filters.testResultStatuses),
        );
      });

      test('round-trips through TestResultsFilters without data loss', () {
        final roundTripped = AttachmentRuleFilters.fromTestResultsFilters(
          filters.toTestResultsFilters(),
        );

        expect(roundTripped, equals(filters));
      });

      test('areFiltersCompatible returns true for a round-trippable filter',
          () {
        final testResultsFilters = filters.toTestResultsFilters();

        expect(
          AttachmentRuleFilters.areFiltersCompatible(testResultsFilters),
          isTrue,
        );
      });
    });

    group('hasFilters', () {
      test('returns false for empty filters', () {
        const emptyFilters = AttachmentRuleFilters();
        expect(emptyFilters.hasFilters, isFalse);
      });

      test('returns true when any field is set', () {
        expect(filters.hasFilters, isTrue);
      });

      test('returns true when only testPlans is set', () {
        const testPlanFilters = AttachmentRuleFilters(testPlans: ['plan1']);
        expect(testPlanFilters.hasFilters, isTrue);
      });

      test('returns true when only artefactVersions is set', () {
        const versionFilters = AttachmentRuleFilters(
          artefactVersions: ['1.0'],
        );
        expect(versionFilters.hasFilters, isTrue);
      });
    });
  });
}
