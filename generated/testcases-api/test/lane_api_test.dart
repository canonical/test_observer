//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.12

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

import 'package:testcases/api.dart';
import 'package:test/test.dart';


/// tests for LaneApi
void main() {
  // final instance = LaneApi();

  group('tests for LaneApi', () {
    // Add a new lane
    //
    // Add a new lane to an existent page. This method should create an empty open lane and return the new lane Id
    //
    //Future<String> addLane(AddLaneRequest addLaneRequest) async
    test('test addLane', () async {
      // TODO
    });

    // Delete a lane
    //
    // Permanently delete a lane from the page and all artefacts in this lane
    //
    //Future deleteLane(String laneId) async
    test('test deleteLane', () async {
      // TODO
    });

    // Get all artefacts in the lane
    //
    // With this method we should be able to fetch all the artefacts (in JSON) from the lane
    //
    //Future<List<Artefact>> getArtefactsInLane(String laneId) async
    test('test getArtefactsInLane', () async {
      // TODO
    });

    // Get JSON representation of the lane by its Id
    //
    //Future<Lane> getLaneById(String laneId) async
    test('test getLaneById', () async {
      // TODO
    });

    // Update an existent lane
    //
    // With this method we should be able move lane to another page (by updating pageId), chage its name and status (maybe also Id itself). If we close a lane, the artefacts in it should also be closed
    //
    //Future updateLane(String laneId, Lane lane) async
    test('test updateLane', () async {
      // TODO
    });

  });
}
