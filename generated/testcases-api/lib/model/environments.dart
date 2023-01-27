//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.12

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class Environments {
  /// Returns a new [Environments] instance.
  Environments({
    required this.id,
    required this.name,
    this.artefactId,
    required this.pageId,
    this.environmentsItems = const [],
  });

  String id;

  String name;

  /// Id of the artefact where environments is located
  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? artefactId;

  String pageId;

  List<CheckItem> environmentsItems;

  @override
  bool operator ==(Object other) => identical(this, other) || other is Environments &&
     other.id == id &&
     other.name == name &&
     other.artefactId == artefactId &&
     other.pageId == pageId &&
     other.environmentsItems == environmentsItems;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (id.hashCode) +
    (name.hashCode) +
    (artefactId == null ? 0 : artefactId!.hashCode) +
    (pageId.hashCode) +
    (environmentsItems.hashCode);

  @override
  String toString() => 'Environments[id=$id, name=$name, artefactId=$artefactId, pageId=$pageId, environmentsItems=$environmentsItems]';

  Map<String, dynamic> toJson() {
    final _json = <String, dynamic>{};
      _json[r'id'] = id;
      _json[r'name'] = name;
    if (artefactId != null) {
      _json[r'artefactId'] = artefactId;
    }
      _json[r'pageId'] = pageId;
      _json[r'environmentsItems'] = environmentsItems;
    return _json;
  }

  /// Returns a new [Environments] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static Environments? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "Environments[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "Environments[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return Environments(
        id: mapValueOfType<String>(json, r'id')!,
        name: mapValueOfType<String>(json, r'name')!,
        artefactId: mapValueOfType<String>(json, r'artefactId'),
        pageId: mapValueOfType<String>(json, r'pageId')!,
        environmentsItems: CheckItem.listFromJson(json[r'environmentsItems']) ?? const [],
      );
    }
    return null;
  }

  static List<Environments>? listFromJson(dynamic json, {bool growable = false,}) {
    final result = <Environments>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = Environments.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, Environments> mapFromJson(dynamic json) {
    final map = <String, Environments>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = Environments.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of Environments-objects as value to a dart map
  static Map<String, List<Environments>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<Environments>>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = Environments.listFromJson(entry.value, growable: growable,);
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
    'pageId',
  };
}

