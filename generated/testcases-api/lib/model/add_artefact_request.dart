//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.12

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AddArtefactRequest {
  /// Returns a new [AddArtefactRequest] instance.
  AddArtefactRequest({
    this.name,
    this.source_,
    this.version,
    this.series,
    this.architecture = const [],
    this.laneId,
    this.pageId,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? name;

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
  String? version;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? series;

  List<String> architecture;

  /// ID of the lane where the artefact is located
  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? laneId;

  /// Id of the page where the artefact is located
  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? pageId;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AddArtefactRequest &&
     other.name == name &&
     other.source_ == source_ &&
     other.version == version &&
     other.series == series &&
     other.architecture == architecture &&
     other.laneId == laneId &&
     other.pageId == pageId;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (name == null ? 0 : name!.hashCode) +
    (source_ == null ? 0 : source_!.hashCode) +
    (version == null ? 0 : version!.hashCode) +
    (series == null ? 0 : series!.hashCode) +
    (architecture.hashCode) +
    (laneId == null ? 0 : laneId!.hashCode) +
    (pageId == null ? 0 : pageId!.hashCode);

  @override
  String toString() => 'AddArtefactRequest[name=$name, source_=$source_, version=$version, series=$series, architecture=$architecture, laneId=$laneId, pageId=$pageId]';

  Map<String, dynamic> toJson() {
    final _json = <String, dynamic>{};
    if (name != null) {
      _json[r'name'] = name;
    }
    if (source_ != null) {
      _json[r'source'] = source_;
    }
    if (version != null) {
      _json[r'version'] = version;
    }
    if (series != null) {
      _json[r'series'] = series;
    }
      _json[r'architecture'] = architecture;
    if (laneId != null) {
      _json[r'laneId'] = laneId;
    }
    if (pageId != null) {
      _json[r'pageId'] = pageId;
    }
    return _json;
  }

  /// Returns a new [AddArtefactRequest] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AddArtefactRequest? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AddArtefactRequest[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AddArtefactRequest[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AddArtefactRequest(
        name: mapValueOfType<String>(json, r'name'),
        source_: mapValueOfType<String>(json, r'source'),
        version: mapValueOfType<String>(json, r'version'),
        series: mapValueOfType<String>(json, r'series'),
        architecture: json[r'architecture'] is List
            ? (json[r'architecture'] as List).cast<String>()
            : const [],
        laneId: mapValueOfType<String>(json, r'laneId'),
        pageId: mapValueOfType<String>(json, r'pageId'),
      );
    }
    return null;
  }

  static List<AddArtefactRequest>? listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AddArtefactRequest>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AddArtefactRequest.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AddArtefactRequest> mapFromJson(dynamic json) {
    final map = <String, AddArtefactRequest>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AddArtefactRequest.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AddArtefactRequest-objects as value to a dart map
  static Map<String, List<AddArtefactRequest>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AddArtefactRequest>>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AddArtefactRequest.listFromJson(entry.value, growable: growable,);
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

