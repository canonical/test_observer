import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:yaru/yaru.dart';

import '../spacing.dart';

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
          Expanded(
            child: Row(
              children: navbarEntries
                  .map(
                    (entry) => Container(
                      color: GoRouter.of(context).location == entry.url
                          ? YaruColors.orange
                          : null,
                      padding: const EdgeInsets.all(Spacing.level4),
                      child: Text(
                        entry.title,
                        style: Theme.of(context)
                            .textTheme
                            .titleLarge
                            ?.apply(color: Colors.white),
                      ),
                    ),
                  )
                  .toList(),
            ),
          ),
        ],
      ),
    );
  }
}

class _NavbarEntry {
  final String title;
  final String url;

  const _NavbarEntry(this.title, this.url);
}

const navbarEntries = [_NavbarEntry('Snap Testing', '/snaps')];
