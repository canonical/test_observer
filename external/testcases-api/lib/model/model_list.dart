//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.12

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class ModelList {
  /// Returns a new [ModelList] instance.
  ModelList({
    required this.id,
    required this.boardId,
    required this.name,
    required this.status,
  });

  String id;

  String boardId;

  String name;

  /// List status
  ModelListStatusEnum status;

  @override
  bool operator ==(Object other) => identical(this, other) || other is ModelList &&
     other.id == id &&
     other.boardId == boardId &&
     other.name == name &&
     other.status == status;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (id.hashCode) +
    (boardId.hashCode) +
    (name.hashCode) +
    (status.hashCode);

  @override
  String toString() => 'ModelList[id=$id, boardId=$boardId, name=$name, status=$status]';

  Map<String, dynamic> toJson() {
    final _json = <String, dynamic>{};
      _json[r'id'] = id;
      _json[r'boardId'] = boardId;
      _json[r'name'] = name;
      _json[r'status'] = status;
    return _json;
  }

  /// Returns a new [ModelList] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static ModelList? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "ModelList[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "ModelList[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return ModelList(
        id: mapValueOfType<String>(json, r'id')!,
        boardId: mapValueOfType<String>(json, r'boardId')!,
        name: mapValueOfType<String>(json, r'name')!,
        status: ModelListStatusEnum.fromJson(json[r'status'])!,
      );
    }
    return null;
  }

  static List<ModelList>? listFromJson(dynamic json, {bool growable = false,}) {
    final result = <ModelList>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = ModelList.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, ModelList> mapFromJson(dynamic json) {
    final map = <String, ModelList>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = ModelList.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of ModelList-objects as value to a dart map
  static Map<String, List<ModelList>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<ModelList>>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = ModelList.listFromJson(entry.value, growable: growable,);
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
    'boardId',
    'name',
    'status',
  };
}

/// List status
class ModelListStatusEnum {
  /// Instantiate a new enum with the provided [value].
  const ModelListStatusEnum._(this.value);

  /// The underlying value of this enum member.
  final String value;

  @override
  String toString() => value;

  String toJson() => value;

  static const open = ModelListStatusEnum._(r'open');
  static const closed = ModelListStatusEnum._(r'closed');

  /// List of all possible values in this [enum][ModelListStatusEnum].
  static const values = <ModelListStatusEnum>[
    open,
    closed,
  ];

  static ModelListStatusEnum? fromJson(dynamic value) => ModelListStatusEnumTypeTransformer().decode(value);

  static List<ModelListStatusEnum>? listFromJson(dynamic json, {bool growable = false,}) {
    final result = <ModelListStatusEnum>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = ModelListStatusEnum.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }
}

/// Transformation class that can [encode] an instance of [ModelListStatusEnum] to String,
/// and [decode] dynamic data back to [ModelListStatusEnum].
class ModelListStatusEnumTypeTransformer {
  factory ModelListStatusEnumTypeTransformer() => _instance ??= const ModelListStatusEnumTypeTransformer._();

  const ModelListStatusEnumTypeTransformer._();

  String encode(ModelListStatusEnum data) => data.value;

  /// Decodes a [dynamic value][data] to a ModelListStatusEnum.
  ///
  /// If [allowNull] is true and the [dynamic value][data] cannot be decoded successfully,
  /// then null is returned. However, if [allowNull] is false and the [dynamic value][data]
  /// cannot be decoded successfully, then an [UnimplementedError] is thrown.
  ///
  /// The [allowNull] is very handy when an API changes and a new enum value is added or removed,
  /// and users are still using an old app with the old code.
  ModelListStatusEnum? decode(dynamic data, {bool allowNull = true}) {
    if (data != null) {
      switch (data.toString()) {
        case r'open': return ModelListStatusEnum.open;
        case r'closed': return ModelListStatusEnum.closed;
        default:
          if (!allowNull) {
            throw ArgumentError('Unknown enum value to decode: $data');
          }
      }
    }
    return null;
  }

  /// Singleton [ModelListStatusEnumTypeTransformer] instance.
  static ModelListStatusEnumTypeTransformer? _instance;
}


