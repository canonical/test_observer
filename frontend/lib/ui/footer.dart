import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher_string.dart';

import 'spacing.dart';

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
          RichText(
            text: TextSpan(
              style: fontStyle,
              children: [
                const TextSpan(text: 'Powered by '),
                TextSpan(
                  text: 'Canonical Ltd.',
                  style: fontStyle?.apply(
                    decoration: TextDecoration.underline,
                    color: Colors.blue,
                  ),
                  recognizer: TapGestureRecognizer()
                    ..onTap = () => launchUrlString('https://canonical.com/'),
                ),
              ],
            ),
          ),
          const SizedBox(height: Spacing.level3),
          GestureDetector(
            onTap: () =>
                launchUrlString('https://github.com/canonical/test_observer'),
            child: Text(
              'Project source code',
              style: fontStyle,
            ),
          ),
        ],
      ),
    );
  }
}
