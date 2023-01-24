import 'package:flutter/material.dart';
import 'package:yaru_colors/yaru_colors.dart';

enum BuildStatus {
  failed,
  inProgress,
  success;

  Color get color {
    switch (this) {
      case failed:
        return YaruColors.error;

      case success:
        return YaruColors.success;

      default:
        return YaruColors.warmGrey;
    }
  }

  @override
  String toString() => name;
}
