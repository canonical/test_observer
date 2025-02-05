import 'package:flutter/material.dart';

import '../spacing.dart';
import 'vanilla_colors.dart';

const navigationBarHeight = 55.0;

class VanillaNavigation extends StatelessWidget {
  const VanillaNavigation({super.key, required this.children});

  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: navigationBarHeight,
      width: double.infinity,
      child: MenuBar(
        style: const MenuStyle(
          padding: WidgetStatePropertyAll(
            EdgeInsets.symmetric(horizontal: Spacing.pageHorizontalPadding),
          ),
          shape: WidgetStatePropertyAll(RoundedRectangleBorder()),
          elevation: WidgetStatePropertyAll(0),
          backgroundColor:
              WidgetStatePropertyAll(VanillaColors.darkBackgroundDefault),
        ),
        children: children,
      ),
    );
  }
}

class VanillaNavigationButton extends StatelessWidget {
  const VanillaNavigationButton({
    super.key,
    required this.child,
    this.onPressed,
    this.isSelected = false,
  });

  final Widget child;
  final void Function()? onPressed;
  final bool isSelected;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: navigationBarHeight,
      child: MenuItemButton(
        style: ButtonStyle(
          padding: const WidgetStatePropertyAll(EdgeInsets.all(Spacing.level4)),
          foregroundColor:
              const WidgetStatePropertyAll(VanillaColors.darkTextDefault),
          overlayColor:
              const WidgetStatePropertyAll(VanillaColors.darkBackgroundHover),
          backgroundColor: isSelected
              ? const WidgetStatePropertyAll(VanillaColors.darkBackgroundHover)
              : null,
          shape: isSelected
              ? WidgetStatePropertyAll(
                  LinearBorder.bottom(
                    side: const BorderSide(
                      width: 3,
                      color: VanillaColors.darkBorderHighlight,
                    ),
                  ),
                )
              : null,
        ),
        onPressed: onPressed,
        child: child,
      ),
    );
  }
}

class VanillaNavigationTitle extends StatelessWidget {
  const VanillaNavigationTitle(
      {super.key, required this.title, this.onPressed});

  final String title;
  final void Function()? onPressed;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onPressed,
      child: Center(
        child: Padding(
          padding: const EdgeInsets.only(right: Spacing.level6),
          child: Text(
            title,
            style: Theme.of(context)
                .textTheme
                .headlineSmall
                ?.apply(color: VanillaColors.darkTextDefault),
          ),
        ),
      ),
    );
  }
}
