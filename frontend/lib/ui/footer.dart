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
