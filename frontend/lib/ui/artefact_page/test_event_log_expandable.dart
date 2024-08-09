import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru/yaru.dart';

import '../../providers/test_events.dart';
import '../expandable.dart';

class TestEventLogExpandable extends ConsumerWidget {
  const TestEventLogExpandable({
    super.key,
    required this.testExecutionId,
    required this.initiallyExpanded,
  });

  final int testExecutionId;
  final bool initiallyExpanded;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final testEvents = ref.watch(testEventsProvider(testExecutionId));

    return Expandable(
      title: const Text('Event Log'),
      initiallyExpanded: initiallyExpanded,
      children: <Widget>[
        testEvents.when(
          loading: () => const Center(child: YaruCircularProgressIndicator()),
          error: (error, stackTrace) => Center(child: Text('Error: $error')),
          data: (testEvents) => DataTable(
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
        ),
      ],
    );
  }
}
