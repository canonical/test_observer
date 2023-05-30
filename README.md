# Test Observer

Observe the status and state of certification tests for various artefacts

## Prerequisites for developing and deploying locally

- `juju` 3.1 or later (`sudo snap install juju --channel=3.1/stable`)
- `microk8s` 1.27 or later (`sudo snap install microk8s --channel=1.27-strict/stable`) + [permission setup steps after install](https://juju.is/docs/sdk/set-up-your-development-environment#heading--install-microk8s)
- `terraform` 1.4.6 or later (`sudo snap install terraform`)
- `lxd` 5.13 or later (`sudo snap install lxc --channel=5.0/stable`) + `lxd init` after install.
- `charmcraft` 2.3.0 or later (`sudo snap install charmcraft --channel=2.x/stable`)
- optional: `jhack` for all kinds of handy Juju and charm SDK development and debugging operations (`sudo snap install jhack`)

## Deploying a copy of the system with terraform / juju in microk8s

Fist configure microk8s with the needed extensions:

```
sudo microk8s enable community # required for installing traefik
sudo microk8s enable dns hostpath-storage metallb traefik # metallb setup involves choosing a free IP range for the load balancer.
```

Then help microk8s work with an authorized (private) OCI image registry at ghcr.io:

1. Get a GitHub personal access token at https://github.com/settings/tokens/new with the `package:read` permission.
2. Configure containerd in microk8s with the auth credentials needed to pull images from non-default, authorisation requiring OCI registries by appending the following to `/var/snap/microk8s/current/args/containerd-template.toml`:

```yaml
[plugins."io.containerd.grpc.v1.cri".registry.configs."ghcr.io".auth]
  username = "mz2"
  password = "your-GitHub-API-token"
```

After this config file tweak, restart containerd and microk8s:

```bash
sudo systemctl restart snap.microk8s.daemon-containerd.service && sudo microk8s.stop && sudo microk8s.start
juju bootstrap microk8s
juju model-config logging-config="<root>=DEBUG"
```

### Deploy the system locally with Terraform

In the `terraform` directory of your working copy, complete the one-time initialisation:

```bash
cd terraform
terraform init
```

After initialization (or after making changes to the terraform configuration) you can deploy the whole system with:

```bash
TF_VAR_environment=development TF_VAR_external_ingress_hostname="mah-domain.com" terraform apply -auto-approve
```

At the time of writing, this will accomplish deploying the following:

- the backend API server
- the frontend served using nginx
- a postgresql database
- traefik as ingress
- backend connected to frontend (the backend's public facing base URI passed to the frontend app)
- backend connected to database
- backend connected to load balancer
- frontend connected to load balancer

Terraform works by applying changes between the current state of the system and what is in the plan (the test-observer.tf configuration file). When `terraform apply` is run the 1st time, there is no state -> it will create the Juju model and all resources inside it. When it is run with a pre-existing model already in place, it will instead set / unset config values that have changed, add / remove relations, add / remove applications, etc. Basically, it makes working with Juju declarative - yay!

The terraform juju provider is documented over here: https://registry.terraform.io/providers/juju/juju/latest/docs

Terraform tracks its state with a .tfstate file which is created as a result of running `terraform apply` -- for production purposes this will be stored in an S3-like bucket remotely, and for local development purposes it sits in the `terraform` directory aftery you have done a `terraform apply`).

You can optionally get SSL certificates automatically managed for the ingress (in case you happen to have a DNS zone with Cloudflare DNS available):

```bash
TF_VAR_environment=development TF_VAR_external_ingress_hostname="mah-domain.com" TF_VAR_cloudflare_acme=true TF_VAR_cloudflare_dns_api_token=... TF_VAR_cloudflare_zone_read_api_token=... TF_VAR_cloudflare_email=... terraform apply -auto-approve
```

After all is up, `juju status --relations` should give you output to the direction of the following (the acme-operator only there if `TF_VAR_cloudflare_acme` was passed in):

```bash
$ juju status --relations
Model                      Controller          Cloud/Region        Version  SLA          Timestamp
test-observer-development  microk8s-localhost  microk8s/localhost  3.1.2    unsupported  23:23:01+03:00

App                     Version  Status  Scale  Charm                     Channel    Rev  Address         Exposed  Message
acme-operator                    active      1  cloudflare-acme-operator  beta         3  10.152.183.59   no
ingress                 2.9.6    active      1  traefik-k8s               stable     110  192.168.0.202   no
pg                      14.7     active      1  postgresql-k8s            14/stable   73  10.152.183.106  no       Primary
test-observer-api                active      1  test-observer-api         edge         6  10.152.183.207  no
test-observer-frontend           active      1  test-observer-frontend    edge         2  10.152.183.111  no

Unit                       Workload  Agent  Address      Ports  Message
acme-operator/0*           active    idle   10.1.92.188
ingress/0*                 active    idle   10.1.92.182
pg/0*                      active    idle   10.1.92.137         Primary
test-observer-api/0*       active    idle   10.1.92.143
test-observer-frontend/0*  active    idle   10.1.92.189

Relation provider                            Requirer                                          Interface          Type     Message
acme-operator:certificates                   ingress:certificates                              tls-certificates   regular
ingress:ingress                              test-observer-api:ingress                         ingress            regular
ingress:ingress                              test-observer-frontend:ingress                    ingress            regular
pg:database                                  test-observer-api:database                        postgresql_client  regular
pg:database-peers                            pg:database-peers                                 postgresql_peers   peer
pg:restart                                   pg:restart                                        rolling_op         peer
test-observer-api:test-observer-rest-api-v1  test-observer-frontend:test-observer-rest-api-v1  http               regular
```

To test the application with the frontend and API server ports exposed, you need to create some aliases in `/etc/hosts` to the IP address that the ingress got from `metallb` (`juju status` above will find you the ingress IP). Let's assume you have a domain `mah-domain.com` that you want to expose service under, the backend and frontend will be present as subdomains `test-observer-frontend.mah-domain.com` and `test-observer-api.mah-domain.com`, respectively:

```bash
❯ cat /etc/hosts
192.168.0.202   test-observer-frontend.mah-domain.com test-observer-api.mah-domain.com
...
```

## Developing the charm

To develop and test updates to the backend and frontend charms, you would typically want to first complete the above steps to deploy a working system. Once you have done that, proceed with the following steps.

### Build and refresh the backend charm

You can make edits to the backend charm and refresh it in the running system on the fly with:

```bash
cd backend/charm
charmcraft pack
juju refresh test-observer-api --path ./test-observer-api_ubuntu-22.04-amd64.charm

# to update the OCI image that runs the backend
juju attach-resource test-observer-api --resource api-image=ghcr.io/canonical/test_observer/backend:[tag or sha]
```

### Build and refresh the frontend charm

Same thing with the frontend:

```bash
cd frontend/charm
charmcraft pack

juju refresh test-observer-frontend ./test-observer-frontend_ubuntu-22.04-amd64.charm

# to update the OCI image that runs the backend
juju attach-resource test-observer-frontend frontend-image=ghcr.io/canonical/test_observer/frontend:[tag or sha]
```

Note that the frontend app is made aware of the backend URL to connect to using the global `window.testObserverAPIBaseURI`, which is set at runtime with some nginx config level trickery based on...

- the `test-observer-api` charm's `hostname` config value.
- the frontend charm's `test-observer-api-scheme` config value.

These in turn can be set using the terraform plan (`terraform/test-observer.tf` and associated variables).

## Handy documentation pointers about charming

- [Integrations (how to provide and require relations)](https://juju.is/docs/sdk/integration)

### Enable the K8s Dashboard

You need an auth token in case you want to connect to the kubernetes dashboard:

```bash
microk8s kubectl describe secret -n kube-system microk8s-dashboard-token
```
