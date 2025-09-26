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

import '../../../../routing.dart';

class IssueUrlSection extends StatefulWidget {
  const IssueUrlSection({super.key, this.onChanged, this.initialValue});

  final ValueChanged<String>? onChanged;
  final String? initialValue;

  @override
  State<IssueUrlSection> createState() => _IssueUrlSectionState();
}

class _IssueUrlSectionState extends State<IssueUrlSection> {
  late TextEditingController _controller;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: widget.initialValue ?? '');
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  String? _validate(String? value) {
    if (value == null || value.isEmpty) {
      return 'Please enter a URL';
    }
    final uri = Uri.tryParse(value);
    if (uri == null || !uri.hasScheme || !uri.hasAuthority) {
      return 'Please enter a valid URL';
    }
    if (isTestObserverIssueUrl(uri) && !isValidIssuePage(uri)) {
      return 'Invalid Test Observer issue URL, expected: ${Uri.base.origin}/#/issues/<id>';
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      key: const Key('attachIssueFormUrlInput'),
      controller: _controller,
      validator: _validate,
      decoration: const InputDecoration(
        labelText:
            'Test Observer issue URL or external URL (GitHub, Jira, Launchpad)',
      ),
      onChanged: widget.onChanged,
    );
  }
}

Uri extractRouteUri(Uri uri) {
  return uri.fragment.isNotEmpty ? Uri.parse(uri.fragment) : uri;
}

bool isTestObserverIssueUrl(Uri uri) {
  return uri.origin == Uri.base.origin;
}

bool isValidIssuePage(Uri uri) {
  return AppRoutes.isIssuePage(extractRouteUri(uri));
}
