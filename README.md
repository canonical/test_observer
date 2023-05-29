# Test Observer

Observe the status and state of certification tests for various artefacts

## Prerequisites for developing and deploying locally

- `juju` 3.1 or later (`sudo snap install juju --channel=3.1/stable`)
- `microk8s` 1.27 or later (`sudo snap install microk8s --channel=1.27-strict/stable`)
- `terraform` 1.4.6 or later (`sudo snap install terraform`)
- optional: `jhack` for all kinds of handy Juju and charm SDK development and debugging operations (`sudo snap install jhack`)

## Deploying a local copy of the system

Fist configure microk8s with the needed extensions:

```
sudo microk8s enable community # required for installing traefik
sudo microk8s enable dns hostpath-storage metallb traefik
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

### Deploy with Terraform

In the `terraform` directory of your working copy, complete the one-time initialisation:

```bash
cd terraform
terraform init
```

After initialization (or after making changes to the terraform configuration) you can deploy the whole system with:

```bash
TF_VAR_environment=development terraform apply -auto-approve
```

At the time of writing, this will accomplish the following:

- the backend API server
- the frontend served using nginx
- a postgresql database
- traefik as ingress
- backend connected to frontend (the backend's public facing base URI passed to the frontend app)
- backend connected to database
- backend connected to load balancer
- frontend connected to load balancer

You can also get SSL certificates automatically managed for the ingress (in case you happen to have a DNS zone with Cloudflare DNS available):

```bash
TF_VAR_environment=development TF_VAR_cloudflare_acme=true TF_VAR_cloudflare_dns_api_token=... TF_VAR_cloudflare_zone_read_api_token=... TF_VAR_cloudflare_email=... terraform apply -auto-approve
```

After all is up, `juju status --relations` should give you output to the direction of the following (the acme-operator only there if `TF_VAR_cloudflare_acme` was passed in):

```bash
❯ juju status --relations
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

## Build and refresh the backend charm

Once you have your system running, you can make edits to the backend charm and refresh it in the running system on the fly with:

```bash
cd backend/charm
charmcraft pack
juju refresh test-observer-api --path ./test-observer-api_ubuntu-22.04-amd64.charm

# If you want to update the OCI image that runs the backend
juju attach-resource test-observer-api --resource api-image=ghcr.io/canonical/test_observer/backend:[tag or sha]
```

## Build and refresh the frontend charm

Same thing with the frontend:

```bash
cd frontend/charm
charmcraft pack

juju refresh test-observer-frontend ./test-observer-frontend_ubuntu-22.04-amd64.charm

# If you want to update the OCI image that runs the backend
juju attach-resource test-observer-frontend frontend-image=ghcr.io/canonical/test_observer/frontend:[tag or sha]
```

### Expose the application through ingress

To test the application with the frontend and API server ports exposed, you need to create some aliases in `/etc/hosts` either to `127.0.0.1` or the IP address that you gave `metallb` (`juju status` will find you that):

```bash
❯ cat /etc/hosts
127.0.0.1       localhost test-observer-frontend test-observer-api
...
```

## Handy documentation pointers about charming

- [Integrations (how to provide and require relations)](https://juju.is/docs/sdk/integration)

### Enable the K8s Dashboard

You need an auth token in case you want to connect to the kubernetes dashboard:

```bash
microk8s kubectl describe secret -n kube-system microk8s-dashboard-token
```
