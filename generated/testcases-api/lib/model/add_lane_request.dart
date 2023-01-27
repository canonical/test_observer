//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.12

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AddLaneRequest {
  /// Returns a new [AddLaneRequest] instance.
  AddLaneRequest({
    this.pageId,
    this.name,
    this.status,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? pageId;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? name;

  /// Lane status
  AddLaneRequestStatusEnum? status;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AddLaneRequest &&
     other.pageId == pageId &&
     other.name == name &&
     other.status == status;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (pageId == null ? 0 : pageId!.hashCode) +
    (name == null ? 0 : name!.hashCode) +
    (status == null ? 0 : status!.hashCode);

  @override
  String toString() => 'AddLaneRequest[pageId=$pageId, name=$name, status=$status]';

  Map<String, dynamic> toJson() {
    final _json = <String, dynamic>{};
    if (pageId != null) {
      _json[r'pageId'] = pageId;
    }
    if (name != null) {
      _json[r'name'] = name;
    }
    if (status != null) {
      _json[r'status'] = status;
    }
    return _json;
  }

  /// Returns a new [AddLaneRequest] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AddLaneRequest? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AddLaneRequest[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AddLaneRequest[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AddLaneRequest(
        pageId: mapValueOfType<String>(json, r'pageId'),
        name: mapValueOfType<String>(json, r'name'),
        status: AddLaneRequestStatusEnum.fromJson(json[r'status']),
      );
    }
    return null;
  }

  static List<AddLaneRequest>? listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AddLaneRequest>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AddLaneRequest.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AddLaneRequest> mapFromJson(dynamic json) {
    final map = <String, AddLaneRequest>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AddLaneRequest.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AddLaneRequest-objects as value to a dart map
  static Map<String, List<AddLaneRequest>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AddLaneRequest>>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AddLaneRequest.listFromJson(entry.value, growable: growable,);
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

/// Lane status
class AddLaneRequestStatusEnum {
  /// Instantiate a new enum with the provided [value].
  const AddLaneRequestStatusEnum._(this.value);

  /// The underlying value of this enum member.
  final String value;

  @override
  String toString() => value;

  String toJson() => value;

  static const open = AddLaneRequestStatusEnum._(r'open');
  static const closed = AddLaneRequestStatusEnum._(r'closed');

  /// List of all possible values in this [enum][AddLaneRequestStatusEnum].
  static const values = <AddLaneRequestStatusEnum>[
    open,
    closed,
  ];

  static AddLaneRequestStatusEnum? fromJson(dynamic value) => AddLaneRequestStatusEnumTypeTransformer().decode(value);

  static List<AddLaneRequestStatusEnum>? listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AddLaneRequestStatusEnum>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AddLaneRequestStatusEnum.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }
}

/// Transformation class that can [encode] an instance of [AddLaneRequestStatusEnum] to String,
/// and [decode] dynamic data back to [AddLaneRequestStatusEnum].
class AddLaneRequestStatusEnumTypeTransformer {
  factory AddLaneRequestStatusEnumTypeTransformer() => _instance ??= const AddLaneRequestStatusEnumTypeTransformer._();

  const AddLaneRequestStatusEnumTypeTransformer._();

  String encode(AddLaneRequestStatusEnum data) => data.value;

  /// Decodes a [dynamic value][data] to a AddLaneRequestStatusEnum.
  ///
  /// If [allowNull] is true and the [dynamic value][data] cannot be decoded successfully,
  /// then null is returned. However, if [allowNull] is false and the [dynamic value][data]
  /// cannot be decoded successfully, then an [UnimplementedError] is thrown.
  ///
  /// The [allowNull] is very handy when an API changes and a new enum value is added or removed,
  /// and users are still using an old app with the old code.
  AddLaneRequestStatusEnum? decode(dynamic data, {bool allowNull = true}) {
    if (data != null) {
      switch (data.toString()) {
        case r'open': return AddLaneRequestStatusEnum.open;
        case r'closed': return AddLaneRequestStatusEnum.closed;
        default:
          if (!allowNull) {
            throw ArgumentError('Unknown enum value to decode: $data');
          }
      }
    }
    return null;
  }

  /// Singleton [AddLaneRequestStatusEnumTypeTransformer] instance.
  static AddLaneRequestStatusEnumTypeTransformer? _instance;
}


