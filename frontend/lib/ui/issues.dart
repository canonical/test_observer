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
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/issue.dart';
import '../providers/issues.dart';
import '../routing.dart';
import 'inline_url_text.dart';

class IssueSourceWidget extends StatelessWidget {
  const IssueSourceWidget({
    super.key,
    required this.source,
    this.textStyle,
  });

  final IssueSource source;
  final TextStyle? textStyle;

  @override
  Widget build(BuildContext context) {
    final style = textStyle ?? Theme.of(context).textTheme.labelSmall;
    return Text(
      source.name.toUpperCase(),
      style: style?.copyWith(
        fontWeight: FontWeight.bold,
        letterSpacing: 1.2,
      ),
    );
  }
}

class IssueProjectWidget extends StatelessWidget {
  const IssueProjectWidget({
    super.key,
    required this.project,
    this.textStyle,
  });

  final String project;
  final TextStyle? textStyle;

  @override
  Widget build(BuildContext context) {
    final style = textStyle ?? Theme.of(context).textTheme.bodyMedium;
    return Text(
      project,
      style: style?.copyWith(color: Colors.grey),
    );
  }
}

class IssueLinkWidget extends StatelessWidget {
  const IssueLinkWidget({
    super.key,
    required this.issue,
    this.textStyle,
  });

  final Issue issue;
  final TextStyle? textStyle;

  @override
  Widget build(BuildContext context) {
    final style = (textStyle ?? Theme.of(context).textTheme.bodyMedium)?.apply(
      decoration: TextDecoration.underline,
      color: Colors.blue,
    );
    if (issue.source == IssueSource.jira) {
      return InlineUrlText(
        url: issue.url,
        urlText: '${issue.project}-${issue.key}',
        fontStyle: style,
      );
    } else {
      return InlineUrlText(
        url: issue.url,
        urlText: '#${issue.key}',
        fontStyle: style,
      );
    }
  }
}

class IssueTitleWidget extends StatelessWidget {
  const IssueTitleWidget({
    super.key,
    required this.issue,
    this.textStyle,
  });

  final Issue issue;
  final TextStyle? textStyle;

  @override
  Widget build(BuildContext context) {
    return Text(
      (issue.title.isNotEmpty ? issue.title : '[No title]'),
      style: (textStyle ?? Theme.of(context).textTheme.titleMedium)?.copyWith(
        color: Theme.of(context).colorScheme.primary,
        decoration: TextDecoration.none,
      ),
      overflow: TextOverflow.ellipsis,
      maxLines: 1,
    );
  }
}

class IssueStatusWidget extends StatelessWidget {
  const IssueStatusWidget({
    super.key,
    required this.issue,
    this.textStyle,
  });

  final Issue issue;
  final TextStyle? textStyle;

  @override
  Widget build(BuildContext context) {
    late Color color;
    late String label;
    late IconData icon;
    switch (issue.status) {
      case IssueStatus.open:
        color = Colors.green;
        label = 'Open';
        icon = Icons.adjust;
        break;
      case IssueStatus.closed:
        color = Colors.purple;
        label = 'Closed';
        icon = Icons.check_circle_outline;
        break;
      case IssueStatus.unknown:
        color = Colors.grey;
        label = 'Unknown';
        icon = Icons.help_outline;
        break;
    }

    final style = textStyle ?? Theme.of(context).textTheme.bodyMedium;
    final iconSize = style?.fontSize ?? 18.0;

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, color: color, size: iconSize),
        const SizedBox(width: 6),
        Text(label, style: style),
      ],
    );
  }
}

class IssueUrlFormField extends StatefulWidget {
  const IssueUrlFormField({
    super.key,
    this.allowInternalIssue = true,
    this.onChanged,
    this.initialValue,
  });

  final bool allowInternalIssue;
  final ValueChanged<String>? onChanged;
  final String? initialValue;

  @override
  State<IssueUrlFormField> createState() => _IssueUrlFormFieldState();
}

class _IssueUrlFormFieldState extends State<IssueUrlFormField> {
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
    if (uri == null ||
        !uri.hasScheme ||
        !uri.hasAuthority ||
        uri.host.isEmpty) {
      return 'Please enter a valid URL';
    }
    if (widget.allowInternalIssue &&
        isTestObserverUrl(uri) &&
        !isValidIssuePage(uri)) {
      return 'Invalid Test Observer issue URL, expected: ${Uri.base.origin}/#/issues/<id>';
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      key: const Key('issueUrlFormField'),
      controller: _controller,
      validator: _validate,
      decoration: InputDecoration(
        labelText: widget.allowInternalIssue
            ? 'Test Observer issue URL or external URL (GitHub, Jira, Launchpad)'
            : 'External issue URL (GitHub, Jira, Launchpad)',
      ),
      onChanged: widget.onChanged,
    );
  }
}

Uri extractRouteUri(Uri uri) {
  return uri.fragment.isNotEmpty ? Uri.parse(uri.fragment) : uri;
}

bool isTestObserverUrl(Uri uri) {
  return uri.origin == Uri.base.origin;
}

bool isValidIssuePage(Uri uri) {
  return AppRoutes.isIssuePage(extractRouteUri(uri));
}

Future<int> getOrCreateIssueId(WidgetRef ref, String issueUrl) async {
  final uri = Uri.parse(issueUrl.trim());
  if (isTestObserverUrl(uri)) {
    return AppRoutes.issueIdFromUri(extractRouteUri(uri));
  } else {
    final issue = await ref
        .read(issuesProvider.notifier)
        .createIssue(url: uri.toString());
    return issue.id;
  }
}
