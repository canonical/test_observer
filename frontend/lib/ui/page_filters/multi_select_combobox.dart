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
import 'package:flutter_typeahead/flutter_typeahead.dart';
import 'package:yaru/yaru.dart';

class MultiSelectCombobox extends StatefulWidget {
  final String title;
  final List<String> allOptions;
  final Function(String optionName, bool isSelected) onChanged;
  final FocusNode? focusNode;
  final int maxSuggestions;

  const MultiSelectCombobox({
    super.key,
    required this.title,
    required this.allOptions,
    required this.onChanged,
    this.focusNode,
    this.maxSuggestions = 10,
  });

  @override
  State<MultiSelectCombobox> createState() => MultiSelectComboboxState();
}

class MultiSelectComboboxState extends State<MultiSelectCombobox> {
  final List<String> _selected = [];
  bool _isExpanded = false;

  late TextEditingController _controller;
  late FocusNode _internalFocusNode;
  FocusNode? _typeAheadFocusNode;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController();
    _internalFocusNode = FocusNode();
  }

  @override
  void dispose() {
    _controller.dispose();
    _internalFocusNode.dispose();
    super.dispose();
  }

  // Method to focus on the combobox (for Ctrl+F functionality)
  void focusCombobox() {
    setState(() => _isExpanded = true);
    // Focus after the build completes and TypeAheadField is rendered
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_typeAheadFocusNode != null) {
        _typeAheadFocusNode!.requestFocus();
      }
    });
  }

  List<String> _getSuggestions(String pattern) {
    // Show options matching search AND not already selected, limited to maxSuggestions
    return widget.allOptions
        .where(
          (option) =>
              option.toLowerCase().contains(pattern.toLowerCase()) &&
              !_selected.contains(option),
        )
        .take(widget.maxSuggestions)
        .toList();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        GestureDetector(
          onTap: () => setState(() => _isExpanded = !_isExpanded),
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
            decoration: BoxDecoration(
              border: Border.all(color: Colors.grey),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    '${widget.title} (${_selected.length} selected)',
                    style: const TextStyle(fontSize: 16),
                  ),
                ),
                Icon(_isExpanded ? Icons.arrow_drop_up : Icons.arrow_drop_down),
              ],
            ),
          ),
        ),
        if (_isExpanded) ...[
          const SizedBox(height: 8),
          TypeAheadField<String>(
            suggestionsCallback: _getSuggestions,
            itemBuilder: (context, suggestion) {
              return ListTile(title: Text(suggestion));
            },
            onSelected: (suggestion) {
              setState(() {
                _selected.add(suggestion);
                widget.onChanged(suggestion, true);
                _controller.clear();
              });
            },
            builder: (context, controller, focusNode) {
              _controller = controller;
              _typeAheadFocusNode =
                  focusNode; // Store the TypeAhead's focus node
              return TextField(
                controller: controller,
                focusNode: focusNode,
                decoration: const InputDecoration(
                  hintText: 'Search...',
                  border: OutlineInputBorder(),
                ),
              );
            },
            hideOnEmpty: true,
            hideOnError: true,
            hideOnLoading: true,
          ),
          const SizedBox(height: 8),
          // Show only selected items below search
          ..._selected.map((option) {
            return Row(
              children: [
                YaruCheckbox(
                  value: true,
                  onChanged: (_) {
                    setState(() {
                      _selected.remove(option);
                      widget.onChanged(option, false);
                    });
                  },
                ),
                Flexible(
                  child: Tooltip(
                    message: option,
                    child: Text(
                      option,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ),
              ],
            );
          }),
        ],
      ],
    );
  }
}
