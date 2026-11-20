// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'rerun_details.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$rerunDetailsHash() => r'80c3b53175800c963ab2537006d31ef659f35033';

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

/// See also [rerunDetails].
@ProviderFor(rerunDetails)
const rerunDetailsProvider = RerunDetailsFamily();

/// See also [rerunDetails].
class RerunDetailsFamily extends Family<AsyncValue<RerunDetailsResponse>> {
  /// See also [rerunDetails].
  const RerunDetailsFamily();

  /// See also [rerunDetails].
  RerunDetailsProvider call({
    required String family,
    int? priority,
    int page = 1,
  }) {
    return RerunDetailsProvider(
      family: family,
      priority: priority,
      page: page,
    );
  }

  @override
  RerunDetailsProvider getProviderOverride(
    covariant RerunDetailsProvider provider,
  ) {
    return call(
      family: provider.family,
      priority: provider.priority,
      page: provider.page,
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
  String? get name => r'rerunDetailsProvider';
}

/// See also [rerunDetails].
class RerunDetailsProvider
    extends AutoDisposeFutureProvider<RerunDetailsResponse> {
  /// See also [rerunDetails].
  RerunDetailsProvider({
    required String family,
    int? priority,
    int page = 1,
  }) : this._internal(
          (ref) => rerunDetails(
            ref as RerunDetailsRef,
            family: family,
            priority: priority,
            page: page,
          ),
          from: rerunDetailsProvider,
          name: r'rerunDetailsProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$rerunDetailsHash,
          dependencies: RerunDetailsFamily._dependencies,
          allTransitiveDependencies:
              RerunDetailsFamily._allTransitiveDependencies,
          family: family,
          priority: priority,
          page: page,
        );

  RerunDetailsProvider._internal(
    super._createNotifier, {
    required super.name,
    required super.dependencies,
    required super.allTransitiveDependencies,
    required super.debugGetCreateSourceHash,
    required super.from,
    required this.family,
    required this.priority,
    required this.page,
  }) : super.internal();

  final String family;
  final int? priority;
  final int page;

  @override
  Override overrideWith(
    FutureOr<RerunDetailsResponse> Function(RerunDetailsRef provider) create,
  ) {
    return ProviderOverride(
      origin: this,
      override: RerunDetailsProvider._internal(
        (ref) => create(ref as RerunDetailsRef),
        from: from,
        name: null,
        dependencies: null,
        allTransitiveDependencies: null,
        debugGetCreateSourceHash: null,
        family: family,
        priority: priority,
        page: page,
      ),
    );
  }

  @override
  AutoDisposeFutureProviderElement<RerunDetailsResponse> createElement() {
    return _RerunDetailsProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is RerunDetailsProvider &&
        other.family == family &&
        other.priority == priority &&
        other.page == page;
  }

  @override
  int get hashCode {
    var hash = _SystemHash.combine(0, runtimeType.hashCode);
    hash = _SystemHash.combine(hash, family.hashCode);
    hash = _SystemHash.combine(hash, priority.hashCode);
    hash = _SystemHash.combine(hash, page.hashCode);

    return _SystemHash.finish(hash);
  }
}

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
mixin RerunDetailsRef on AutoDisposeFutureProviderRef<RerunDetailsResponse> {
  /// The parameter `family` of this provider.
  String get family;

  /// The parameter `priority` of this provider.
  int? get priority;

  /// The parameter `page` of this provider.
  int get page;
}

class _RerunDetailsProviderElement
    extends AutoDisposeFutureProviderElement<RerunDetailsResponse>
    with RerunDetailsRef {
  _RerunDetailsProviderElement(super.provider);

  @override
  String get family => (origin as RerunDetailsProvider).family;
  @override
  int? get priority => (origin as RerunDetailsProvider).priority;
  @override
  int get page => (origin as RerunDetailsProvider).page;
}
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
