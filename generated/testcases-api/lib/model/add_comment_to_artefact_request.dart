//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.12

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AddCommentToArtefactRequest {
  /// Returns a new [AddCommentToArtefactRequest] instance.
  AddCommentToArtefactRequest({
    this.text,
  });

  /// Comment text
  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? text;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AddCommentToArtefactRequest &&
     other.text == text;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (text == null ? 0 : text!.hashCode);

  @override
  String toString() => 'AddCommentToArtefactRequest[text=$text]';

  Map<String, dynamic> toJson() {
    final _json = <String, dynamic>{};
    if (text != null) {
      _json[r'text'] = text;
    }
    return _json;
  }

  /// Returns a new [AddCommentToArtefactRequest] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AddCommentToArtefactRequest? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AddCommentToArtefactRequest[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AddCommentToArtefactRequest[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AddCommentToArtefactRequest(
        text: mapValueOfType<String>(json, r'text'),
      );
    }
    return null;
  }

  static List<AddCommentToArtefactRequest>? listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AddCommentToArtefactRequest>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AddCommentToArtefactRequest.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AddCommentToArtefactRequest> mapFromJson(dynamic json) {
    final map = <String, AddCommentToArtefactRequest>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AddCommentToArtefactRequest.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AddCommentToArtefactRequest-objects as value to a dart map
  static Map<String, List<AddCommentToArtefactRequest>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AddCommentToArtefactRequest>>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AddCommentToArtefactRequest.listFromJson(entry.value, growable: growable,);
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

