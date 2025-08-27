import os


VERSION = os.getenv("VERSION", "0.0.0")
SENTRY_DSN = os.getenv("SENTRY_DSN")
SAML_SP_BASE_URL = os.getenv("SAML_SP_BASE_URL", "http://localhost:30000")
SAML_IDP_METADATA_URL = os.getenv(
    "SAML_IDP_METADATA_URL",
    "http://localhost:8080/simplesaml/saml2/idp/metadata.php",
)
SAML_SP_X509_CERT = os.getenv("SAML_SP_X509_CERT", "")
SAML_SP_KEY = os.getenv("SAML_SP_KEY", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:30001")
