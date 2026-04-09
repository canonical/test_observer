OpenAPI 
=======

.. vale off

.. only:: html

    .. raw:: html

        <link rel="stylesheet" type="text/css" href="../../_static/swagger-ui.css" />
        <link rel="stylesheet" type="text/css" href="../../_static/swagger-custom.css" />
        <div id="openapi-swagger"></div>
        <script src="../../_static/swagger-ui-bundle.js" charset="UTF-8"></script>
        <script src="../../_static/swagger-ui-standalone-preset.js" charset="UTF-8"></script>
        <script>
            window.addEventListener("load", function () {
                // The OpenAPI spec file is copied to the root of the `docs/` directory during build
                // by Sphinx using the `html_extra_path` option in `conf.py`.
                const specUrl = new URL("../../openapi.json", window.location.href).toString();
                SwaggerUIBundle({
                    url: specUrl,
                    dom_id: "#openapi-swagger",
                    presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
                    plugins: [],
                    deepLinking: true,
                    defaultModelsExpandDepth: -1,
                    supportedSubmitMethods: []
                });
            });
        </script>

.. vale on

.. only:: not html

    The interactive Swagger UI is available in the HTML documentation only.
