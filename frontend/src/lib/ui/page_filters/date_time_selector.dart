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

import '../date_time.dart';

class DateTimeSelector extends StatefulWidget {
  const DateTimeSelector({
    super.key,
    required this.title,
    required this.onSelected,
    this.initialDate,
  });

  final String title;
  final Function(DateTime?) onSelected;
  final DateTime? initialDate;

  @override
  State<DateTimeSelector> createState() => _DateTimeSelectorState();
}

class _DateTimeSelectorState extends State<DateTimeSelector> {
  void _clearDate() {
    setState(() {
      _selectedDate = null;
      _controller.clear();
      _errorText = null;
    });
    widget.onSelected(null);
  }

  late DateTime? _selectedDate;
  late bool _isExpanded;
  late TextEditingController _controller;
  String? _errorText;

  @override
  void initState() {
    super.initState();
    _selectedDate = widget.initialDate;
    _controller = TextEditingController(
      text: _selectedDate != null ? formatDateTime(_selectedDate!) : '',
    );
    _isExpanded = _selectedDate != null;
  }

  @override
  void didUpdateWidget(DateTimeSelector oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.initialDate != oldWidget.initialDate) {
      setState(() {
        _selectedDate = widget.initialDate;
        _controller.text =
            _selectedDate != null ? formatDateTime(_selectedDate!) : '';
        _isExpanded = _isExpanded || _selectedDate != null;
      });
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _onTextChanged(String value) {
    setState(() {
      _errorText = null;
      if (value.isEmpty) {
        _errorText = null;
        return;
      }
      final parsed = DateTime.tryParse(value);
      if (parsed == null) {
        _errorText = 'Invalid date/time';
      }
    });
  }

  void _onFieldSubmittedOrUnfocused(String value) {
    final parsed = DateTime.tryParse(value);
    setState(() {
      if (parsed != null) {
        _selectedDate = parsed.toUtc();
        _errorText = null;
        widget.onSelected(_selectedDate);
      } else if (value.isEmpty) {
        _selectedDate = null;
        _errorText = null;
        widget.onSelected(null);
      } else {
        _errorText = 'Invalid date/time';
      }
    });
  }

  Future<void> _selectDate(BuildContext context) async {
    final initial = _selectedDate ?? DateTime.now();
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: initial,
      firstDate: DateTime(2000),
      lastDate: DateTime(2050),
    );
    if (picked != null) {
      setState(() {
        _selectedDate = DateTime(
          picked.year,
          picked.month,
          picked.day,
          _selectedDate?.hour ?? 0,
          _selectedDate?.minute ?? 0,
        ).toUtc();
        _controller.text = formatDateTime(_selectedDate!);
        _errorText = null;
      });
      widget.onSelected(_selectedDate);
    }
  }

  Future<void> _selectTime(BuildContext context) async {
    final initial = _selectedDate != null
        ? TimeOfDay(hour: _selectedDate!.hour, minute: _selectedDate!.minute)
        : TimeOfDay.now();
    final TimeOfDay? picked = await showTimePicker(
      context: context,
      initialTime: initial,
    );
    if (picked != null) {
      setState(() {
        final base = _selectedDate ?? DateTime.now();
        _selectedDate = DateTime(
          base.year,
          base.month,
          base.day,
          picked.hour,
          picked.minute,
        ).toUtc();
        _controller.text = formatDateTime(_selectedDate!);
        _errorText = null;
      });
      widget.onSelected(_selectedDate);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _ExpandableHeader(
          title: widget.title,
          selectedDate: _selectedDate,
          isExpanded: _isExpanded,
          onTap: () => setState(() => _isExpanded = !_isExpanded),
        ),
        if (_isExpanded)
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.start,
                  children: [
                    IconButton(
                      icon: const Icon(Icons.calendar_today),
                      tooltip: 'Pick date',
                      onPressed: () => _selectDate(context),
                    ),
                    IconButton(
                      icon: const Icon(Icons.access_time),
                      tooltip: 'Pick time',
                      onPressed: () => _selectTime(context),
                    ),
                    IconButton(
                      icon: const Icon(Icons.clear),
                      tooltip: 'Clear',
                      onPressed: _selectedDate != null ? _clearDate : null,
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Expanded(
                      child: Focus(
                        onFocusChange: (hasFocus) {
                          if (!hasFocus) {
                            _onFieldSubmittedOrUnfocused(_controller.text);
                          }
                        },
                        child: TextFormField(
                          controller: _controller,
                          decoration: InputDecoration(
                            hintText: 'YYYY-MM-DD HH:MM:SS',
                            errorText: _errorText,
                          ),
                          onChanged: _onTextChanged,
                          onFieldSubmitted: _onFieldSubmittedOrUnfocused,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
      ],
    );
  }
}

class _ExpandableHeader extends StatelessWidget {
  const _ExpandableHeader({
    required this.title,
    required this.selectedDate,
    required this.isExpanded,
    required this.onTap,
  });

  final String title;
  final DateTime? selectedDate;
  final bool isExpanded;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    String display = title;
    if (selectedDate != null) {
      display += ' (';
      display += '${selectedDate!.year.toString().padLeft(4, '0')}-'
          '${selectedDate!.month.toString().padLeft(2, '0')}-'
          '${selectedDate!.day.toString().padLeft(2, '0')} ';
      display += '${selectedDate!.hour.toString().padLeft(2, '0')}:'
          '${selectedDate!.minute.toString().padLeft(2, '0')})';
    } else {
      display += ' (Not selected)';
    }
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
                display,
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
