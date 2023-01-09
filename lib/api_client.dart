import "package:openapi_generator_annotations/openapi_generator_annotations.dart";

@Openapi(
    additionalProperties:
        AdditionalProperties(pubName: 'testcases', pubAuthor: 'Nadzeya'),
    inputSpecFile: 'api/cardsapp_openapi.yaml',
    generatorName: Generator.dart,
    outputDirectory: 'api/testcases')
class TestcasesGeneratorConfig extends OpenapiGeneratorConfig {}
