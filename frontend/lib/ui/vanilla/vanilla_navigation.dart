import 'package:flutter/material.dart';

import '../spacing.dart';
import 'vanilla_colors.dart';

const navigationBarHeight = 55.0;

class VanillaNavigation extends StatelessWidget {
  const VanillaNavigation({super.key, required this.children});

  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding:
          const EdgeInsets.symmetric(horizontal: Spacing.pageHorizontalPadding),
      color: VanillaColors.darkBackgroundDefault,
      height: navigationBarHeight,
      child: Row(
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
  const VanillaNavigationTitle({
    super.key,
    required this.title,
    this.onPressed,
  });

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

class VanillaNavigationDropdown extends StatelessWidget {
  const VanillaNavigationDropdown({
    super.key,
    required this.menuChildren,
    required this.child,
  });

  final List<Widget> menuChildren;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: navigationBarHeight,
      child: SubmenuButton(
        style: const ButtonStyle(
          padding: WidgetStatePropertyAll(EdgeInsets.all(Spacing.level4)),
          foregroundColor:
              WidgetStatePropertyAll(VanillaColors.darkTextDefault),
          overlayColor:
              WidgetStatePropertyAll(VanillaColors.darkBackgroundHover),
        ),
        menuStyle: const MenuStyle(
          shape: WidgetStatePropertyAll(RoundedRectangleBorder()),
          backgroundColor:
              WidgetStatePropertyAll(VanillaColors.darkBackgroundDefault),
        ),
        menuChildren: menuChildren,
        child: child,
      ),
    );
  }
}
