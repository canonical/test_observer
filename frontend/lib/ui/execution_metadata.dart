// Copyright 2025 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter/material.dart';
import '../../models/execution_metadata.dart';
import 'spacing.dart';

class ExecutionMetadataTable extends StatefulWidget {
  final ExecutionMetadata metadata;
  const ExecutionMetadataTable({super.key, required this.metadata});

  @override
  State<ExecutionMetadataTable> createState() => _ExecutionMetadataTableState();
}

class _ExecutionMetadataTableState extends State<ExecutionMetadataTable> {
  final ScrollController _scrollController = ScrollController();

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final sortedEntries = widget.metadata.data.entries.toList()
      ..sort((a, b) => a.key.compareTo(b.key));
    if (sortedEntries.isEmpty) {
      return const Text('No execution metadata available.');
    }
    return Scrollbar(
      controller: _scrollController,
      interactive: true,
      child: SingleChildScrollView(
        controller: _scrollController,
        scrollDirection: Axis.horizontal,
        child: DataTable(
          dataRowMaxHeight: double.infinity,
          columns: const [
            DataColumn(
              label: Text('Category'),
            ),
            DataColumn(
              label: Text('Values'),
            ),
          ],
          rows: sortedEntries
              .map(
                (entry) => DataRow(
                  cells: [
                    DataCell(Text(entry.key)),
                    DataCell(
                      Column(
                        mainAxisAlignment: MainAxisAlignment.start,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: (entry.value.toList()..sort())
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
        ),
      ),
    );
  }
}
