import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:yaru/yaru.dart';

import '../routing.dart';
import 'spacing.dart';

class Navbar extends StatelessWidget {
  const Navbar({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: Spacing.pageHorizontalPadding,
      ),
      color: YaruColors.coolGrey,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Image.asset('assets/canonical.png'),
          const SizedBox(width: Spacing.level4),
          const Expanded(
            child: Row(
              children: [
                _NavbarEntry(title: 'Snap Testing', route: AppRoutes.snaps),
                _NavbarEntry(title: 'Deb Testing', route: AppRoutes.debs),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _NavbarEntry extends StatelessWidget {
  const _NavbarEntry({required this.route, required this.title});

  final String route;
  final String title;

  @override
  Widget build(BuildContext context) {
    final pageUri = AppRoutes.uriFromContext(context);

    return InkWell(
      onTap: () {
        final destination =
            Uri.parse(route).replace(queryParameters: pageUri.queryParameters);
        context.go(destination.toString());
      },
      child: Container(
        color: GoRouterState.of(context).fullPath!.startsWith(route)
            ? YaruColors.orange
            : null,
        padding: const EdgeInsets.all(Spacing.level4),
        child: Text(
          title,
          style: Theme.of(context)
              .textTheme
              .titleLarge
              ?.apply(color: Colors.white),
        ),
      ),
    );
  }
}
