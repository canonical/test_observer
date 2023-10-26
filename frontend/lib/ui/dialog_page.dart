import 'package:flutter/material.dart';

class DialogPage<T> extends Page<T> {
  final WidgetBuilder builder;

  const DialogPage({
    super.key,
    super.name,
    super.arguments,
    super.restorationId,
    required this.builder,
  });

  @override
  Route<T> createRoute(BuildContext context) => DialogRoute<T>(
        context: context,
        builder: builder,
        settings: this,
      );
}
