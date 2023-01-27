//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.12

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AddArtefactGroupRequest {
  /// Returns a new [AddArtefactGroupRequest] instance.
  AddArtefactGroupRequest({
    this.name,
    this.versionPattern,
    this.source_,
    this.series,
    this.architectures = const [],
    this.pageId,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? name;

  /// More useful for kernels
  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? versionPattern;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? source_;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? series;

  List<String> architectures;

  /// Id of the page where the artefact_group is located
  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? pageId;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AddArtefactGroupRequest &&
     other.name == name &&
     other.versionPattern == versionPattern &&
     other.source_ == source_ &&
     other.series == series &&
     other.architectures == architectures &&
     other.pageId == pageId;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (name == null ? 0 : name!.hashCode) +
    (versionPattern == null ? 0 : versionPattern!.hashCode) +
    (source_ == null ? 0 : source_!.hashCode) +
    (series == null ? 0 : series!.hashCode) +
    (architectures.hashCode) +
    (pageId == null ? 0 : pageId!.hashCode);

  @override
  String toString() => 'AddArtefactGroupRequest[name=$name, versionPattern=$versionPattern, source_=$source_, series=$series, architectures=$architectures, pageId=$pageId]';

  Map<String, dynamic> toJson() {
    final _json = <String, dynamic>{};
    if (name != null) {
      _json[r'name'] = name;
    }
    if (versionPattern != null) {
      _json[r'versionPattern'] = versionPattern;
    }
    if (source_ != null) {
      _json[r'source'] = source_;
    }
    if (series != null) {
      _json[r'series'] = series;
    }
      _json[r'architectures'] = architectures;
    if (pageId != null) {
      _json[r'pageId'] = pageId;
    }
    return _json;
  }

  /// Returns a new [AddArtefactGroupRequest] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AddArtefactGroupRequest? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AddArtefactGroupRequest[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AddArtefactGroupRequest[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AddArtefactGroupRequest(
        name: mapValueOfType<String>(json, r'name'),
        versionPattern: mapValueOfType<String>(json, r'versionPattern'),
        source_: mapValueOfType<String>(json, r'source'),
        series: mapValueOfType<String>(json, r'series'),
        architectures: json[r'architectures'] is List
            ? (json[r'architectures'] as List).cast<String>()
            : const [],
        pageId: mapValueOfType<String>(json, r'pageId'),
      );
    }
    return null;
  }

  static List<AddArtefactGroupRequest>? listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AddArtefactGroupRequest>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AddArtefactGroupRequest.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AddArtefactGroupRequest> mapFromJson(dynamic json) {
    final map = <String, AddArtefactGroupRequest>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AddArtefactGroupRequest.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AddArtefactGroupRequest-objects as value to a dart map
  static Map<String, List<AddArtefactGroupRequest>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AddArtefactGroupRequest>>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AddArtefactGroupRequest.listFromJson(entry.value, growable: growable,);
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

