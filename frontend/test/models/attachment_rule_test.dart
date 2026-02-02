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

import 'package:flutter_test/flutter_test.dart';
import 'package:testcase_dashboard/models/attachment_rule.dart';
import 'package:testcase_dashboard/models/execution_metadata.dart';
import 'dart:convert';

void main() {
  group('AttachmentRule', () {
    group('JSON serialization', () {
      test('deserializes with auto_rerun_on_attach field', () {
        final json = {
          'id': 1,
          'enabled': true,
          'auto_rerun_on_attach': true,
          'families': ['snap'],
          'environment_names': ['laptop'],
          'test_case_names': ['test-1'],
          'template_ids': ['template-1'],
          'test_result_statuses': ['FAILED'],
          'execution_metadata': {'category': ['value']},
        };

        final rule = AttachmentRule.fromJson(json);

        expect(rule.id, equals(1));
        expect(rule.enabled, isTrue);
        expect(rule.autoRerunOnAttach, isTrue);
        expect(rule.families, equals(['snap']));
        expect(rule.environmentNames, equals(['laptop']));
      });

      test('deserializes with auto_rerun_on_attach false', () {
        final json = {
          'id': 1,
          'enabled': true,
          'auto_rerun_on_attach': false,
          'families': [],
          'environment_names': [],
          'test_case_names': [],
          'template_ids': [],
          'test_result_statuses': [],
          'execution_metadata': {},
        };

        final rule = AttachmentRule.fromJson(json);

        expect(rule.autoRerunOnAttach, isFalse);
      });

      test('defaults auto_rerun_on_attach to false when missing', () {
        final json = {
          'id': 1,
          'enabled': true,
          'families': [],
          'environment_names': [],
          'test_case_names': [],
          'template_ids': [],
          'test_result_statuses': [],
          'execution_metadata': {},
        };

        final rule = AttachmentRule.fromJson(json);

        expect(rule.autoRerunOnAttach, isFalse);
      });

      test('serializes auto_rerun_on_attach field', () {
        final rule = AttachmentRule(
          id: 1,
          enabled: true,
          autoRerunOnAttach: true,
          families: [],
          environmentNames: [],
          testCaseNames: [],
          templateIds: [],
          testResultStatuses: [],
          executionMetadata: const ExecutionMetadata(),
        );

        final json = rule.toJson();

        expect(json['auto_rerun_on_attach'], isTrue);
      });
    });

    group('copyWith', () {
      test('copies with auto_rerun_on_attach changed', () {
        final original = AttachmentRule(
          id: 1,
          enabled: true,
          autoRerunOnAttach: false,
          families: [],
          environmentNames: [],
          testCaseNames: [],
          templateIds: [],
          testResultStatuses: [],
          executionMetadata: const ExecutionMetadata(),
        );

        final updated = original.copyWith(autoRerunOnAttach: true);

        expect(updated.autoRerunOnAttach, isTrue);
        expect(updated.enabled, isTrue);
        expect(updated.id, equals(1));
      });
    });
  });
}
