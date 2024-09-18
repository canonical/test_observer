import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru/yaru.dart';

class BlockingProviderPreloader<T> extends ConsumerWidget {
  const BlockingProviderPreloader({
    super.key,
    required this.provider,
    required this.builder,
  });

  final ProviderListenable<AsyncValue<T>> provider;
  final Widget Function(BuildContext context, T value) builder;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final value = ref.watch(provider);

    return value.when(
      data: (value) => builder(context, value),
      error: (e, stack) =>
          Center(child: Text('Error:\n$e\nStackTrace:\n$stack')),
      loading: () => const Center(child: YaruCircularProgressIndicator()),
    );
  }
}
