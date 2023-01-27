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


/// tests for ArtefactApi
void main() {
  // final instance = ArtefactApi();

  group('tests for ArtefactApi', () {
    // Add a new artefact
    //
    // Add a new artefact to en existing lane. With this method we should be able to create an empty open artefact without any environmentss, comments and labels. The response should consist of new artefact Id
    //
    //Future<String> addArtefact(AddArtefactRequest addArtefactRequest) async
    test('test addArtefact', () async {
      // TODO
    });

    // Add comment an existent artefact
    //
    // Add comment an existent artefact by artefact Id
    //
    //Future<List<Comment>> addCommentToArtefact(String artefactId, AddCommentToArtefactRequest addCommentToArtefactRequest) async
    test('test addCommentToArtefact', () async {
      // TODO
    });

    // Attach a label an existent artefact
    //
    // Create a new label for an existent artefact
    //
    //Future<List<Label>> addLabelToArtefact(String artefactId, AddLabelToArtefactRequest addLabelToArtefactRequest) async
    test('test addLabelToArtefact', () async {
      // TODO
    });

    // Delete a artefact
    //
    // Delete a artefact and all its labels, comments and environmentss
    //
    //Future deleteArtefact(String artefactId) async
    test('test deleteArtefact', () async {
      // TODO
    });

    // Get artefact by its Id
    //
    // Get a JSON representation of the artefact
    //
    //Future<Artefact> getArtefactById(String artefactId) async
    test('test getArtefactById', () async {
      // TODO
    });

    // Get artefact comments
    //
    //Future<List<Comment>> getCommentInArtefactById(String artefactId, int commentId) async
    test('test getCommentInArtefactById', () async {
      // TODO
    });

    // Get artefact comments
    //
    //Future<List<Comment>> getCommentsInArtefact(String artefactId) async
    test('test getCommentsInArtefact', () async {
      // TODO
    });

    // Get artefact labels
    //
    // Fetch the labels in the artefact
    //
    //Future<List<Label>> getLabelsInArtefact(String artefactId) async
    test('test getLabelsInArtefact', () async {
      // TODO
    });

    // Update an existent artefact
    //
    // Update an existent artefact by Id. Here we should be able to move artefact to another lane by changing laneId, and update labels and comments as well.
    //
    //Future updateArtefact(String artefactId, Artefact artefact) async
    test('test updateArtefact', () async {
      // TODO
    });

  });
}
