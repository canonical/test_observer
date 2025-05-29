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
import 'spacing.dart';
import 'vanilla/vanilla_text_input.dart';

class SubmittableTextField extends StatefulWidget {
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
  State<SubmittableTextField> createState() => _SubmittableTextFieldState();
}

class _SubmittableTextFieldState extends State<SubmittableTextField> {
  bool isEditing = false;
  TextEditingController commentController = TextEditingController();
  FocusNode focusNode = FocusNode();

  @override
  void initState() {
    super.initState();
    commentController.text = widget.initialValue;
  }

  @override
  void dispose() {
    commentController.dispose();
    focusNode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            widget.title,
            const Spacer(),
            if (isEditing) ..._editingIcons else ..._normalIcons,
          ],
        ),
        const SizedBox(height: Spacing.level3),
        VanillaTextInput(
          focusNode: focusNode,
          enabled: isEditing,
          labelStyle: Theme.of(context).textTheme.titleLarge,
          controller: commentController,
          multiline: true,
          hintText: 'No comment',
        ),
      ],
    );
  }

  List<IconButton> get _normalIcons {
    return [
      IconButton(
        onPressed: () {
          setState(() {
            isEditing = true;
          });
          WidgetsBinding.instance
              .addPostFrameCallback((_) => focusNode.requestFocus());
        },
        icon: Icon(Icons.edit),
      ),
    ];
  }

  List<IconButton> get _editingIcons {
    return [
      IconButton(
        onPressed: () {
          setState(() {
            isEditing = false;
            commentController.text = widget.initialValue;
          });
        },
        icon: Icon(Icons.cancel),
      ),
      IconButton(
        onPressed: () {
          setState(() {
            isEditing = false;
            widget.onSubmit(commentController.text);
          });
        },
        icon: Icon(Icons.done),
      ),
    ];
  }
}
