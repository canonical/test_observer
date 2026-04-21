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

import '../expandable.dart';
import '../../models/execution_metadata.dart';
import '../execution_metadata.dart';

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
