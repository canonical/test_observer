//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.12

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AddChecklistRequest {
  /// Returns a new [AddChecklistRequest] instance.
  AddChecklistRequest({
    this.name,
    this.cardId,
    this.boardId,
    this.checklistItems = const [],
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? name;

  /// Id of the card where checklist is located
  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? cardId;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? boardId;

  List<CheckItem> checklistItems;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AddChecklistRequest &&
     other.name == name &&
     other.cardId == cardId &&
     other.boardId == boardId &&
     other.checklistItems == checklistItems;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (name == null ? 0 : name!.hashCode) +
    (cardId == null ? 0 : cardId!.hashCode) +
    (boardId == null ? 0 : boardId!.hashCode) +
    (checklistItems.hashCode);

  @override
  String toString() => 'AddChecklistRequest[name=$name, cardId=$cardId, boardId=$boardId, checklistItems=$checklistItems]';

  Map<String, dynamic> toJson() {
    final _json = <String, dynamic>{};
    if (name != null) {
      _json[r'name'] = name;
    }
    if (cardId != null) {
      _json[r'cardId'] = cardId;
    }
    if (boardId != null) {
      _json[r'boardId'] = boardId;
    }
      _json[r'checklistItems'] = checklistItems;
    return _json;
  }

  /// Returns a new [AddChecklistRequest] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AddChecklistRequest? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AddChecklistRequest[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AddChecklistRequest[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AddChecklistRequest(
        name: mapValueOfType<String>(json, r'name'),
        cardId: mapValueOfType<String>(json, r'cardId'),
        boardId: mapValueOfType<String>(json, r'boardId'),
        checklistItems: CheckItem.listFromJson(json[r'checklistItems']) ?? const [],
      );
    }
    return null;
  }

  static List<AddChecklistRequest>? listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AddChecklistRequest>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AddChecklistRequest.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AddChecklistRequest> mapFromJson(dynamic json) {
    final map = <String, AddChecklistRequest>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AddChecklistRequest.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AddChecklistRequest-objects as value to a dart map
  static Map<String, List<AddChecklistRequest>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AddChecklistRequest>>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AddChecklistRequest.listFromJson(entry.value, growable: growable,);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

