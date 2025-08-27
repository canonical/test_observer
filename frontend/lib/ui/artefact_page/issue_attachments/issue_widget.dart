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

import '../../../models/issue.dart';
import '../../inline_url_text.dart';
import 'issue_status_chip.dart';
import '../../spacing.dart';

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
          children: [
            // Source (all uppercase, small font, bold)
            Text(
              issue.source.name.toUpperCase(),
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1.2,
                  ),
            ),
            SizedBox(width: Spacing.level3),
            // Project (gray)
            Text(
              issue.project,
              style: Theme.of(context)
                  .textTheme
                  .bodyMedium
                  ?.copyWith(color: Colors.grey),
            ),
            SizedBox(width: Spacing.level3),
            // #key as link
            InlineUrlText(
              url: issue.url,
              urlText: '#${issue.key}',
              fontStyle: Theme.of(context).textTheme.bodyMedium,
            ),
            SizedBox(width: Spacing.level3),
            IssueStatusChip(status: issue.status),
          ],
        ),
        SizedBox(height: Spacing.level3),
        Text(
          (issue.title.isNotEmpty ? issue.title : '[No title]'),
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                color: Theme.of(context).colorScheme.primary,
                decoration: TextDecoration.none,
              ),
        ),
      ],
    );
  }
}
