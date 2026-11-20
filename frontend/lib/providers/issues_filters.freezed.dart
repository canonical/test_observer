// dart format width=80
// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'issues_filters.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$IssuesFiltersState {
  Set<IssueSource> get possibleSources;
  Set<String> get possibleProjects;
  Set<IssueStatus> get possibleStatuses;
  Set<IssueSource> get selectedSources;
  Set<String> get selectedProjects;
  Set<IssueStatus> get selectedStatuses;
  Set<String> get possibleFamilies;
  Set<String> get selectedFamilies;

  /// Create a copy of IssuesFiltersState
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  $IssuesFiltersStateCopyWith<IssuesFiltersState> get copyWith =>
      _$IssuesFiltersStateCopyWithImpl<IssuesFiltersState>(
          this as IssuesFiltersState, _$identity);

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is IssuesFiltersState &&
            const DeepCollectionEquality()
                .equals(other.possibleSources, possibleSources) &&
            const DeepCollectionEquality()
                .equals(other.possibleProjects, possibleProjects) &&
            const DeepCollectionEquality()
                .equals(other.possibleStatuses, possibleStatuses) &&
            const DeepCollectionEquality()
                .equals(other.selectedSources, selectedSources) &&
            const DeepCollectionEquality()
                .equals(other.selectedProjects, selectedProjects) &&
            const DeepCollectionEquality()
                .equals(other.selectedStatuses, selectedStatuses) &&
            const DeepCollectionEquality()
                .equals(other.possibleFamilies, possibleFamilies) &&
            const DeepCollectionEquality()
                .equals(other.selectedFamilies, selectedFamilies));
  }

  @override
  int get hashCode => Object.hash(
      runtimeType,
      const DeepCollectionEquality().hash(possibleSources),
      const DeepCollectionEquality().hash(possibleProjects),
      const DeepCollectionEquality().hash(possibleStatuses),
      const DeepCollectionEquality().hash(selectedSources),
      const DeepCollectionEquality().hash(selectedProjects),
      const DeepCollectionEquality().hash(selectedStatuses),
      const DeepCollectionEquality().hash(possibleFamilies),
      const DeepCollectionEquality().hash(selectedFamilies));

  @override
  String toString() {
    return 'IssuesFiltersState(possibleSources: $possibleSources, possibleProjects: $possibleProjects, possibleStatuses: $possibleStatuses, selectedSources: $selectedSources, selectedProjects: $selectedProjects, selectedStatuses: $selectedStatuses, possibleFamilies: $possibleFamilies, selectedFamilies: $selectedFamilies)';
  }
}

/// @nodoc
abstract mixin class $IssuesFiltersStateCopyWith<$Res> {
  factory $IssuesFiltersStateCopyWith(
          IssuesFiltersState value, $Res Function(IssuesFiltersState) _then) =
      _$IssuesFiltersStateCopyWithImpl;
  @useResult
  $Res call(
      {Set<IssueSource> possibleSources,
      Set<String> possibleProjects,
      Set<IssueStatus> possibleStatuses,
      Set<IssueSource> selectedSources,
      Set<String> selectedProjects,
      Set<IssueStatus> selectedStatuses,
      Set<String> possibleFamilies,
      Set<String> selectedFamilies});
}

/// @nodoc
class _$IssuesFiltersStateCopyWithImpl<$Res>
    implements $IssuesFiltersStateCopyWith<$Res> {
  _$IssuesFiltersStateCopyWithImpl(this._self, this._then);

  final IssuesFiltersState _self;
  final $Res Function(IssuesFiltersState) _then;

  /// Create a copy of IssuesFiltersState
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? possibleSources = null,
    Object? possibleProjects = null,
    Object? possibleStatuses = null,
    Object? selectedSources = null,
    Object? selectedProjects = null,
    Object? selectedStatuses = null,
    Object? possibleFamilies = null,
    Object? selectedFamilies = null,
  }) {
    return _then(_self.copyWith(
      possibleSources: null == possibleSources
          ? _self.possibleSources
          : possibleSources // ignore: cast_nullable_to_non_nullable
              as Set<IssueSource>,
      possibleProjects: null == possibleProjects
          ? _self.possibleProjects
          : possibleProjects // ignore: cast_nullable_to_non_nullable
              as Set<String>,
      possibleStatuses: null == possibleStatuses
          ? _self.possibleStatuses
          : possibleStatuses // ignore: cast_nullable_to_non_nullable
              as Set<IssueStatus>,
      selectedSources: null == selectedSources
          ? _self.selectedSources
          : selectedSources // ignore: cast_nullable_to_non_nullable
              as Set<IssueSource>,
      selectedProjects: null == selectedProjects
          ? _self.selectedProjects
          : selectedProjects // ignore: cast_nullable_to_non_nullable
              as Set<String>,
      selectedStatuses: null == selectedStatuses
          ? _self.selectedStatuses
          : selectedStatuses // ignore: cast_nullable_to_non_nullable
              as Set<IssueStatus>,
      possibleFamilies: null == possibleFamilies
          ? _self.possibleFamilies
          : possibleFamilies // ignore: cast_nullable_to_non_nullable
              as Set<String>,
      selectedFamilies: null == selectedFamilies
          ? _self.selectedFamilies
          : selectedFamilies // ignore: cast_nullable_to_non_nullable
              as Set<String>,
    ));
  }
}

