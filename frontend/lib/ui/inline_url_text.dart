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
    final fontStyle = this.fontStyle ??
        DefaultTextStyle.of(context).style.apply(
              decoration: TextDecoration.underline,
              color: Colors.blue,
            );

    return RichText(
      text: TextSpan(
        style: fontStyle,
        children: [
          if (leadingText != null) TextSpan(text: leadingText),
          TextSpan(
            text: urlText ?? url,
            style: fontStyle,
            recognizer: TapGestureRecognizer()
              ..onTap = () => launchUrlString(url),
          ),
          if (trailingText != null) TextSpan(text: trailingText),
        ],
      ),
    );
  }
}
