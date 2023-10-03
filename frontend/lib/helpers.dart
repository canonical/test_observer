// ignore_for_file: avoid_web_libraries_in_flutter

import 'dart:html';
import 'dart:js_util' as js_util;

String? getSentryDSN() {
  return js_util.getProperty(window, 'sentryDSN');
}
