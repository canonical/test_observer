// Copyright 2023 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2023 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter/material.dart';
import 'package:url_launcher/link.dart';

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
    final resolvedFontStyle = fontStyle ??
        DefaultTextStyle.of(context).style.apply(
              decoration: TextDecoration.underline,
              color: Colors.blue,
            );

    final parsedUri = Uri.parse(url);
    final resolvedUri =
        parsedUri.isAbsolute ? parsedUri : Uri.base.resolveUri(parsedUri);

    final linkWidget = Link(
      uri: resolvedUri,
      target: LinkTarget.blank,
      builder: (context, followLink) => GestureDetector(
        onTap: followLink,
        child: Text(urlText ?? url, style: resolvedFontStyle),
      ),
    );

    if (leadingText == null && trailingText == null) {
      return linkWidget;
    }

    return RichText(
      text: TextSpan(
        style: resolvedFontStyle,
        children: [
          if (leadingText != null) TextSpan(text: leadingText),
          WidgetSpan(child: linkWidget),
          if (trailingText != null) TextSpan(text: trailingText),
        ],
      ),
    );
  }
}
