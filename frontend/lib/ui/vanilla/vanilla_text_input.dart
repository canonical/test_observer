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

import '../spacing.dart';

class VanillaTextInput extends StatelessWidget {
  const VanillaTextInput({
    super.key,
    String? label,
    this.enabled = true,
    this.multiline = false,
    this.controller,
    this.validator,
    this.hintText,
    this.labelStyle,
    this.focusNode,
  }) : _label = label;

  final String? _label;
  final bool enabled;
  final bool multiline;
  final TextEditingController? controller;
  final String? Function(String?)? validator;
  final String? hintText;
  final TextStyle? labelStyle;
  final FocusNode? focusNode;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (_label != null)
          Text(
            _label,
            style: labelStyle ?? Theme.of(context).textTheme.titleMedium,
          ),
        const SizedBox(height: Spacing.level2),
        TextFormField(
          focusNode: focusNode,
          controller: controller,
          validator: validator,
          keyboardType: multiline ? TextInputType.multiline : null,
          maxLines: multiline ? null : 1,
          minLines: multiline ? 4 : null,
          enabled: enabled,
          decoration: InputDecoration(
            hintText: hintText,
            enabledBorder:
                const UnderlineInputBorder(borderRadius: BorderRadius.zero),
            focusedBorder: const OutlineInputBorder(
              borderRadius: BorderRadius.zero,
              borderSide: BorderSide(color: Colors.blue),
            ),
            disabledBorder: const UnderlineInputBorder(
              borderRadius: BorderRadius.zero,
              borderSide: BorderSide(color: Colors.black12),
            ),
            focusedErrorBorder: const OutlineInputBorder(
              borderRadius: BorderRadius.zero,
              borderSide: BorderSide(color: Colors.red),
            ),
            errorBorder: const UnderlineInputBorder(
              borderRadius: BorderRadius.zero,
              borderSide: BorderSide(color: Colors.red),
            ),
          ),
        ),
      ],
    );
  }
}
