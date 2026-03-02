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
import 'package:flutter_typeahead/flutter_typeahead.dart';
import 'package:yaru/yaru.dart';

import '../vanilla/vanilla_text_input.dart';

/// Represents a meta option that can override normal selection behavior
class MetaOption<V> {
  final V value;
  final String label;

  const MetaOption({
    required this.value,
    required this.label,
  });
}

class MultiSelectCombobox<T> extends StatefulWidget {
  final String title;
  final List<T>? allOptions;
  final Function(T option, bool isSelected) onChanged;
  final FocusNode? focusNode;
  final int maxSuggestions;
  final Set<T> initialSelected;

  // Meta options - mutually exclusive special options
  final List<MetaOption>? metaOptions;
  final dynamic selectedMetaOption;
  final Function(dynamic metaValue)? onMetaOptionChanged;

  // For local filtering: provide allOptions and itemToString for search
  // For async search: provide asyncSuggestionsCallback
  final String Function(T item)? itemToString;

  // Optional async suggestions callback
  final Future<List<T>> Function(String pattern)? asyncSuggestionsCallback;

  // Minimum characters to trigger async search
  final int minCharsForAsyncSearch;

  // Builder for custom display of items (both suggestions and selected)
  // If not provided, uses default tooltip with text display
  final Widget Function(T item)? itemBuilder;

  // Show all options without search box
  final bool showAllOptionsWithoutSearch;

  // Make selections mutually exclusive (only one item can be selected at a time)
  final bool isMutuallyExclusive;

  const MultiSelectCombobox({
    super.key,
    required this.title,
    required this.onChanged,
    this.allOptions,
    this.itemBuilder,
    this.itemToString,
    this.focusNode,
    this.maxSuggestions = 50,
    this.initialSelected = const {},
    this.asyncSuggestionsCallback,
    this.minCharsForAsyncSearch = 2,
    this.metaOptions,
    this.selectedMetaOption,
    this.onMetaOptionChanged,
    this.showAllOptionsWithoutSearch = false,
    this.isMutuallyExclusive = false,
  })  : assert(
          asyncSuggestionsCallback != null ||
              (allOptions != null && itemToString != null),
          'Must provide either asyncSuggestionsCallback or both allOptions and itemToString for local filtering',
        ),
        assert(
          (metaOptions == null &&
                  selectedMetaOption == null &&
                  onMetaOptionChanged == null) ||
              (metaOptions != null && onMetaOptionChanged != null),
          'If using metaOptions, must provide both metaOptions and onMetaOptionChanged',
        ),
        assert(
          !showAllOptionsWithoutSearch || allOptions != null,
          'Must provide allOptions when showAllOptionsWithoutSearch is true',
        );

  Widget _defaultItemBuilder(T item) {
    final toString = itemToString ?? (item) => item.toString();
    final text = toString(item);
    return Tooltip(
      message: text,
      child: Text(
        text,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
      ),
    );
  }

  @override
  State<MultiSelectCombobox<T>> createState() => MultiSelectComboboxState<T>();
}

class MultiSelectComboboxState<T> extends State<MultiSelectCombobox<T>> {
  late Set<T> _selected;
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

