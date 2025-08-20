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

import '../expandable.dart';
import '../../models/execution_metadata.dart';
import 'execution_metadata_table.dart';

class ExecutionMetadataExpandable extends StatelessWidget {
  const ExecutionMetadataExpandable({
    super.key,
    required this.executionMetadata,
    required this.initiallyExpanded,
  });

  final ExecutionMetadata executionMetadata;
  final bool initiallyExpanded;

  @override
  Widget build(BuildContext context) {
    return Expandable(
      title: const Text('Execution Metadata'),
      initiallyExpanded: initiallyExpanded,
      children: [
        ExecutionMetadataTable(metadata: executionMetadata),
      ],
    );
  }
}