/// @nodoc

class _IssuesFiltersState implements IssuesFiltersState {
  const _IssuesFiltersState(
      {final Set<IssueSource> possibleSources = const {},
      final Set<String> possibleProjects = const {},
      final Set<IssueStatus> possibleStatuses = const {},
      final Set<IssueSource> selectedSources = const {},
      final Set<String> selectedProjects = const {},
      final Set<IssueStatus> selectedStatuses = const {},
      final Set<String> possibleFamilies = const {},
      final Set<String> selectedFamilies = const {}})
      : _possibleSources = possibleSources,
        _possibleProjects = possibleProjects,
        _possibleStatuses = possibleStatuses,
        _selectedSources = selectedSources,
        _selectedProjects = selectedProjects,
        _selectedStatuses = selectedStatuses,
        _possibleFamilies = possibleFamilies,
        _selectedFamilies = selectedFamilies;

  final Set<IssueSource> _possibleSources;
  @override
  @JsonKey()
  Set<IssueSource> get possibleSources {
    if (_possibleSources is EqualUnmodifiableSetView) return _possibleSources;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableSetView(_possibleSources);
  }

  final Set<String> _possibleProjects;
  @override
  @JsonKey()
  Set<String> get possibleProjects {
    if (_possibleProjects is EqualUnmodifiableSetView) return _possibleProjects;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableSetView(_possibleProjects);
  }

  final Set<IssueStatus> _possibleStatuses;
  @override
  @JsonKey()
  Set<IssueStatus> get possibleStatuses {
    if (_possibleStatuses is EqualUnmodifiableSetView) return _possibleStatuses;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableSetView(_possibleStatuses);
  }

  final Set<IssueSource> _selectedSources;
  @override
  @JsonKey()
  Set<IssueSource> get selectedSources {
    if (_selectedSources is EqualUnmodifiableSetView) return _selectedSources;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableSetView(_selectedSources);
  }

  final Set<String> _selectedProjects;
  @override
  @JsonKey()
  Set<String> get selectedProjects {
    if (_selectedProjects is EqualUnmodifiableSetView) return _selectedProjects;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableSetView(_selectedProjects);
  }

  final Set<IssueStatus> _selectedStatuses;
  @override
  @JsonKey()
  Set<IssueStatus> get selectedStatuses {
    if (_selectedStatuses is EqualUnmodifiableSetView) return _selectedStatuses;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableSetView(_selectedStatuses);
  }

  final Set<String> _possibleFamilies;
  @override
  @JsonKey()
  Set<String> get possibleFamilies {
    if (_possibleFamilies is EqualUnmodifiableSetView) return _possibleFamilies;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableSetView(_possibleFamilies);
  }

  final Set<String> _selectedFamilies;
  @override
  @JsonKey()
  Set<String> get selectedFamilies {
    if (_selectedFamilies is EqualUnmodifiableSetView) return _selectedFamilies;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableSetView(_selectedFamilies);
  }

