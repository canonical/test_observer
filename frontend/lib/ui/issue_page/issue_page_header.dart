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

import '../../models/issue.dart';
import '../spacing.dart';
import '../issues.dart';

class IssuePageHeader extends StatelessWidget {
  const IssuePageHeader({super.key, required this.issue});

  final Issue issue;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Text(
          'Issue',
          style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
        ),
        const SizedBox(width: Spacing.level5),
        IssueProjectWidget(
          project: issue.project,
          textStyle: Theme.of(context).textTheme.headlineMedium,
        ),
        const SizedBox(width: Spacing.level5),
        IssueLinkWidget(
          issue: issue,
          textStyle: Theme.of(context).textTheme.headlineMedium,
        ),
        const SizedBox(width: Spacing.level5),
        IssueStatusWidget(
          issue: issue,
          textStyle: Theme.of(context).textTheme.headlineSmall,
        ),
      ],
    );
  }
}
