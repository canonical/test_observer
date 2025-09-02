<?php
/**
 * SAML 2.0 IdP configuration for SimpleSAMLphp.
 *
 * See: https://simplesamlphp.org/docs/stable/simplesamlphp-reference-idp-hosted
 */

$metadata['__DYNAMIC:1__'] = array(
        'host' => '__DEFAULT__',

        'privatekey' => 'server.pem',
        'certificate' => 'server.crt',

        'auth' => 'example-userpass',

        // Use emailAddress NameIdFormat
        'authproc' => [
            100 => [
                'class' => 'saml:AttributeNameID',
                'attribute' => 'email',
                'Format' => 'urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress',
            ],
        ],
);