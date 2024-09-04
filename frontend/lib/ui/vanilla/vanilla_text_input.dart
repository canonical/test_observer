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
  }) : _label = label;

  final String? _label;
  final bool enabled;
  final bool multiline;
  final TextEditingController? controller;
  final String? Function(String?)? validator;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (_label != null)
          Text(_label, style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: Spacing.level2),
        TextFormField(
          controller: controller,
          validator: validator,
          keyboardType: multiline ? TextInputType.multiline : null,
          maxLines: multiline ? null : 1,
          minLines: multiline ? 4 : null,
          enabled: enabled,
          decoration: const InputDecoration(
            enabledBorder:
                UnderlineInputBorder(borderRadius: BorderRadius.zero),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.zero,
              borderSide: BorderSide(color: Colors.blue),
            ),
            disabledBorder: UnderlineInputBorder(
              borderRadius: BorderRadius.zero,
              borderSide: BorderSide(color: Colors.black12),
            ),
            focusedErrorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.zero,
              borderSide: BorderSide(color: Colors.red),
            ),
            errorBorder: UnderlineInputBorder(
              borderRadius: BorderRadius.zero,
              borderSide: BorderSide(color: Colors.red),
            ),
          ),
        ),
      ],
    );
  }
}
