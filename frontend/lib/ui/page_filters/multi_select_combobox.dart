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

import '../vanilla/vanilla_text_input.dart';

class MultiSelectCombobox extends StatefulWidget {
  final String title;
  final List<String> allOptions;
  final Function(String optionName, bool isSelected) onChanged;
  final FocusNode? focusNode;
  final int maxSuggestions;
  final Set<String> initialSelected;

  // Optional async suggestions callback
  final Future<List<String>> Function(String pattern)? asyncSuggestionsCallback;

  // Minimum characters to trigger async search
  final int minCharsForAsyncSearch;

  const MultiSelectCombobox({
    super.key,
    required this.title,
    required this.allOptions,
    required this.onChanged,
    this.focusNode,
    this.maxSuggestions = 50,
    this.initialSelected = const {},
    this.asyncSuggestionsCallback,
    this.minCharsForAsyncSearch = 2,
  });

  @override
  State<MultiSelectCombobox> createState() => MultiSelectComboboxState();
}

class MultiSelectComboboxState extends State<MultiSelectCombobox> {
  late Set<String> _selected;
  late bool _isExpanded;

  late TextEditingController _controller;
  late FocusNode _internalFocusNode;
  FocusNode? _typeAheadFocusNode;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController();
    _internalFocusNode = FocusNode();

    // Initialize with URL parameters
    _selected = Set.from(widget.initialSelected);

    // Auto-expand if there are pre-selected items
    _isExpanded = widget.initialSelected.isNotEmpty;
  }

  @override
  void didUpdateWidget(MultiSelectCombobox oldWidget) {
    super.didUpdateWidget(oldWidget);

    // Update selected items when widget rebuilds with new initialSelected
    final oldSorted = oldWidget.initialSelected.toList()..sort();
    final newSorted = widget.initialSelected.toList()..sort();

    if (oldSorted.join(',') != newSorted.join(',')) {
      setState(() {
        _selected = Set.from(widget.initialSelected);
        // Keep expanded state if there are still selections, or expand if new selections appeared
        _isExpanded = _isExpanded || widget.initialSelected.isNotEmpty;
      });
    }
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

  Future<List<String>> _getSuggestions(String pattern) async {
    if (widget.asyncSuggestionsCallback != null) {
      if (pattern.trim().length < widget.minCharsForAsyncSearch) {
        return [];
      }

      try {
        final asyncResults = await widget.asyncSuggestionsCallback!(pattern);
        return asyncResults
            .where((option) => !_selected.contains(option))
            .toList();
      } catch (e) {
        debugPrint('Error fetching async suggestions: $e');
        return [];
      }
    }

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
        _ComboboxHeader(
          title: widget.title,
          selectedCount: _selected.length,
          isExpanded: _isExpanded,
          onTap: () => setState(() => _isExpanded = !_isExpanded),
        ),
        if (_isExpanded) ...[
          const SizedBox(height: 8),
          _ComboboxSearchField(
            controller: _controller,
            getSuggestions: _getSuggestions,
            isAsync: widget.asyncSuggestionsCallback != null,
            minCharsForSearch: widget.minCharsForAsyncSearch,
            onSelected: (suggestion) {
              setState(() {
                _selected.add(suggestion);
                widget.onChanged(suggestion, true);
                _controller.clear();
              });
            },
            onFocusNodeSet: (focusNode) {
              _typeAheadFocusNode = focusNode;
            },
          ),
          const SizedBox(height: 8),
          _SelectedItemsList(
            selectedItems: _selected,
            onRemove: (option) {
              setState(() {
                _selected.remove(option);
                widget.onChanged(option, false);
              });
            },
          ),
        ],
      ],
    );
  }
}

// Header with title, count, and expand/collapse button
class _ComboboxHeader extends StatelessWidget {
  const _ComboboxHeader({
    required this.title,
    required this.selectedCount,
    required this.isExpanded,
    required this.onTap,
  });

  final String title;
  final int selectedCount;
  final bool isExpanded;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
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
                '$title ($selectedCount selected)',
                style: const TextStyle(fontSize: 16),
              ),
            ),
            Icon(isExpanded ? Icons.arrow_drop_up : Icons.arrow_drop_down),
          ],
        ),
      ),
    );
  }
}

// Search field with TypeAhead functionality
class _ComboboxSearchField extends StatelessWidget {
  const _ComboboxSearchField({
    required this.controller,
    required this.getSuggestions,
    required this.isAsync,
    required this.minCharsForSearch,
    required this.onSelected,
    required this.onFocusNodeSet,
  });

  final TextEditingController controller;
  final Future<List<String>> Function(String) getSuggestions;
  final bool isAsync;
  final int minCharsForSearch;
  final Function(String) onSelected;
  final Function(FocusNode) onFocusNodeSet;

  @override
  Widget build(BuildContext context) {
    return TypeAheadField<String>(
      suggestionsCallback: getSuggestions,
      itemBuilder: (context, suggestion) {
        return ListTile(title: Text(suggestion));
      },
      onSelected: onSelected,
      builder: (context, controller, focusNode) {
        // Store the TypeAhead's focus node for parent widget
        onFocusNodeSet(focusNode);
        return VanillaTextInput(
          controller: controller,
          focusNode: focusNode,
          hintText: isAsync
              ? 'Type $minCharsForSearch+ characters to search...'
              : 'Search...',
        );
      },
      decorationBuilder: (context, child) {
        return Material(
          elevation: 4,
          borderRadius: BorderRadius.circular(4),
          child: Container(
            constraints: const BoxConstraints(maxHeight: 250),
            child: child,
          ),
        );
      },
      offset: const Offset(0, 4),
      hideOnEmpty: true,
      hideOnError: true,
      hideOnLoading: false,
      loadingBuilder: isAsync
          ? (context) => const ListTile(
                title: Text('Searching...'),
                leading: SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
              )
          : null,
      errorBuilder: isAsync
          ? (context, error) => const ListTile(
                title: Text('Error loading suggestions'),
                leading: Icon(Icons.error, color: Colors.red),
              )
          : null,
    );
  }
}

// List of selected items with checkboxes for removal
class _SelectedItemsList extends StatelessWidget {
  const _SelectedItemsList({
    required this.selectedItems,
    required this.onRemove,
  });

  final Set<String> selectedItems;
  final Function(String) onRemove;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: selectedItems.map((option) {
        return Row(
          children: [
            YaruCheckbox(
              value: true,
              onChanged: (_) => onRemove(option),
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
      }).toList(),
    );
  }
}
