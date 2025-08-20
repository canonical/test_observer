// lib/ui/test_results_page/test_result_helpers.dart

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
import 'package:url_launcher/url_launcher.dart';

import '../../models/test_result.dart';

class TestResultHelpers {
  static TestResultStatus parseTestResultStatus(String? status) {
    switch (status?.toUpperCase()) {
      case 'PASSED':
        return TestResultStatus.passed;
      case 'FAILED':
        return TestResultStatus.failed;
      case 'SKIPPED':
        return TestResultStatus.skipped;
      default:
        return TestResultStatus.failed;
    }
  }

  static Widget getStatusIcon(TestResultStatus status) {
    return status.getIcon();
  }

  static String formatDate(String? dateStr) {
    if (dateStr == null) return '';
    try {
      final date = DateTime.parse(dateStr);
      return '${date.day.toString().padLeft(2, '0')}/${date.month.toString().padLeft(2, '0')}/${date.year.toString().substring(2)}';
    } catch (e) {
      return '';
    }
  }

  static String formatFullDate(String? dateStr) {
    if (dateStr == null) return 'N/A';
    try {
      final date = DateTime.parse(dateStr);
      return '${date.day}/${date.month}/${date.year} ${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
    } catch (e) {
      return dateStr;
    }
  }

  static void navigateToTestExecution(Map<String, dynamic> result) {
    final testExecution = result['test_execution'] as Map<String, dynamic>;
    final artefact = result['artefact'] as Map<String, dynamic>;
    final environment = testExecution['environment'] as Map<String, dynamic>?;

    final family = artefact['family'] as String? ?? '';
    final artefactId = artefact['id'] as int? ?? 0;
    final testPlan =
        (testExecution['test_plan'] as String?)?.trim().isNotEmpty == true
            ? testExecution['test_plan']
            : 'unknown'; // there exists test results without test plans

    final environmentName = environment?['name'] as String? ?? '';

    final currentUri = Uri.base;
    final baseUrl =
        '${currentUri.scheme}://${currentUri.host}:${currentUri.port}';

    final encodedTestPlan = Uri.encodeQueryComponent(testPlan);
    final encodedEnvironment = Uri.encodeQueryComponent(environmentName);
    final linkUrl =
        '$baseUrl/#/${family}s/$artefactId?Test+plan=$encodedTestPlan&Environment=$encodedEnvironment';

    _launchUrl(linkUrl);
  }

  static void _launchUrl(String url) async {
    final uri = Uri.parse(url);
    await launchUrl(
      uri,
      mode: LaunchMode.externalApplication,
    );
  }
}
