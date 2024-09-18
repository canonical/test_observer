import 'package:flutter/material.dart';

import '../../providers/test_events.dart';
import '../blocking_provider_preloader.dart';

class TestEventLogExpandable extends StatelessWidget {
  const TestEventLogExpandable({
    super.key,
    required this.testExecutionId,
    required this.initiallyExpanded,
  });

  final int testExecutionId;
  final bool initiallyExpanded;

  @override
  Widget build(BuildContext context) {
    return BlockingProviderPreloader(
      provider: testEventsProvider(testExecutionId),
      builder: (_, testEvents) => DataTable(
        columns: const <DataColumn>[
          DataColumn(
            label: Expanded(
              child: Text(
                'Event Name',
                style: TextStyle(fontStyle: FontStyle.italic),
              ),
            ),
          ),
          DataColumn(
            label: Expanded(
              child: Text(
                'Timestamp',
                style: TextStyle(fontStyle: FontStyle.italic),
              ),
            ),
          ),
          DataColumn(
            label: Expanded(
              child: Text(
                'Detail',
                style: TextStyle(fontStyle: FontStyle.italic),
              ),
            ),
          ),
        ],
        rows: testEvents
            .map(
              (testEvent) => DataRow(
                cells: <DataCell>[
                  DataCell(Text(testEvent.eventName)),
                  DataCell(Text(testEvent.timestamp)),
                  DataCell(
                    Tooltip(
                      message: testEvent.detail,
                      child: Text(
                        testEvent.detail,
                        overflow: TextOverflow.ellipsis,
                        maxLines: 1,
                      ),
                    ),
                  ),
                ],
              ),
            )
            .toList(),
      ),
    );
  }
}
