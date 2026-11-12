// Copyright 2026 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter_test/flutter_test.dart';
import 'package:testcase_dashboard/models/stage_name.dart';

void main() {
  test('stageFilterLabel only quotes values colliding with no-stage label', () {
    expect(stageFilterLabel('beta'), 'beta');
    expect(stageFilterLabel(''), '(no stage)');
    expect(stageFilterLabel('(no stage)'), '"(no stage)"');
  });
}
