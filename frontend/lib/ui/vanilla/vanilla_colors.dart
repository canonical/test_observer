// Copyright (C) 2023-2025 Canonical Ltd.
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

import 'dart:ui';

// Colors follow Vanilla color naming scheme found in the repo below
// https://github.com/canonical/vanilla-framework/tree/main/tokens/color/light
class VanillaColors {
  static const basePositive = Color(0xff0e8420);
  static const baseNegative = Color(0xffc7162b);
  static const baseCaution = Color(0xffcc7900);
  static const baseInformation = Color(0xff24598f);
  static const backgroundActive = Color(0xffebebeb);
  static const backgroundCautionDefault = Color.fromRGBO(199, 90, 0, 0.1);
  static const backgroundCheckboxChecked = Color(0xff0066cc);
  static const backgroundDefault = Color(0xffffffff);
  static const backgroundHover = Color(0xfff2f2f2);
  static const backgroundInput = Color(0xfff5f5f5);
  static const backgroundInformationDefault = Color.fromRGBO(0, 99, 199, 0.1);
  static const backgroundNegativeDefault = Color.fromRGBO(199, 0, 20, 0.1);
  static const backgroundNeutralDefault = Color(0xfff2f2f2);
  static const backgroundOverlay = Color.fromRGBO(17, 17, 17, 0.85);
  static const backgroundPositiveDefault = Color.fromRGBO(10, 189, 37, 0.1);
  static const borderDefault = Color.fromRGBO(0, 0, 0, 0.2);
  static const borderHighContrast = Color.fromRGBO(0, 0, 0, 0.56);
  static const borderPositive = basePositive;
  static const borderNegative = baseNegative;
  static const borderCaution = baseCaution;
  static const borderInformation = baseInformation;
  static const borderNeutral = Color.fromRGBO(0, 0, 0, 0.56);
  static const textDefault = Color(0xff000000);
  static const textButtonPositive = Color(0xffffffff);
  static const textButtonNegative = Color(0xffffffff);
  static const buttonPositiveHover = Color(0xff0c6d1a);
  static const buttonNegativeHover = Color(0xffb01326);
  static const darkBackgroundDefault = Color(0xff262626);
  static const darkBackgroundHover = Color.fromRGBO(255, 255, 255, 0.05);
  static const darkTextDefault = Color(0xffffffff);
  static const darkBorderHighlight = Color(0xffffffff);
}
