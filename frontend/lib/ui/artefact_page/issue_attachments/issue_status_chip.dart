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
