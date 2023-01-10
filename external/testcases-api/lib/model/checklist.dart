//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.12

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class Checklist {
  /// Returns a new [Checklist] instance.
  Checklist({
    required this.id,
    required this.name,
    this.cardId,
    required this.boardId,
    this.checklistItems = const [],
  });

  String id;

  String name;

  /// Id of the card where checklist is located
  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? cardId;

  String boardId;

  List<CheckItem> checklistItems;

  @override
  bool operator ==(Object other) => identical(this, other) || other is Checklist &&
     other.id == id &&
     other.name == name &&
     other.cardId == cardId &&
     other.boardId == boardId &&
     other.checklistItems == checklistItems;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (id.hashCode) +
    (name.hashCode) +
    (cardId == null ? 0 : cardId!.hashCode) +
    (boardId.hashCode) +
    (checklistItems.hashCode);

  @override
  String toString() => 'Checklist[id=$id, name=$name, cardId=$cardId, boardId=$boardId, checklistItems=$checklistItems]';

  Map<String, dynamic> toJson() {
    final _json = <String, dynamic>{};
      _json[r'id'] = id;
      _json[r'name'] = name;
    if (cardId != null) {
      _json[r'cardId'] = cardId;
    }
      _json[r'boardId'] = boardId;
      _json[r'checklistItems'] = checklistItems;
    return _json;
  }

  /// Returns a new [Checklist] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static Checklist? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "Checklist[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "Checklist[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return Checklist(
        id: mapValueOfType<String>(json, r'id')!,
        name: mapValueOfType<String>(json, r'name')!,
        cardId: mapValueOfType<String>(json, r'cardId'),
        boardId: mapValueOfType<String>(json, r'boardId')!,
        checklistItems: CheckItem.listFromJson(json[r'checklistItems']) ?? const [],
      );
    }
    return null;
  }

  static List<Checklist>? listFromJson(dynamic json, {bool growable = false,}) {
    final result = <Checklist>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = Checklist.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, Checklist> mapFromJson(dynamic json) {
    final map = <String, Checklist>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = Checklist.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of Checklist-objects as value to a dart map
  static Map<String, List<Checklist>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<Checklist>>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = Checklist.listFromJson(entry.value, growable: growable,);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
    'id',
    'name',
    'boardId',
  };
}

