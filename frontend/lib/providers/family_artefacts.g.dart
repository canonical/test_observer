// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'family_artefacts.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$familyArtefactsHash() => r'0a72c1af7822e0d80ba6f8f943750fe98621efd3';

/// Copied from Dart SDK
class _SystemHash {
  _SystemHash._();

  static int combine(int hash, int value) {
    // ignore: parameter_assignments
    hash = 0x1fffffff & (hash + value);
    // ignore: parameter_assignments
    hash = 0x1fffffff & (hash + ((0x0007ffff & hash) << 10));
    return hash ^ (hash >> 6);
  }

  static int finish(int hash) {
    // ignore: parameter_assignments
    hash = 0x1fffffff & (hash + ((0x03ffffff & hash) << 3));
    // ignore: parameter_assignments
    hash = hash ^ (hash >> 11);
    return 0x1fffffff & (hash + ((0x00003fff & hash) << 15));
  }
}

/// See also [familyArtefacts].
@ProviderFor(familyArtefacts)
const familyArtefactsProvider = FamilyArtefactsFamily();

/// See also [familyArtefacts].
class FamilyArtefactsFamily extends Family<AsyncValue<Map<int, Artefact>>> {
  /// See also [familyArtefacts].
  const FamilyArtefactsFamily();

  /// See also [familyArtefacts].
  FamilyArtefactsProvider call(
    String family,
  ) {
    return FamilyArtefactsProvider(
      family,
    );
  }

  @override
  FamilyArtefactsProvider getProviderOverride(
    covariant FamilyArtefactsProvider provider,
  ) {
    return call(
      provider.family,
    );
  }

  static const Iterable<ProviderOrFamily>? _dependencies = null;

  @override
  Iterable<ProviderOrFamily>? get dependencies => _dependencies;

  static const Iterable<ProviderOrFamily>? _allTransitiveDependencies = null;

  @override
  Iterable<ProviderOrFamily>? get allTransitiveDependencies =>
      _allTransitiveDependencies;

  @override
  String? get name => r'familyArtefactsProvider';
}

/// See also [familyArtefacts].
class FamilyArtefactsProvider
    extends AutoDisposeFutureProvider<Map<int, Artefact>> {
  /// See also [familyArtefacts].
  FamilyArtefactsProvider(
    String family,
  ) : this._internal(
          (ref) => familyArtefacts(
            ref as FamilyArtefactsRef,
            family,
          ),
          from: familyArtefactsProvider,
          name: r'familyArtefactsProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$familyArtefactsHash,
          dependencies: FamilyArtefactsFamily._dependencies,
          allTransitiveDependencies:
              FamilyArtefactsFamily._allTransitiveDependencies,
          family: family,
        );

  FamilyArtefactsProvider._internal(
    super._createNotifier, {
    required super.name,
    required super.dependencies,
    required super.allTransitiveDependencies,
    required super.debugGetCreateSourceHash,
    required super.from,
    required this.family,
  }) : super.internal();

  final String family;

  @override
  Override overrideWith(
    FutureOr<Map<int, Artefact>> Function(FamilyArtefactsRef provider) create,
  ) {
    return ProviderOverride(
      origin: this,
      override: FamilyArtefactsProvider._internal(
        (ref) => create(ref as FamilyArtefactsRef),
        from: from,
        name: null,
        dependencies: null,
        allTransitiveDependencies: null,
        debugGetCreateSourceHash: null,
        family: family,
      ),
    );
  }

  @override
  AutoDisposeFutureProviderElement<Map<int, Artefact>> createElement() {
    return _FamilyArtefactsProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is FamilyArtefactsProvider && other.family == family;
  }

  @override
  int get hashCode {
    var hash = _SystemHash.combine(0, runtimeType.hashCode);
    hash = _SystemHash.combine(hash, family.hashCode);

    return _SystemHash.finish(hash);
  }
}

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
mixin FamilyArtefactsRef on AutoDisposeFutureProviderRef<Map<int, Artefact>> {
  /// The parameter `family` of this provider.
  String get family;
}

class _FamilyArtefactsProviderElement
    extends AutoDisposeFutureProviderElement<Map<int, Artefact>>
    with FamilyArtefactsRef {
  _FamilyArtefactsProviderElement(super.provider);

  @override
  String get family => (origin as FamilyArtefactsProvider).family;
}
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
