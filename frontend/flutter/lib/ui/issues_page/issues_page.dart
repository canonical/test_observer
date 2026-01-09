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

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/material.dart';
import 'package:yaru/yaru.dart';

import '../../providers/issues.dart';
import '../blocking_provider_preloader.dart';
import '../spacing.dart';
import 'issues_page_body.dart';
import 'issues_page_side_visibility.dart';
import 'issues_page_side.dart';
import 'issues_page_header.dart';

class IssuesPage extends ConsumerWidget {
  const IssuesPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return BlockingProviderPreloader(
      provider: issuesProvider(),
      builder: (_, issues) {
        final showSide = ref.watch(issuesPageSideVisibilityProvider);
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            IssuesPageHeader(title: 'Linked External Issues'),
            const SizedBox(height: Spacing.level4),
            Expanded(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  YaruOptionButton(
                    child: const Icon(Icons.filter_alt),
                    onPressed: () => ref
                        .read(issuesPageSideVisibilityProvider.notifier)
                        .set(!showSide),
                  ),
                  const SizedBox(width: Spacing.level2),
                  Visibility(
                    visible: showSide,
                    maintainState: true,
                    child: IssuesPageSide(
                      searchHint: 'Search issues...',
                    ),
                  ),
                  const SizedBox(width: Spacing.level5),
                  Expanded(child: IssuesPageBody()),
                ],
              ),
            ),
          ],
        );
      },
    );
  }
}
