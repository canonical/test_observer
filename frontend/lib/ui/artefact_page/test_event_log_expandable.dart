import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/test_event.dart';
import '../expandable.dart';

class TestEventLogExpandable extends ConsumerWidget {
  const TestEventLogExpandable({
    super.key,
    required this.testExecutionId,
    required this.initiallyExpanded,
    required this.testEvents,
  });

  final int testExecutionId;
  final bool initiallyExpanded;
  final List<TestEvent> testEvents;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Expandable(
      title: const Text('Event Log'),
      initiallyExpanded: initiallyExpanded,
      children: <Widget>[
        DataTable(
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
      ],
    );
  }
}
