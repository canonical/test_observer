import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class NonBlockingProviderPreloader extends ConsumerWidget {
  const NonBlockingProviderPreloader({
    super.key,
    required this.provider,
    required this.child,
  });

  final ProviderListenable provider;
  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.watch(provider);
    return child;
  }
}
