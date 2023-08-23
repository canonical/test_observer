import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher_string.dart';

class InlineUrlText extends StatelessWidget {
  const InlineUrlText({
    super.key,
    this.fontStyle,
    required this.url,
    this.trailingText,
    this.leadingText,
    this.urlText,
  });

  final TextStyle? fontStyle;
  final String url;
  final String? urlText;
  final String? trailingText;
  final String? leadingText;

  @override
  Widget build(BuildContext context) {
    return RichText(
      text: TextSpan(
        style: fontStyle,
        children: [
          if (leadingText != null) TextSpan(text: leadingText),
          TextSpan(
            text: urlText ?? url,
            style: fontStyle?.apply(
              decoration: TextDecoration.underline,
              color: Colors.blue,
            ),
            recognizer: TapGestureRecognizer()
              ..onTap = () => launchUrlString(url),
          ),
          if (trailingText != null) TextSpan(text: trailingText),
        ],
      ),
    );
  }
}
