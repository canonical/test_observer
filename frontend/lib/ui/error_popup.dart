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

import '../providers/global_error_message.dart';

class ErrorPopup extends ConsumerWidget {
  const ErrorPopup({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.listen(globalErrorMessageProvider, (previous, next) {
      if (next.isNotEmpty) {
        showDialog(
          context: context,
          builder: (context) => PopScope(
            onPopInvokedWithResult: (_, __) =>
                ref.read(globalErrorMessageProvider.notifier).set(''),
            child: SimpleDialog(
              title: const Text('Error'),
              // match default padding of title
              contentPadding: const EdgeInsets.fromLTRB(24.0, 12.0, 24.0, 16.0),
              children: [Text(next)],
            ),
          ),
        );
      }
    });

    return child;
  }
}
