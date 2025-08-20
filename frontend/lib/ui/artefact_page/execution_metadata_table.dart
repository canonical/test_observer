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
import '../../models/execution_metadata.dart';
import '../spacing.dart';

class ExecutionMetadataTable extends StatelessWidget {
  final ExecutionMetadata metadata;
  const ExecutionMetadataTable({super.key, required this.metadata});

  @override
  Widget build(BuildContext context) {
    final entries = metadata.data.entries.toList();
    if (entries.isEmpty) {
      return const Text('No execution metadata available.');
    }
    return DataTable(
      dataRowMaxHeight: double.infinity,
      columns: const [
        DataColumn(
          label: Text(
            'Category',
            style: TextStyle(fontStyle: FontStyle.italic),
          ),
        ),
        DataColumn(
          label: Text(
            'Values',
            style: TextStyle(fontStyle: FontStyle.italic),
          ),
        ),
      ],
      rows: entries
          .map(
            (entry) => DataRow(
              cells: [
                DataCell(Text(entry.key)),
                DataCell(
                  Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: entry.value
                        .expand(
                          (v) => [
                            const SizedBox(height: Spacing.level3),
                            Tooltip(
                              message: v,
                              child: Text(
                                v,
                                overflow: TextOverflow.ellipsis,
                                maxLines: 1,
                              ),
                            ),
                            const SizedBox(height: Spacing.level3),
                          ],
                        )
                        .toList(),
                  ),
                ),
              ],
            ),
          )
          .toList(),
    );
  }
}
