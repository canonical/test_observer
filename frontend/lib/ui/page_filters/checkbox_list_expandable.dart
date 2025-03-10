import 'package:flutter/material.dart';
import 'package:yaru/yaru.dart';

import '../../providers/filters_state.dart';
import '../expandable.dart';

class CheckboxListExpandable extends StatelessWidget {
  const CheckboxListExpandable({
    super.key,
    required this.title,
    required this.options,
    required this.onChanged,
  });

  final String title;
  final List<FilterOptionState> options;
  final Function(String optionName, bool isSelected) onChanged;

  @override
  Widget build(BuildContext context) {
    return Expandable(
      initiallyExpanded: true,
      title: Text(
        title,
        style: Theme.of(context).textTheme.headlineSmall,
      ),
      children: [
        for (final option in options)
          Row(
            children: [
              YaruCheckbox(
                value: option.isSelected,
                onChanged: (newValue) {
                  if (newValue != null) {
                    onChanged(option.name, newValue);
                  }
                },
              ),
              Text(option.name),
            ],
          ),
      ],
    );
  }
}
