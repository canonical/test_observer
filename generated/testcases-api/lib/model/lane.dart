//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.12

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class Lane {
  /// Returns a new [Lane] instance.
  Lane({
    required this.id,
    required this.pageId,
    required this.name,
    required this.status,
  });

  String id;

  String pageId;

  String name;

  /// Lane status
  LaneStatusEnum status;

  @override
  bool operator ==(Object other) => identical(this, other) || other is Lane &&
     other.id == id &&
     other.pageId == pageId &&
     other.name == name &&
     other.status == status;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (id.hashCode) +
    (pageId.hashCode) +
    (name.hashCode) +
    (status.hashCode);

  @override
  String toString() => 'Lane[id=$id, pageId=$pageId, name=$name, status=$status]';

  Map<String, dynamic> toJson() {
    final _json = <String, dynamic>{};
      _json[r'id'] = id;
      _json[r'pageId'] = pageId;
      _json[r'name'] = name;
      _json[r'status'] = status;
    return _json;
  }

  /// Returns a new [Lane] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static Lane? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "Lane[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "Lane[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return Lane(
        id: mapValueOfType<String>(json, r'id')!,
        pageId: mapValueOfType<String>(json, r'pageId')!,
        name: mapValueOfType<String>(json, r'name')!,
        status: LaneStatusEnum.fromJson(json[r'status'])!,
      );
    }
    return null;
  }

  static List<Lane>? listFromJson(dynamic json, {bool growable = false,}) {
    final result = <Lane>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = Lane.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, Lane> mapFromJson(dynamic json) {
    final map = <String, Lane>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = Lane.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of Lane-objects as value to a dart map
  static Map<String, List<Lane>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<Lane>>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = Lane.listFromJson(entry.value, growable: growable,);
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
    'pageId',
    'name',
    'status',
  };
}

/// Lane status
class LaneStatusEnum {
  /// Instantiate a new enum with the provided [value].
  const LaneStatusEnum._(this.value);

  /// The underlying value of this enum member.
  final String value;

  @override
  String toString() => value;

  String toJson() => value;

  static const open = LaneStatusEnum._(r'open');
  static const closed = LaneStatusEnum._(r'closed');

  /// List of all possible values in this [enum][LaneStatusEnum].
  static const values = <LaneStatusEnum>[
    open,
    closed,
  ];

  static LaneStatusEnum? fromJson(dynamic value) => LaneStatusEnumTypeTransformer().decode(value);

  static List<LaneStatusEnum>? listFromJson(dynamic json, {bool growable = false,}) {
    final result = <LaneStatusEnum>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = LaneStatusEnum.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }
}

/// Transformation class that can [encode] an instance of [LaneStatusEnum] to String,
/// and [decode] dynamic data back to [LaneStatusEnum].
class LaneStatusEnumTypeTransformer {
  factory LaneStatusEnumTypeTransformer() => _instance ??= const LaneStatusEnumTypeTransformer._();

  const LaneStatusEnumTypeTransformer._();

  String encode(LaneStatusEnum data) => data.value;

  /// Decodes a [dynamic value][data] to a LaneStatusEnum.
  ///
  /// If [allowNull] is true and the [dynamic value][data] cannot be decoded successfully,
  /// then null is returned. However, if [allowNull] is false and the [dynamic value][data]
  /// cannot be decoded successfully, then an [UnimplementedError] is thrown.
  ///
  /// The [allowNull] is very handy when an API changes and a new enum value is added or removed,
  /// and users are still using an old app with the old code.
  LaneStatusEnum? decode(dynamic data, {bool allowNull = true}) {
    if (data != null) {
      switch (data.toString()) {
        case r'open': return LaneStatusEnum.open;
        case r'closed': return LaneStatusEnum.closed;
        default:
          if (!allowNull) {
            throw ArgumentError('Unknown enum value to decode: $data');
          }
      }
    }
    return null;
  }

  /// Singleton [LaneStatusEnumTypeTransformer] instance.
  static LaneStatusEnumTypeTransformer? _instance;
}


