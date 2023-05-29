resource "juju_integration" "ingress-to-acme-operator" {
    application {
        name = juju_application.ingress.name
        endpoint = "certificates"
    }

    application {
        name = juju_application.cloudflare_acme_operator.name
        endpoint = "certificates"
    }
}