  /// Create a copy of IssuesFiltersState
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  _$IssuesFiltersStateCopyWith<_IssuesFiltersState> get copyWith =>
      __$IssuesFiltersStateCopyWithImpl<_IssuesFiltersState>(this, _$identity);

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _IssuesFiltersState &&
            const DeepCollectionEquality()
                .equals(other._possibleSources, _possibleSources) &&
            const DeepCollectionEquality()
                .equals(other._possibleProjects, _possibleProjects) &&
            const DeepCollectionEquality()
                .equals(other._possibleStatuses, _possibleStatuses) &&
            const DeepCollectionEquality()
                .equals(other._selectedSources, _selectedSources) &&
            const DeepCollectionEquality()
                .equals(other._selectedProjects, _selectedProjects) &&
            const DeepCollectionEquality()
                .equals(other._selectedStatuses, _selectedStatuses) &&
            const DeepCollectionEquality()
                .equals(other._possibleFamilies, _possibleFamilies) &&
            const DeepCollectionEquality()
                .equals(other._selectedFamilies, _selectedFamilies));
  }

  @override
  int get hashCode => Object.hash(
      runtimeType,
      const DeepCollectionEquality().hash(_possibleSources),
      const DeepCollectionEquality().hash(_possibleProjects),
      const DeepCollectionEquality().hash(_possibleStatuses),
      const DeepCollectionEquality().hash(_selectedSources),
      const DeepCollectionEquality().hash(_selectedProjects),
      const DeepCollectionEquality().hash(_selectedStatuses),
      const DeepCollectionEquality().hash(_possibleFamilies),
      const DeepCollectionEquality().hash(_selectedFamilies));

  @override
  String toString() {
    return 'IssuesFiltersState(possibleSources: $possibleSources, possibleProjects: $possibleProjects, possibleStatuses: $possibleStatuses, selectedSources: $selectedSources, selectedProjects: $selectedProjects, selectedStatuses: $selectedStatuses, possibleFamilies: $possibleFamilies, selectedFamilies: $selectedFamilies)';
  }
}

/// @nodoc
abstract mixin class _$IssuesFiltersStateCopyWith<$Res>
    implements $IssuesFiltersStateCopyWith<$Res> {
  factory _$IssuesFiltersStateCopyWith(
          _IssuesFiltersState value, $Res Function(_IssuesFiltersState) _then) =
      __$IssuesFiltersStateCopyWithImpl;
  @override
  @useResult
  $Res call(
      {Set<IssueSource> possibleSources,
      Set<String> possibleProjects,
      Set<IssueStatus> possibleStatuses,
      Set<IssueSource> selectedSources,
      Set<String> selectedProjects,
      Set<IssueStatus> selectedStatuses,
      Set<String> possibleFamilies,
      Set<String> selectedFamilies});
}

/// @nodoc
class __$IssuesFiltersStateCopyWithImpl<$Res>
    implements _$IssuesFiltersStateCopyWith<$Res> {
  __$IssuesFiltersStateCopyWithImpl(this._self, this._then);

  final _IssuesFiltersState _self;
  final $Res Function(_IssuesFiltersState) _then;

  /// Create a copy of IssuesFiltersState
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $Res call({
    Object? possibleSources = null,
    Object? possibleProjects = null,
    Object? possibleStatuses = null,
    Object? selectedSources = null,
    Object? selectedProjects = null,
    Object? selectedStatuses = null,
    Object? possibleFamilies = null,
    Object? selectedFamilies = null,
  }) {
    return _then(_IssuesFiltersState(
      possibleSources: null == possibleSources
          ? _self._possibleSources
          : possibleSources // ignore: cast_nullable_to_non_nullable
              as Set<IssueSource>,
      possibleProjects: null == possibleProjects
          ? _self._possibleProjects
          : possibleProjects // ignore: cast_nullable_to_non_nullable
              as Set<String>,
      possibleStatuses: null == possibleStatuses
          ? _self._possibleStatuses
          : possibleStatuses // ignore: cast_nullable_to_non_nullable
              as Set<IssueStatus>,
      selectedSources: null == selectedSources
          ? _self._selectedSources
          : selectedSources // ignore: cast_nullable_to_non_nullable
              as Set<IssueSource>,
      selectedProjects: null == selectedProjects
          ? _self._selectedProjects
          : selectedProjects // ignore: cast_nullable_to_non_nullable
              as Set<String>,
      selectedStatuses: null == selectedStatuses
          ? _self._selectedStatuses
          : selectedStatuses // ignore: cast_nullable_to_non_nullable
              as Set<IssueStatus>,
      possibleFamilies: null == possibleFamilies
          ? _self._possibleFamilies
          : possibleFamilies // ignore: cast_nullable_to_non_nullable
              as Set<String>,
      selectedFamilies: null == selectedFamilies
          ? _self._selectedFamilies
          : selectedFamilies // ignore: cast_nullable_to_non_nullable
              as Set<String>,
    ));
  }
}

// dart format on
