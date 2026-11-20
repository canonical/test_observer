// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'issues_filters.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$issuesFiltersHash() => r'2339a6ffdc371c76b8fbe7140d1606190fafa4bc';

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

abstract class _$IssuesFilters
    extends BuildlessAutoDisposeNotifier<IssuesFiltersState> {
  late final Uri pageUri;

  IssuesFiltersState build(
    Uri pageUri,
  );
}

/// See also [IssuesFilters].
@ProviderFor(IssuesFilters)
const issuesFiltersProvider = IssuesFiltersFamily();

/// See also [IssuesFilters].
class IssuesFiltersFamily extends Family<IssuesFiltersState> {
  /// See also [IssuesFilters].
  const IssuesFiltersFamily();

  /// See also [IssuesFilters].
  IssuesFiltersProvider call(
    Uri pageUri,
  ) {
    return IssuesFiltersProvider(
      pageUri,
    );
  }

  @override
  IssuesFiltersProvider getProviderOverride(
    covariant IssuesFiltersProvider provider,
  ) {
    return call(
      provider.pageUri,
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
  String? get name => r'issuesFiltersProvider';
}

/// See also [IssuesFilters].
class IssuesFiltersProvider
    extends AutoDisposeNotifierProviderImpl<IssuesFilters, IssuesFiltersState> {
  /// See also [IssuesFilters].
  IssuesFiltersProvider(
    Uri pageUri,
  ) : this._internal(
          () => IssuesFilters()..pageUri = pageUri,
          from: issuesFiltersProvider,
          name: r'issuesFiltersProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$issuesFiltersHash,
          dependencies: IssuesFiltersFamily._dependencies,
          allTransitiveDependencies:
              IssuesFiltersFamily._allTransitiveDependencies,
          pageUri: pageUri,
        );

  IssuesFiltersProvider._internal(
    super._createNotifier, {
    required super.name,
    required super.dependencies,
    required super.allTransitiveDependencies,
    required super.debugGetCreateSourceHash,
    required super.from,
    required this.pageUri,
  }) : super.internal();

  final Uri pageUri;

  @override
  IssuesFiltersState runNotifierBuild(
    covariant IssuesFilters notifier,
  ) {
    return notifier.build(
      pageUri,
    );
  }

  @override
  Override overrideWith(IssuesFilters Function() create) {
    return ProviderOverride(
      origin: this,
      override: IssuesFiltersProvider._internal(
        () => create()..pageUri = pageUri,
        from: from,
        name: null,
        dependencies: null,
        allTransitiveDependencies: null,
        debugGetCreateSourceHash: null,
        pageUri: pageUri,
      ),
    );
  }

  @override
  AutoDisposeNotifierProviderElement<IssuesFilters, IssuesFiltersState>
      createElement() {
    return _IssuesFiltersProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is IssuesFiltersProvider && other.pageUri == pageUri;
  }

  @override
  int get hashCode {
    var hash = _SystemHash.combine(0, runtimeType.hashCode);
    hash = _SystemHash.combine(hash, pageUri.hashCode);

    return _SystemHash.finish(hash);
  }
}

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
mixin IssuesFiltersRef on AutoDisposeNotifierProviderRef<IssuesFiltersState> {
  /// The parameter `pageUri` of this provider.
  Uri get pageUri;
}

class _IssuesFiltersProviderElement extends AutoDisposeNotifierProviderElement<
    IssuesFilters, IssuesFiltersState> with IssuesFiltersRef {
  _IssuesFiltersProviderElement(super.provider);

  @override
  Uri get pageUri => (origin as IssuesFiltersProvider).pageUri;
}
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
