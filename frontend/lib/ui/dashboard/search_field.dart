import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru/yaru.dart';

import '../../providers/search_value.dart';

class SearchField extends ConsumerWidget {
  const SearchField({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return _SearchNotifierListener(
      child: SizedBox(
        height: 50,
        width: double.infinity,
        child: SearchBar(
          hintText: 'Search by name',
          hintStyle: MaterialStatePropertyAll(
            Theme.of(context)
                .textTheme
                .bodyLarge
                ?.apply(color: YaruColors.warmGrey),
          ),
          elevation: const MaterialStatePropertyAll(0),
          shape: MaterialStatePropertyAll(LinearBorder.bottom()),
          side: const MaterialStatePropertyAll(BorderSide()),
          onChanged: ref.read(searchValueProvider.notifier).onChanged,
        ),
      ),
    );
  }
}

// Watches searchValueProvider as otherwise riverpod will not initialize it
// since it's not being watched by any widget
class _SearchNotifierListener extends ConsumerWidget {
  const _SearchNotifierListener({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.watch(searchValueProvider);
    return child;
  }
}
