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

import 'package:flutter/material.dart';

import '../../../models/issue.dart';
import '../../spacing.dart';
import '../../issues.dart';

class IssueWidget extends StatelessWidget {
  const IssueWidget({
    super.key,
    required this.issue,
  });

  final Issue issue;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.baseline,
          textBaseline: TextBaseline.alphabetic,
          spacing: Spacing.level3,
          children: [
            IssueSourceWidget(source: issue.source),
            IssueProjectWidget(project: issue.project),
            IssueLinkWidget(issue: issue),
            IssueStatusWidget(issue: issue),
          ],
        ),
        SizedBox(height: Spacing.level3),
        IssueTitleWidget(issue: issue),
      ],
    );
  }
}
