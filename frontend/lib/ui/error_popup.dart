// Copyright (C) 2023-2025 Canonical Ltd.
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
import 'vanilla/vanilla_modal.dart';

class ErrorPopup extends ConsumerWidget {
  const ErrorPopup({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.listen(globalErrorMessageProvider, (previous, next) {
      if (next.isNotEmpty) {
        showVanillaModal(
          context: context,
          builder: (context) => PopScope(
            onPopInvokedWithResult: (_, __) =>
                ref.read(globalErrorMessageProvider.notifier).set(''),
            child: VanillaModal(
              title: const Text('Error'),
              content: Text(next),
            ),
          ),
        );
      }
    });

    return child;
  }
}
