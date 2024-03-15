import 'package:flutter/material.dart';
import 'package:yaru_widgets/yaru_widgets.dart';

import '../models/filter.dart';
import '../models/filters.dart';
import 'spacing.dart';

class SideFilters extends StatelessWidget {
  const SideFilters({
    super.key,
    required this.filters,
    required this.onOptionChanged,
  });

  final Filters filters;
  final Function(String, String, bool) onOptionChanged;

  static const width = 300.0;
  static const spacingBetweenFilters = Spacing.level4;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: width,
      child: ListView.separated(
        shrinkWrap: true,
        itemBuilder: (_, i) => _SideFilter(
          filter: filters.filters[i],
          onOptionChanged: onOptionChanged,
        ),
        separatorBuilder: (_, __) =>
            const SizedBox(height: spacingBetweenFilters),
        itemCount: filters.filters.length,
      ),
    );
  }
}

class _SideFilter extends StatelessWidget {
  const _SideFilter({required this.filter, required this.onOptionChanged});

  final Filter filter;
  final Function(String, String, bool) onOptionChanged;

  @override
  Widget build(BuildContext context) {
    return ExpansionTile(
      initiallyExpanded: true,
      controlAffinity: ListTileControlAffinity.leading,
      childrenPadding: const EdgeInsets.only(left: Spacing.level4),
      shape: const Border(),
      collapsedShape: const Border(),
      title: Text(
        filter.name,
        style: Theme.of(context).textTheme.headlineSmall,
      ),
      children: [
        for (final option in filter.availableOptions)
          Row(
            children: [
              YaruCheckbox(
                value: filter.selectedOptions.contains(option),
                onChanged: (newValue) {
                  if (newValue != null) {
                    onOptionChanged(filter.name, option, newValue);
                  }
                },
              ),
              Text(option),
            ],
          ),
      ],
    );
  }
}
