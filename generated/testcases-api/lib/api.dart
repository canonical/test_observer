//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.12

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

library openapi.api;

import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart';
import 'package:intl/intl.dart';
import 'package:meta/meta.dart';

part 'api_client.dart';
part 'api_helper.dart';
part 'api_exception.dart';
part 'auth/authentication.dart';
part 'auth/api_key_auth.dart';
part 'auth/oauth.dart';
part 'auth/http_basic_auth.dart';
part 'auth/http_bearer_auth.dart';

part 'api/artefact_api.dart';
part 'api/artefact_group_api.dart';
part 'api/environments_api.dart';
part 'api/lane_api.dart';
part 'api/page_api.dart';

part 'model/add_artefact_group_request.dart';
part 'model/add_artefact_request.dart';
part 'model/add_comment_to_artefact_request.dart';
part 'model/add_label_to_artefact_request.dart';
part 'model/add_lane_request.dart';
part 'model/add_page_request.dart';
part 'model/addenvironments_request.dart';
part 'model/artefact.dart';
part 'model/check_item.dart';
part 'model/comment.dart';
part 'model/environments.dart';
part 'model/label.dart';
part 'model/lane.dart';
part 'model/page.dart';


const _delimiters = {'csv': ',', 'ssv': ' ', 'tsv': '\t', 'pipes': '|'};
const _dateEpochMarker = 'epoch';
final _dateFormatter = DateFormat('yyyy-MM-dd');
final _regList = RegExp(r'^List<(.*)>$');
final _regSet = RegExp(r'^Set<(.*)>$');
final _regMap = RegExp(r'^Map<String,(.*)>$');

ApiClient defaultApiClient = ApiClient();
