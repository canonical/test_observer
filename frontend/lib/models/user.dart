import 'package:dartx/dartx.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

part 'user.freezed.dart';
part 'user.g.dart';

@freezed
class User with _$User {
  const User._();

  const factory User({
    required int id,
    required String name,
    @JsonKey(name: 'launchpad_email') required String launchpadEmail,
    @JsonKey(name: 'launchpad_handle') required String launchpadHandle,
  }) = _User;

  factory User.fromJson(Map<String, Object?> json) => _$UserFromJson(json);

  String get initials {
    final names = name.split(' ');
    final numOfNames = names.length;
    switch (numOfNames) {
      case 0:
        return 'N/A';
      case 1:
        return names[0][0].capitalize();
      default:
        return names[0][0].capitalize() + names[numOfNames - 1][0].capitalize();
    }
  }
}
