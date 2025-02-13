// Copyright (C) 2023-2025 Canonical Ltd.
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

import '../../providers/test_events.dart';
import '../blocking_provider_preloader.dart';
import '../expandable.dart';

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
    return Expandable(
      title: const Text('Event log'),
      initiallyExpanded: initiallyExpanded,
      children: [
        BlockingProviderPreloader(
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
        ),
      ],
    );
  }
}