    // Auto-expand if there are pre-selected items or a meta option is selected
    _isExpanded =
        widget.initialSelected.isNotEmpty || widget.selectedMetaOption != null;
  }

  @override
  void didUpdateWidget(MultiSelectCombobox<T> oldWidget) {
    super.didUpdateWidget(oldWidget);

    // Update selected items when widget rebuilds with new initialSelected
    // Simple set comparison instead of sorting
    if (oldWidget.initialSelected
            .difference(widget.initialSelected)
            .isNotEmpty ||
        widget.initialSelected
            .difference(oldWidget.initialSelected)
            .isNotEmpty) {
      setState(() {
        _selected = Set.from(widget.initialSelected);
        // Keep expanded state if there are still selections, or expand if new selections appeared
        _isExpanded = _isExpanded || widget.initialSelected.isNotEmpty;
      });
    }

    // Expand if meta option changes from null to non-null
    if (oldWidget.selectedMetaOption != widget.selectedMetaOption &&
        widget.selectedMetaOption != null) {
      setState(() {
        _isExpanded = true;
      });
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    _internalFocusNode.dispose();
    super.dispose();
  }

  // Getters for DRY
  bool get _isAsyncMode => widget.asyncSuggestionsCallback != null;
  Widget Function(T) get _itemBuilder =>
      widget.itemBuilder ?? widget._defaultItemBuilder;

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

  List<T> _filterSelected(List<T> items) {
    return items.where((option) => !_selected.contains(option)).toList();
  }

  Future<List<T>> _getSuggestions(String pattern) async {
    if (_isAsyncMode) {
      if (pattern.trim().length < widget.minCharsForAsyncSearch) {
        return [];
      }

      try {
        final asyncResults = await widget.asyncSuggestionsCallback!(pattern);
        return _filterSelected(asyncResults);
      } catch (e) {
        debugPrint('Error fetching async suggestions: $e');
        return [];
      }
    }

    // Local filtering - allOptions and itemToString are guaranteed by assertion
    final toString = widget.itemToString!;
    final options = widget.allOptions!;
    final filtered = options
        .where(
          (option) =>
              toString(option).toLowerCase().contains(pattern.toLowerCase()),
        )
        .take(widget.maxSuggestions)
        .toList();
    return _filterSelected(filtered);
  }

  @override
  Widget build(BuildContext context) {
    final hasMetaOptionSelected = widget.selectedMetaOption != null;

    // Determine display text
    String displayText;
    if (hasMetaOptionSelected && widget.metaOptions != null) {
      // Find the label for the selected meta option
      final selectedMeta = widget.metaOptions!
          .firstWhere((opt) => opt.value == widget.selectedMetaOption);
      displayText = '${widget.title} (${selectedMeta.label})';
    } else {
      displayText = '${widget.title} (${_selected.length} selected)';
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _ComboboxHeader(
          title: displayText,
          isExpanded: _isExpanded,
          onTap: () => setState(() => _isExpanded = !_isExpanded),
        ),
        if (_isExpanded) ...[
          const SizedBox(height: 8),
          // Meta options (if provided)
          if (widget.metaOptions != null) ...[
            _MetaOptionsRow(
              metaOptions: widget.metaOptions!,
              selectedMetaOption: widget.selectedMetaOption,
              onMetaOptionChanged: (value) {
                // Clear regular selections when meta option is selected
                if (value != null && _selected.isNotEmpty) {
                  for (final item in _selected.toList()) {
                    widget.onChanged(item, false);
                  }
                  setState(() {
                    _selected.clear();
                  });
                }
                // Notify parent of meta option change
                widget.onMetaOptionChanged!(value);
              },
            ),
            const SizedBox(height: 8),
          ],
          if (widget.showAllOptionsWithoutSearch)
            _AllOptionsList<T>(
              allOptions: widget.allOptions!,
              selectedItems: _selected,
              itemBuilder: _itemBuilder,
              isMutuallyExclusive: widget.isMutuallyExclusive,
              onChanged: (option, isSelected) {
                setState(() {
                  if (widget.isMutuallyExclusive) {
                    // For mutually exclusive mode
                    if (isSelected) {
                      // Deselect all other options first
                      for (final item in _selected.toList()) {
                        if (item != option) {
                          widget.onChanged(item, false);
                        }
                      }
                      _selected.clear();
                      _selected.add(option);
                      widget.onChanged(option, true);
                    } else {
                      // Deselect the option
                      _selected.remove(option);
                      widget.onChanged(option, false);
                    }
                  } else {
                    // For multi-select mode
                    if (isSelected) {
                      _selected.add(option);
                    } else {
                      _selected.remove(option);
                    }
                    widget.onChanged(option, isSelected);
                  }
                });
                // Clear meta option when regular selection is made
                if (widget.selectedMetaOption != null) {
                  widget.onMetaOptionChanged!(null);
                }
              },
            )
          else ...[
            _ComboboxSearchField<T>(
              controller: _controller,
              getSuggestions: _getSuggestions,
              isAsync: _isAsyncMode,
              minCharsForSearch: widget.minCharsForAsyncSearch,
              itemBuilder: _itemBuilder,
              onSelected: (suggestion) {
                setState(() {
                  _selected.add(suggestion);
                  widget.onChanged(suggestion, true);
                  _controller.clear();
                });
                // Clear meta option when regular selection is made
                if (widget.selectedMetaOption != null) {
                  widget.onMetaOptionChanged!(null);
                }
              },
              onFocusNodeSet: (focusNode) {
                _typeAheadFocusNode = focusNode;
              },
            ),
            const SizedBox(height: 8),
            _SelectedItemsList<T>(
              selectedItems: _selected,
              itemBuilder: _itemBuilder,
              onRemove: (option) {
                setState(() {
                  _selected.remove(option);
                  widget.onChanged(option, false);
                });
              },
            ),
          ],
        ],
      ],
    );
  }
}

