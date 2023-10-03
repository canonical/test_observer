import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sentry_flutter/sentry_flutter.dart';

import 'app.dart';
import 'helpers.dart';

Future<void> main() async {
  final sentryDSN = getSentryDSN();

  if (sentryDSN != null &&
      sentryDSN.isNotEmpty &&
      sentryDSN != 'http://sentry-dsn-placeholder/') {
    await SentryFlutter.init(
      (options) {
        options.dsn = sentryDSN;
        options.sampleRate = 0.1;
      },
      appRunner: () => runApp(const ProviderScope(child: App())),
    );
  } else {
    runApp(const ProviderScope(child: App()));
  }
}
