// Copyright (C) 2023 Canonical Ltd.
//
// This file is part of Test Observer Frontend.
//
// Test Observer Frontend is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// Test Observer Frontend is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

import 'package:flutter/material.dart';

import 'vanilla_colors.dart';

class VanillaChip extends StatelessWidget {
  const VanillaChip({
    super.key,
    required this.text,
    this.type = VanillaChipType.normal,
  });

  final String text;
  final VanillaChipType type;

  @override
  Widget build(BuildContext context) {
    return Chip(
      label: Text(
        text,
        style: Theme.of(context).textTheme.labelMedium,
      ),
      shape: const StadiumBorder(),
      backgroundColor: type.color,
      side: BorderSide(color: type.borderColor),
    );
  }
}

enum VanillaChipType {
  normal,
  positive,
  negative,
  caution,
  information;

  Color get color {
    switch (this) {
      case normal:
        return VanillaColors.backgroundNeutralDefault;
      case positive:
        return VanillaColors.backgroundPositiveDefault;
      case negative:
        return VanillaColors.backgroundNegativeDefault;
      case caution:
        return VanillaColors.backgroundCautionDefault;
      case information:
        return VanillaColors.backgroundInformationDefault;
    }
  }

  Color get borderColor {
    switch (this) {
      case normal:
        return VanillaColors.borderNeutral;
      case positive:
        return VanillaColors.borderPositive;
      case negative:
        return VanillaColors.borderNegative;
      case caution:
        return VanillaColors.borderCaution;
      case information:
        return VanillaColors.borderInformation;
    }
  }
}
