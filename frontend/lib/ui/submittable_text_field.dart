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
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'spacing.dart';
import 'vanilla/vanilla_text_input.dart';

class SubmittableTextField extends ConsumerStatefulWidget {
  const SubmittableTextField({
    super.key,
    required this.title,
    required this.onSubmit,
    required this.initialValue,
  });

  final Widget title;
  final Function(String value) onSubmit;
  final String initialValue;

  @override
  ConsumerState<SubmittableTextField> createState() =>
      _SubmittableTextFieldState();
}

class _SubmittableTextFieldState extends ConsumerState<SubmittableTextField> {
  bool isEditing = false;
  TextEditingController commentController = TextEditingController();

  @override
  void initState() {
    super.initState();
    commentController.text = widget.initialValue;
  }

  @override
  void dispose() {
    commentController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final fontStyle = Theme.of(context).textTheme.bodyLarge;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _title(fontStyle),
        const SizedBox(height: Spacing.level3),
        VanillaTextInput(
          enabled: isEditing,
          labelStyle: Theme.of(context).textTheme.titleLarge,
          controller: commentController,
          multiline: true,
          hintText: 'No comment',
        ),
      ],
    );
  }

  Row _title(TextStyle? fontStyle) {
    return Row(
      children: [
        widget.title,
        const Spacer(),
        if (isEditing)
          IconButton(
            onPressed: () {
              setState(() {
                isEditing = false;
                widget.onSubmit(commentController.text);
              });
            },
            icon: Icon(Icons.done),
          )
        else
          IconButton(
            onPressed: () {
              setState(() {
                isEditing = true;
              });
            },
            icon: Icon(Icons.edit),
          ),
      ],
    );
  }
}
