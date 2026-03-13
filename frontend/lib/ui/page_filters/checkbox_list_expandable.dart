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
import 'package:yaru/yaru.dart';

import '../../providers/page_filters.dart';
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
      tilePadding: EdgeInsets.zero,
      childrenPadding: EdgeInsets.zero,
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
              Flexible(
                child: Tooltip(
                  message: option.name,
                  child: Text(
                    option.name.contains('::')
                        ? option.name
                            .substring(option.name.lastIndexOf('::') + 2)
                        : option.name,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ),
            ],
          ),
      ],
    );
  }
}
