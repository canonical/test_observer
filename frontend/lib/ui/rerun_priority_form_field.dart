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

const rerunPriorityMin = -1000000;
const rerunPriorityMax = 1000000;

String? validateRerunPriority(String? value) {
  if (value == null || value.isEmpty) return 'Rerun priority is required';
  final n = int.tryParse(value);
  if (n == null) return 'Enter a valid integer';
  if (n < rerunPriorityMin || n > rerunPriorityMax) {
    return 'Rerun priority must be between $rerunPriorityMin and $rerunPriorityMax';
  }
  return null;
}

class RerunPriorityFormField extends StatelessWidget {
  const RerunPriorityFormField({super.key, required this.controller});

  final TextEditingController controller;

  @override
  Widget build(BuildContext context) {
    final tooltipKey = GlobalKey<TooltipState>();
    return TextFormField(
      controller: controller,
      decoration: InputDecoration(
        labelText: 'Rerun priority',
        helperText: 'Optional, $rerunPriorityMin to $rerunPriorityMax '
            '(default 0)',
        suffixIcon: Tooltip(
          key: tooltipKey,
          margin: const EdgeInsets.symmetric(horizontal: 24),
          triggerMode: TooltipTriggerMode.manual,
          showDuration: const Duration(seconds: 10),
          message: 'Higher-priority reruns are returned first in the rerun '
              'queue. Priority is only an ordering hint: your test scheduler '
              'may or may not honour it.',
          child: IconButton(
            icon: const Icon(Icons.info_outline, size: 18),
            tooltip: 'About rerun priority',
            onPressed: () => tooltipKey.currentState?.ensureTooltipVisible(),
          ),
        ),
      ),
      keyboardType: const TextInputType.numberWithOptions(signed: true),
      validator: validateRerunPriority,
    );
  }
}
