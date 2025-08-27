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

import '../../../models/issue.dart';

class IssueStatusChip extends StatelessWidget {
  final IssueStatus status;
  const IssueStatusChip({super.key, required this.status});

  @override
  Widget build(BuildContext context) {
    late Color color;
    late String label;
    late IconData icon;
    switch (status) {
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
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, color: color, size: 18),
        const SizedBox(width: 6),
        Text(label, style: Theme.of(context).textTheme.bodyMedium),
      ],
    );
  }
}
