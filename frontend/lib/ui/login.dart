// Copyright 2026 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher_string.dart';

import '../providers/api.dart';

class LoginPromptPage extends StatelessWidget {
  const LoginPromptPage({super.key, this.returnTo});

  final String? returnTo;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 420),
          child: Card(
            margin: const EdgeInsets.all(24),
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Login required',
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'You need to log in before accessing this page.',
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 24),
                  FilledButton(
                    onPressed: () {
                      final uri = Uri.parse(apiUrl);
                      final target = _resolvedReturnTo();
                      final loginUri = uri.replace(
                        path: '/v1/auth/saml/login',
                        queryParameters: {'return_to': target},
                      );

                      launchUrlString(
                        loginUri.toString(),
                        webOnlyWindowName: '_self',
                      );
                    },
                    child: const Text('Log in'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  String _resolvedReturnTo() {
    final localPath =
        returnTo != null && returnTo!.startsWith('/') ? returnTo! : '/';
    return buildFrontendReturnToUrl(
      baseUri: Uri.base,
      localPath: localPath,
    );
  }
}

String buildFrontendReturnToUrl({
  required Uri baseUri,
  required String localPath,
}) {
  final normalizedPath = localPath.startsWith('/') ? localPath : '/';

  // Flutter web uses hash URLs by default (e.g. /#/route). In that case,
  // return_to must keep the destination inside the fragment.
  if (baseUri.fragment.startsWith('/')) {
    return baseUri
        .replace(path: '/', queryParameters: null, fragment: normalizedPath)
        .toString();
  }

  return baseUri.resolve(normalizedPath).toString();
}
