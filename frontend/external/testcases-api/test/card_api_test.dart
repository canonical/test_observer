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


/// tests for CardApi
void main() {
  // final instance = CardApi();

  group('tests for CardApi', () {
    // Add a new card
    //
    // Add a new card to en existent list. With this method we should be able to create an empty open card without any checklists, comments and labels. The response should consist of new card Id
    //
    //Future<String> addCard(AddCardRequest addCardRequest) async
    test('test addCard', () async {
      // TODO
    });

    // Add comment an existent card
    //
    // Add comment an existent card by card Id
    //
    //Future<List<Comment>> addCommentToCard(String cardId, AddCommentToCardRequest addCommentToCardRequest) async
    test('test addCommentToCard', () async {
      // TODO
    });

    // Attach a label an existent card
    //
    // Create a new label for an existent card
    //
    //Future<List<Label>> addLabelToCard(String cardId, AddLabelToCardRequest addLabelToCardRequest) async
    test('test addLabelToCard', () async {
      // TODO
    });

    // Delete a card
    //
    // Delete a card and all its labels, comments and checklists
    //
    //Future deleteCard(String cardId) async
    test('test deleteCard', () async {
      // TODO
    });

    // Get card by its Id
    //
    // Get a JSON representation of the card
    //
    //Future<Card> getCardById(String cardId) async
    test('test getCardById', () async {
      // TODO
    });

    // Get card checklists
    //
    // Fetch the JSON representation of the checklists in a card
    //
    //Future<List<Checklist>> getChecklistsInCard(String cardId) async
    test('test getChecklistsInCard', () async {
      // TODO
    });

    // Get card comments
    //
    //Future<List<Comment>> getCommentInCardById(String cardId, int commentId) async
    test('test getCommentInCardById', () async {
      // TODO
    });

    // Get card comments
    //
    //Future<List<Comment>> getCommentsInCard(String cardId) async
    test('test getCommentsInCard', () async {
      // TODO
    });

    // Get card labels
    //
    // Fetch the labels in the card
    //
    //Future<List<Label>> getLabelsInCard(String cardId) async
    test('test getLabelsInCard', () async {
      // TODO
    });

    // Update an existent card
    //
    // Update an existent card by Id. Here we should be able to move card to another list by changing listId, and update labels and comments as well.
    //
    //Future updateCard(String cardId, Card card) async
    test('test updateCard', () async {
      // TODO
    });

  });
}
