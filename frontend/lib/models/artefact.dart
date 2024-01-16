import 'package:flutter/material.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:yaru/yaru.dart';

import 'stage_name.dart';
import 'user.dart';

part 'artefact.freezed.dart';
part 'artefact.g.dart';

@freezed
class Artefact with _$Artefact {
  const Artefact._();

  const factory Artefact({
    required int id,
    required String name,
    required String version,
    @Default(null) String? track,
    @Default(null) String? store,
    @Default(null) String? series,
    @Default(null) String? repo,
    required ArtefactStatus status,
    required StageName stage,
    required User? assignee,
  }) = _Artefact;

  factory Artefact.fromJson(Map<String, Object?> json) =>
      _$ArtefactFromJson(json);

  Map<String, String> get details => {
        'version': version,
        if (track != null) 'track': track!,
        if (store != null) 'store': store!,
        if (series != null) 'series': series!,
        if (repo != null) 'repo': repo!,
      };
}

enum ArtefactStatus {
  @JsonValue('APPROVED')
  approved,
  @JsonValue('MARKED_AS_FAILED')
  rejected,
  @JsonValue('UNDECIDED')
  undecided;

  String get name {
    switch (this) {
      case approved:
        return 'Approved';
      case rejected:
        return 'Rejected';
      case undecided:
        return 'Undecided';
    }
  }

  Color get color {
    switch (this) {
      case approved:
        return YaruColors.light.success;
      case rejected:
        return YaruColors.red;
      case undecided:
        return YaruColors.textGrey;
    }
  }

  String toJson() {
    switch (this) {
      case approved:
        return 'APPROVED';
      case rejected:
        return 'MARKED_AS_FAILED';
      case undecided:
        return 'UNDECIDED';
    }
  }
}
