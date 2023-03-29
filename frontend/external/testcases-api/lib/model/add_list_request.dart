//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.12

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AddListRequest {
  /// Returns a new [AddListRequest] instance.
  AddListRequest({
    this.boardId,
    this.name,
    this.status,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? boardId;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? name;

  /// List status
  AddListRequestStatusEnum? status;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AddListRequest &&
     other.boardId == boardId &&
     other.name == name &&
     other.status == status;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (boardId == null ? 0 : boardId!.hashCode) +
    (name == null ? 0 : name!.hashCode) +
    (status == null ? 0 : status!.hashCode);

  @override
  String toString() => 'AddListRequest[boardId=$boardId, name=$name, status=$status]';

  Map<String, dynamic> toJson() {
    final _json = <String, dynamic>{};
    if (boardId != null) {
      _json[r'boardId'] = boardId;
    }
    if (name != null) {
      _json[r'name'] = name;
    }
    if (status != null) {
      _json[r'status'] = status;
    }
    return _json;
  }

  /// Returns a new [AddListRequest] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AddListRequest? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AddListRequest[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AddListRequest[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AddListRequest(
        boardId: mapValueOfType<String>(json, r'boardId'),
        name: mapValueOfType<String>(json, r'name'),
        status: AddListRequestStatusEnum.fromJson(json[r'status']),
      );
    }
    return null;
  }

  static List<AddListRequest>? listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AddListRequest>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AddListRequest.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AddListRequest> mapFromJson(dynamic json) {
    final map = <String, AddListRequest>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AddListRequest.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AddListRequest-objects as value to a dart map
  static Map<String, List<AddListRequest>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AddListRequest>>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AddListRequest.listFromJson(entry.value, growable: growable,);
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

/// List status
class AddListRequestStatusEnum {
  /// Instantiate a new enum with the provided [value].
  const AddListRequestStatusEnum._(this.value);

  /// The underlying value of this enum member.
  final String value;

  @override
  String toString() => value;

  String toJson() => value;

  static const open = AddListRequestStatusEnum._(r'open');
  static const closed = AddListRequestStatusEnum._(r'closed');

  /// List of all possible values in this [enum][AddListRequestStatusEnum].
  static const values = <AddListRequestStatusEnum>[
    open,
    closed,
  ];

  static AddListRequestStatusEnum? fromJson(dynamic value) => AddListRequestStatusEnumTypeTransformer().decode(value);

  static List<AddListRequestStatusEnum>? listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AddListRequestStatusEnum>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AddListRequestStatusEnum.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }
}

/// Transformation class that can [encode] an instance of [AddListRequestStatusEnum] to String,
/// and [decode] dynamic data back to [AddListRequestStatusEnum].
class AddListRequestStatusEnumTypeTransformer {
  factory AddListRequestStatusEnumTypeTransformer() => _instance ??= const AddListRequestStatusEnumTypeTransformer._();

  const AddListRequestStatusEnumTypeTransformer._();

  String encode(AddListRequestStatusEnum data) => data.value;

  /// Decodes a [dynamic value][data] to a AddListRequestStatusEnum.
  ///
  /// If [allowNull] is true and the [dynamic value][data] cannot be decoded successfully,
  /// then null is returned. However, if [allowNull] is false and the [dynamic value][data]
  /// cannot be decoded successfully, then an [UnimplementedError] is thrown.
  ///
  /// The [allowNull] is very handy when an API changes and a new enum value is added or removed,
  /// and users are still using an old app with the old code.
  AddListRequestStatusEnum? decode(dynamic data, {bool allowNull = true}) {
    if (data != null) {
      switch (data.toString()) {
        case r'open': return AddListRequestStatusEnum.open;
        case r'closed': return AddListRequestStatusEnum.closed;
        default:
          if (!allowNull) {
            throw ArgumentError('Unknown enum value to decode: $data');
          }
      }
    }
    return null;
  }

  /// Singleton [AddListRequestStatusEnumTypeTransformer] instance.
  static AddListRequestStatusEnumTypeTransformer? _instance;
}


