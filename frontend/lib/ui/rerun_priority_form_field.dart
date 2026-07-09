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
  if (value == null || value.isEmpty) return 'Priority is required';
  final n = int.tryParse(value);
  if (n == null) return 'Enter a valid integer';
  if (n < rerunPriorityMin || n > rerunPriorityMax) {
    return 'Priority must be between $rerunPriorityMin and $rerunPriorityMax';
  }
  return null;
}

class RerunPriorityFormField extends StatelessWidget {
  const RerunPriorityFormField({super.key, required this.controller});

  final TextEditingController controller;

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: controller,
      decoration: const InputDecoration(labelText: 'Priority'),
      keyboardType: TextInputType.numberWithOptions(signed: true),
      validator: validateRerunPriority,
    );
  }
}
