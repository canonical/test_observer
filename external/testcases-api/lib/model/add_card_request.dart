//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.12

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AddCardRequest {
  /// Returns a new [AddCardRequest] instance.
  AddCardRequest({
    this.name,
    this.listId,
    this.boardId,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? name;

  /// ID of the list where the card is located
  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? listId;

  /// Id of the board where the card is located
  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? boardId;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AddCardRequest &&
     other.name == name &&
     other.listId == listId &&
     other.boardId == boardId;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (name == null ? 0 : name!.hashCode) +
    (listId == null ? 0 : listId!.hashCode) +
    (boardId == null ? 0 : boardId!.hashCode);

  @override
  String toString() => 'AddCardRequest[name=$name, listId=$listId, boardId=$boardId]';

  Map<String, dynamic> toJson() {
    final _json = <String, dynamic>{};
    if (name != null) {
      _json[r'name'] = name;
    }
    if (listId != null) {
      _json[r'listId'] = listId;
    }
    if (boardId != null) {
      _json[r'boardId'] = boardId;
    }
    return _json;
  }

  /// Returns a new [AddCardRequest] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AddCardRequest? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AddCardRequest[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AddCardRequest[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AddCardRequest(
        name: mapValueOfType<String>(json, r'name'),
        listId: mapValueOfType<String>(json, r'listId'),
        boardId: mapValueOfType<String>(json, r'boardId'),
      );
    }
    return null;
  }

  static List<AddCardRequest>? listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AddCardRequest>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AddCardRequest.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AddCardRequest> mapFromJson(dynamic json) {
    final map = <String, AddCardRequest>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AddCardRequest.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AddCardRequest-objects as value to a dart map
  static Map<String, List<AddCardRequest>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AddCardRequest>>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AddCardRequest.listFromJson(entry.value, growable: growable,);
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

