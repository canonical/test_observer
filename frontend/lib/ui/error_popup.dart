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
          builder: (context) => WillPopScope(
            onWillPop: () {
              ref.read(globalErrorMessageProvider.notifier).set('');
              return Future.value(true);
            },
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
