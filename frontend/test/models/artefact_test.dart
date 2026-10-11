// Copyright 2026 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter_test/flutter_test.dart';
import 'package:testcase_dashboard/models/artefact.dart';
import 'package:testcase_dashboard/models/environment.dart';

void main() {
  test('parses missing expected environments from the API response', () {
    final artefact = Artefact.fromJson({
      'id': 1,
      'name': 'example',
      'version': '1.0',
      'family': 'generic',
      'status': 'UNDECIDED',
      'comment': '',
      'stage': 'beta',
      'all_environment_reviews_count': 0,
      'completed_environment_reviews_count': 0,
      'bug_link': '',
      'missing_expected_environments': [
        {'id': 7, 'name': 'laptop', 'architecture': 'amd64'},
      ],
    });

    expect(
      artefact.missingExpectedEnvironments,
      const [Environment(id: 7, name: 'laptop', architecture: 'amd64')],
    );
  });
}
