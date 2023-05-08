import 'package:flutter/material.dart';
import 'package:yaru/yaru.dart';

import '../models/family.dart';
import '../spacing.dart';

class Navbar extends StatelessWidget {
  const Navbar({super.key});

  @override
  Widget build(BuildContext context) {
    const families = dummyFamilies;

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
              children: families
                  .map(
                    (family) => Container(
                      color: family == families[0] ? YaruColors.orange : null,
                      padding: const EdgeInsets.all(Spacing.level4),
                      child: Text(
                        family.name,
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
