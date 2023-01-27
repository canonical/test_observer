//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.12

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class Page {
  /// Returns a new [Page] instance.
  Page({
    required this.id,
    required this.name,
    required this.status,
  });

  String id;

  String name;

  /// Page status
  PageStatusEnum status;

  @override
  bool operator ==(Object other) => identical(this, other) || other is Page &&
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
  String toString() => 'Page[id=$id, name=$name, status=$status]';

  Map<String, dynamic> toJson() {
    final _json = <String, dynamic>{};
      _json[r'id'] = id;
      _json[r'name'] = name;
      _json[r'status'] = status;
    return _json;
  }

  /// Returns a new [Page] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static Page? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "Page[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "Page[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return Page(
        id: mapValueOfType<String>(json, r'id')!,
        name: mapValueOfType<String>(json, r'name')!,
        status: PageStatusEnum.fromJson(json[r'status'])!,
      );
    }
    return null;
  }

  static List<Page>? listFromJson(dynamic json, {bool growable = false,}) {
    final result = <Page>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = Page.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, Page> mapFromJson(dynamic json) {
    final map = <String, Page>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = Page.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of Page-objects as value to a dart map
  static Map<String, List<Page>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<Page>>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = Page.listFromJson(entry.value, growable: growable,);
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

/// Page status
class PageStatusEnum {
  /// Instantiate a new enum with the provided [value].
  const PageStatusEnum._(this.value);

  /// The underlying value of this enum member.
  final String value;

  @override
  String toString() => value;

  String toJson() => value;

  static const open = PageStatusEnum._(r'open');
  static const closed = PageStatusEnum._(r'closed');

  /// List of all possible values in this [enum][PageStatusEnum].
  static const values = <PageStatusEnum>[
    open,
    closed,
  ];

  static PageStatusEnum? fromJson(dynamic value) => PageStatusEnumTypeTransformer().decode(value);

  static List<PageStatusEnum>? listFromJson(dynamic json, {bool growable = false,}) {
    final result = <PageStatusEnum>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = PageStatusEnum.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }
}

/// Transformation class that can [encode] an instance of [PageStatusEnum] to String,
/// and [decode] dynamic data back to [PageStatusEnum].
class PageStatusEnumTypeTransformer {
  factory PageStatusEnumTypeTransformer() => _instance ??= const PageStatusEnumTypeTransformer._();

  const PageStatusEnumTypeTransformer._();

  String encode(PageStatusEnum data) => data.value;

  /// Decodes a [dynamic value][data] to a PageStatusEnum.
  ///
  /// If [allowNull] is true and the [dynamic value][data] cannot be decoded successfully,
  /// then null is returned. However, if [allowNull] is false and the [dynamic value][data]
  /// cannot be decoded successfully, then an [UnimplementedError] is thrown.
  ///
  /// The [allowNull] is very handy when an API changes and a new enum value is added or removed,
  /// and users are still using an old app with the old code.
  PageStatusEnum? decode(dynamic data, {bool allowNull = true}) {
    if (data != null) {
      switch (data.toString()) {
        case r'open': return PageStatusEnum.open;
        case r'closed': return PageStatusEnum.closed;
        default:
          if (!allowNull) {
            throw ArgumentError('Unknown enum value to decode: $data');
          }
      }
    }
    return null;
  }

  /// Singleton [PageStatusEnumTypeTransformer] instance.
  static PageStatusEnumTypeTransformer? _instance;
}


