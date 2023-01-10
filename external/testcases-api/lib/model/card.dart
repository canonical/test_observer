//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.12

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class Card {
  /// Returns a new [Card] instance.
  Card({
    required this.id,
    required this.name,
    required this.listId,
    required this.boardId,
    required this.status,
    this.checklistsIds = const [],
    this.labels = const [],
    this.comments = const [],
  });

  String id;

  String name;

  /// ID of the list where the card is located
  String listId;

  String boardId;

  /// List status
  CardStatusEnum status;

  List<String> checklistsIds;

  List<Label> labels;

  List<Comment> comments;

  @override
  bool operator ==(Object other) => identical(this, other) || other is Card &&
     other.id == id &&
     other.name == name &&
     other.listId == listId &&
     other.boardId == boardId &&
     other.status == status &&
     other.checklistsIds == checklistsIds &&
     other.labels == labels &&
     other.comments == comments;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (id.hashCode) +
    (name.hashCode) +
    (listId.hashCode) +
    (boardId.hashCode) +
    (status.hashCode) +
    (checklistsIds.hashCode) +
    (labels.hashCode) +
    (comments.hashCode);

  @override
  String toString() => 'Card[id=$id, name=$name, listId=$listId, boardId=$boardId, status=$status, checklistsIds=$checklistsIds, labels=$labels, comments=$comments]';

  Map<String, dynamic> toJson() {
    final _json = <String, dynamic>{};
      _json[r'id'] = id;
      _json[r'name'] = name;
      _json[r'listId'] = listId;
      _json[r'boardId'] = boardId;
      _json[r'status'] = status;
      _json[r'checklistsIds'] = checklistsIds;
      _json[r'labels'] = labels;
      _json[r'comments'] = comments;
    return _json;
  }

  /// Returns a new [Card] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static Card? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "Card[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "Card[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return Card(
        id: mapValueOfType<String>(json, r'id')!,
        name: mapValueOfType<String>(json, r'name')!,
        listId: mapValueOfType<String>(json, r'listId')!,
        boardId: mapValueOfType<String>(json, r'boardId')!,
        status: CardStatusEnum.fromJson(json[r'status'])!,
        checklistsIds: json[r'checklistsIds'] is List
            ? (json[r'checklistsIds'] as List).cast<String>()
            : const [],
        labels: Label.listFromJson(json[r'labels']) ?? const [],
        comments: Comment.listFromJson(json[r'comments']) ?? const [],
      );
    }
    return null;
  }

  static List<Card>? listFromJson(dynamic json, {bool growable = false,}) {
    final result = <Card>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = Card.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, Card> mapFromJson(dynamic json) {
    final map = <String, Card>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = Card.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of Card-objects as value to a dart map
  static Map<String, List<Card>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<Card>>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = Card.listFromJson(entry.value, growable: growable,);
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
    'listId',
    'boardId',
    'status',
  };
}

/// List status
class CardStatusEnum {
  /// Instantiate a new enum with the provided [value].
  const CardStatusEnum._(this.value);

  /// The underlying value of this enum member.
  final String value;

  @override
  String toString() => value;

  String toJson() => value;

  static const open = CardStatusEnum._(r'open');
  static const closed = CardStatusEnum._(r'closed');

  /// List of all possible values in this [enum][CardStatusEnum].
  static const values = <CardStatusEnum>[
    open,
    closed,
  ];

  static CardStatusEnum? fromJson(dynamic value) => CardStatusEnumTypeTransformer().decode(value);

  static List<CardStatusEnum>? listFromJson(dynamic json, {bool growable = false,}) {
    final result = <CardStatusEnum>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = CardStatusEnum.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }
}

/// Transformation class that can [encode] an instance of [CardStatusEnum] to String,
/// and [decode] dynamic data back to [CardStatusEnum].
class CardStatusEnumTypeTransformer {
  factory CardStatusEnumTypeTransformer() => _instance ??= const CardStatusEnumTypeTransformer._();

  const CardStatusEnumTypeTransformer._();

  String encode(CardStatusEnum data) => data.value;

  /// Decodes a [dynamic value][data] to a CardStatusEnum.
  ///
  /// If [allowNull] is true and the [dynamic value][data] cannot be decoded successfully,
  /// then null is returned. However, if [allowNull] is false and the [dynamic value][data]
  /// cannot be decoded successfully, then an [UnimplementedError] is thrown.
  ///
  /// The [allowNull] is very handy when an API changes and a new enum value is added or removed,
  /// and users are still using an old app with the old code.
  CardStatusEnum? decode(dynamic data, {bool allowNull = true}) {
    if (data != null) {
      switch (data.toString()) {
        case r'open': return CardStatusEnum.open;
        case r'closed': return CardStatusEnum.closed;
        default:
          if (!allowNull) {
            throw ArgumentError('Unknown enum value to decode: $data');
          }
      }
    }
    return null;
  }

  /// Singleton [CardStatusEnumTypeTransformer] instance.
  static CardStatusEnumTypeTransformer? _instance;
}