// Meta options row - mutually exclusive checkboxes
class _MetaOptionsRow extends StatelessWidget {
  const _MetaOptionsRow({
    required this.metaOptions,
    required this.selectedMetaOption,
    required this.onMetaOptionChanged,
  });

  final List<MetaOption> metaOptions;
  final dynamic selectedMetaOption;
  final Function(dynamic) onMetaOptionChanged;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 16,
      children: metaOptions.map((option) {
        final isSelected = selectedMetaOption == option.value;
        return InkWell(
          onTap: () {
            // Toggle: if already selected, deselect; otherwise select
            onMetaOptionChanged(isSelected ? null : option.value);
          },
          borderRadius: BorderRadius.circular(4),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                YaruCheckbox(
                  value: isSelected,
                  onChanged: (_) {
                    onMetaOptionChanged(isSelected ? null : option.value);
                  },
                ),
                Text(
                  option.label,
                  style: TextStyle(
                    color: isSelected ? null : Colors.grey[700],
                  ),
                ),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }
}

// Header with title, count, and expand/collapse button
class _ComboboxHeader extends StatelessWidget {
  const _ComboboxHeader({
    required this.title,
    required this.isExpanded,
    required this.onTap,
  });

  final String title;
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
                title,
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
class _ComboboxSearchField<T> extends StatelessWidget {
  const _ComboboxSearchField({
    required this.controller,
    required this.getSuggestions,
    required this.isAsync,
    required this.minCharsForSearch,
    required this.onSelected,
    required this.onFocusNodeSet,
    required this.itemBuilder,
  });

  final TextEditingController controller;
  final Future<List<T>> Function(String) getSuggestions;
  final bool isAsync;
  final int minCharsForSearch;
  final Function(T) onSelected;
  final Function(FocusNode) onFocusNodeSet;
  final Widget Function(T item) itemBuilder;

  @override
  Widget build(BuildContext context) {
    return TypeAheadField<T>(
      suggestionsCallback: getSuggestions,
      itemBuilder: (context, suggestion) {
        return ListTile(title: itemBuilder(suggestion));
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
class _SelectedItemsList<T> extends StatelessWidget {
  const _SelectedItemsList({
    required this.selectedItems,
    required this.onRemove,
    required this.itemBuilder,
  });

  final Set<T> selectedItems;
  final Function(T) onRemove;
  final Widget Function(T item) itemBuilder;

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
            Flexible(child: itemBuilder(option)),
          ],
        );
      }).toList(),
    );
  }
}

// List of all available options with checkboxes or radio buttons (no search)
class _AllOptionsList<T> extends StatelessWidget {
  const _AllOptionsList({
    required this.allOptions,
    required this.selectedItems,
    required this.onChanged,
    required this.itemBuilder,
    required this.isMutuallyExclusive,
  });

  final List<T> allOptions;
  final Set<T> selectedItems;
  final Function(T, bool) onChanged;
  final Widget Function(T item) itemBuilder;
  final bool isMutuallyExclusive;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: allOptions.map((option) {
        final isSelected = selectedItems.contains(option);

        void handleTap() {
          // If clicking the already selected option, deselect it
          if (isSelected) {
            onChanged(option, false);
          } else {
            onChanged(option, true);
          }
        }

        return InkWell(
          onTap: handleTap,
          child: Row(
            children: [
              YaruCheckbox(
                value: isSelected,
                onChanged: (value) => onChanged(option, value ?? false),
              ),
              Flexible(child: itemBuilder(option)),
            ],
          ),
        );
      }).toList(),
    );
  }
}
