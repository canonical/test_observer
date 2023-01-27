import "package:openapi_generator_annotations/openapi_generator_annotations.dart";

@Openapi(
    additionalProperties:
        DioProperties(pubName: 'testcases', pubAuthor: 'Nadzeya'),
    inputSpecFile:
        'external/certification-dashboard-manager/cardsapp_openapi.yaml',
    generatorName: Generator.dart,
    outputDirectory: 'generated/testcases-api')
class TestcasesGeneratorConfig extends OpenapiGeneratorConfig {}
