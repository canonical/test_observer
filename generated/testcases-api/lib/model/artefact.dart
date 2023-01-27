//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.12

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class Artefact {
  /// Returns a new [Artefact] instance.
  Artefact({
    required this.id,
    required this.name,
    required this.laneId,
    required this.pageId,
    required this.status,
    this.environmentssIds = const [],
    this.labels = const [],
    this.comments = const [],
  });

  String id;

  String name;

  /// ID of the lane where the artefact is located
  String laneId;

  String pageId;

  /// Lane status
  ArtefactStatusEnum status;

  List<String> environmentssIds;

  List<Label> labels;

  List<Comment> comments;

  @override
  bool operator ==(Object other) => identical(this, other) || other is Artefact &&
     other.id == id &&
     other.name == name &&
     other.laneId == laneId &&
     other.pageId == pageId &&
     other.status == status &&
     other.environmentssIds == environmentssIds &&
     other.labels == labels &&
     other.comments == comments;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (id.hashCode) +
    (name.hashCode) +
    (laneId.hashCode) +
    (pageId.hashCode) +
    (status.hashCode) +
    (environmentssIds.hashCode) +
    (labels.hashCode) +
    (comments.hashCode);

  @override
  String toString() => 'Artefact[id=$id, name=$name, laneId=$laneId, pageId=$pageId, status=$status, environmentssIds=$environmentssIds, labels=$labels, comments=$comments]';

  Map<String, dynamic> toJson() {
    final _json = <String, dynamic>{};
      _json[r'id'] = id;
      _json[r'name'] = name;
      _json[r'laneId'] = laneId;
      _json[r'pageId'] = pageId;
      _json[r'status'] = status;
      _json[r'environmentssIds'] = environmentssIds;
      _json[r'labels'] = labels;
      _json[r'comments'] = comments;
    return _json;
  }

  /// Returns a new [Artefact] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static Artefact? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "Artefact[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "Artefact[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return Artefact(
        id: mapValueOfType<String>(json, r'id')!,
        name: mapValueOfType<String>(json, r'name')!,
        laneId: mapValueOfType<String>(json, r'laneId')!,
        pageId: mapValueOfType<String>(json, r'pageId')!,
        status: ArtefactStatusEnum.fromJson(json[r'status'])!,
        environmentssIds: json[r'environmentssIds'] is List
            ? (json[r'environmentssIds'] as List).cast<String>()
            : const [],
        labels: Label.listFromJson(json[r'labels']) ?? const [],
        comments: Comment.listFromJson(json[r'comments']) ?? const [],
      );
    }
    return null;
  }

  static List<Artefact>? listFromJson(dynamic json, {bool growable = false,}) {
    final result = <Artefact>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = Artefact.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, Artefact> mapFromJson(dynamic json) {
    final map = <String, Artefact>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = Artefact.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of Artefact-objects as value to a dart map
  static Map<String, List<Artefact>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<Artefact>>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = Artefact.listFromJson(entry.value, growable: growable,);
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
    'laneId',
    'pageId',
    'status',
  };
}

/// Lane status
class ArtefactStatusEnum {
  /// Instantiate a new enum with the provided [value].
  const ArtefactStatusEnum._(this.value);

  /// The underlying value of this enum member.
  final String value;

  @override
  String toString() => value;

  String toJson() => value;

  static const open = ArtefactStatusEnum._(r'open');
  static const closed = ArtefactStatusEnum._(r'closed');

  /// List of all possible values in this [enum][ArtefactStatusEnum].
  static const values = <ArtefactStatusEnum>[
    open,
    closed,
  ];

  static ArtefactStatusEnum? fromJson(dynamic value) => ArtefactStatusEnumTypeTransformer().decode(value);

  static List<ArtefactStatusEnum>? listFromJson(dynamic json, {bool growable = false,}) {
    final result = <ArtefactStatusEnum>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = ArtefactStatusEnum.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }
}

/// Transformation class that can [encode] an instance of [ArtefactStatusEnum] to String,
/// and [decode] dynamic data back to [ArtefactStatusEnum].
class ArtefactStatusEnumTypeTransformer {
  factory ArtefactStatusEnumTypeTransformer() => _instance ??= const ArtefactStatusEnumTypeTransformer._();

  const ArtefactStatusEnumTypeTransformer._();

  String encode(ArtefactStatusEnum data) => data.value;

  /// Decodes a [dynamic value][data] to a ArtefactStatusEnum.
  ///
  /// If [allowNull] is true and the [dynamic value][data] cannot be decoded successfully,
  /// then null is returned. However, if [allowNull] is false and the [dynamic value][data]
  /// cannot be decoded successfully, then an [UnimplementedError] is thrown.
  ///
  /// The [allowNull] is very handy when an API changes and a new enum value is added or removed,
  /// and users are still using an old app with the old code.
  ArtefactStatusEnum? decode(dynamic data, {bool allowNull = true}) {
    if (data != null) {
      switch (data.toString()) {
        case r'open': return ArtefactStatusEnum.open;
        case r'closed': return ArtefactStatusEnum.closed;
        default:
          if (!allowNull) {
            throw ArgumentError('Unknown enum value to decode: $data');
          }
      }
    }
    return null;
  }

  /// Singleton [ArtefactStatusEnumTypeTransformer] instance.
  static ArtefactStatusEnumTypeTransformer? _instance;
}


