//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.12

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class Board {
  /// Returns a new [Board] instance.
  Board({
    required this.id,
    required this.name,
    required this.status,
  });

  String id;

  String name;

  /// Board status
  BoardStatusEnum status;

  @override
  bool operator ==(Object other) => identical(this, other) || other is Board &&
     other.id == id &&
     other.name == name &&
     other.status == status;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (id.hashCode) +
    (name.hashCode) +
    (status.hashCode);

  @override
  String toString() => 'Board[id=$id, name=$name, status=$status]';

  Map<String, dynamic> toJson() {
    final _json = <String, dynamic>{};
      _json[r'id'] = id;
      _json[r'name'] = name;
      _json[r'status'] = status;
    return _json;
  }

  /// Returns a new [Board] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static Board? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "Board[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "Board[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return Board(
        id: mapValueOfType<String>(json, r'id')!,
        name: mapValueOfType<String>(json, r'name')!,
        status: BoardStatusEnum.fromJson(json[r'status'])!,
      );
    }
    return null;
  }

  static List<Board>? listFromJson(dynamic json, {bool growable = false,}) {
    final result = <Board>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = Board.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, Board> mapFromJson(dynamic json) {
    final map = <String, Board>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = Board.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of Board-objects as value to a dart map
  static Map<String, List<Board>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<Board>>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = Board.listFromJson(entry.value, growable: growable,);
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
    'status',
  };
}

/// Board status
class BoardStatusEnum {
  /// Instantiate a new enum with the provided [value].
  const BoardStatusEnum._(this.value);

  /// The underlying value of this enum member.
  final String value;

  @override
  String toString() => value;

  String toJson() => value;

  static const open = BoardStatusEnum._(r'open');
  static const closed = BoardStatusEnum._(r'closed');

  /// List of all possible values in this [enum][BoardStatusEnum].
  static const values = <BoardStatusEnum>[
    open,
    closed,
  ];

  static BoardStatusEnum? fromJson(dynamic value) => BoardStatusEnumTypeTransformer().decode(value);

  static List<BoardStatusEnum>? listFromJson(dynamic json, {bool growable = false,}) {
    final result = <BoardStatusEnum>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = BoardStatusEnum.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }
}

/// Transformation class that can [encode] an instance of [BoardStatusEnum] to String,
/// and [decode] dynamic data back to [BoardStatusEnum].
class BoardStatusEnumTypeTransformer {
  factory BoardStatusEnumTypeTransformer() => _instance ??= const BoardStatusEnumTypeTransformer._();

  const BoardStatusEnumTypeTransformer._();

  String encode(BoardStatusEnum data) => data.value;

  /// Decodes a [dynamic value][data] to a BoardStatusEnum.
  ///
  /// If [allowNull] is true and the [dynamic value][data] cannot be decoded successfully,
  /// then null is returned. However, if [allowNull] is false and the [dynamic value][data]
  /// cannot be decoded successfully, then an [UnimplementedError] is thrown.
  ///
  /// The [allowNull] is very handy when an API changes and a new enum value is added or removed,
  /// and users are still using an old app with the old code.
  BoardStatusEnum? decode(dynamic data, {bool allowNull = true}) {
    if (data != null) {
      switch (data.toString()) {
        case r'open': return BoardStatusEnum.open;
        case r'closed': return BoardStatusEnum.closed;
        default:
          if (!allowNull) {
            throw ArgumentError('Unknown enum value to decode: $data');
          }
      }
    }
    return null;
  }

  /// Singleton [BoardStatusEnumTypeTransformer] instance.
  static BoardStatusEnumTypeTransformer? _instance;
}


