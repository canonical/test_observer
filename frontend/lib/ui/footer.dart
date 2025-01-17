// Copyright (C) 2024 Canonical Ltd.
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

import 'spacing.dart';
import 'inline_url_text.dart';

class Footer extends StatelessWidget {
  const Footer({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final fontStyle = Theme.of(context).textTheme.labelLarge;

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border(
          top: BorderSide(color: Theme.of(context).colorScheme.outline),
        ),
      ),
      padding: const EdgeInsets.symmetric(
        vertical: Spacing.level5,
        horizontal: Spacing.pageHorizontalPadding,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          InlineUrlText(
            url: 'https://canonical.com/',
            fontStyle: fontStyle,
            urlText: 'Canonical Ltd.',
            leadingText: 'Powered by ',
          ),
          const SizedBox(height: Spacing.level3),
          const InlineUrlText(
            url: 'https://github.com/canonical/test_observer',
            urlText: 'Project source code',
          ),
        ],
      ),
    );
  }
}
