# Test Observer

Observe the status and state of certification tests for various artefacts

## Developing and deploying the charm locally

Install prerequisites for developing the Test Observer charm:

- juju 3.1 or later (`sudo snap install juju --channel=3.1/stable`)
- microk8s 1.27 or later (`sudo snap install microk8s --channel=1.27-strict/stable`)
- charmcraft (`sudo snap install charmcraft`)

Get a GitHub personal access token at https://github.com/settings/tokens/new with the `package:read` permission.

Configure containerd in microk8s with the auth credentials needed to pull images from non-default, authorisation requiring OCI registries by appending the following to `/var/snap/microk8s/current/args/containerd-template.toml`:

```yaml
[plugins."io.containerd.grpc.v1.cri".registry.configs."ghcr.io".auth]
  username = "mz2"
  password = "your-GitHub-API-token"
```

After this config file tweak, restart containerd and microk8s:

```bash
sudo systemctl restart snap.microk8s.daemon-containerd.service && sudo microk8s.stop && sudo microk8s.start
```

Create a microk8s Juju controller and model:

```bash
juju bootstrap microk8s
juju add-model test-observer

# enable debug logging
juju model-config logging-config="<root>=DEBUG"
```

Deploy PostgreSQL into your cluster:

```bash
juju deploy postgresql-k8s --channel=14/stable pg
```

Build and deploy the backend charm:

```bash
cd backend/charm
charmcraft pack
juju deploy ./test-observer-api_ubuntu-22.04-amd64.charm --resource api-image=ghcr.io/canonical/test_observer/backend:[tag or sha]
```

Integrate the test observer service with the database:

```bash
juju integrate pg test-observer-api
```

Build and deploy the frontend charm:

```bash
cd frontend/charm
charmcraft pack
juju deploy ./test-observer-api_ubuntu-22.04-amd64.charm --resource api-image=ghcr.io/canonical/test_observer/frontend:[tag or sha]
```

### Relate the frontend to the API server

The frontend application needs to be related to the API server for the frontend application to find out the correct hostname to connect to:

```bash
juju integrate test-observer-api test-observer-frontend
```

### Expose the application through ingress

To test the application with the frontend and API server ports exposed through the nginx ingress controller (i.e. how it will run in production), do the following.

Firstly, add the following hostnames for `127.0.0.1` in `/etc/hosts`:

```bash
❯ cat /etc/hosts
127.0.0.1       localhost test-observer-frontend test-observer-api
# ...
```

Then deploy the `nginx-ingress-integrator` charm and relate it to both the frontend and the API server:

```bash
juju deploy nginx-ingress-integrator

# to avoid messing around with self signed SSL certificates,
# change this from https:// to http://
juju config test-observer-frontend test-observer-api-scheme=http://

juju integrate nginx-ingress-integrator test-observer-api
juju integrate nginx-ingress-integrator test-observer-frontend
```

After all is up, `juju status --relations` should give you output to the direction of:

```
❯ juju status --relations
Model          Controller          Cloud/Region        Version  SLA          Timestamp
test-observer  microk8s-localhost  microk8s/localhost  3.1.2    unsupported  12:30:41+03:00

App                       Version  Status  Scale  Charm                     Channel    Rev  Address         Exposed  Message
nginx-ingress-integrator  25.3.0   active      1  nginx-ingress-integrator  stable      59  10.152.183.54   no       Ingress IP(s): 127.0.0.1, 127.0.0.1, Service IP(s): 10.152.183.58, 10.152.183.232
pg                        14.7     active      1  postgresql-k8s            14/stable   73  10.152.183.97   no       Primary
test-observer-api                  active      1  test-observer-api                     10  10.152.183.23   no
test-observer-frontend             active      1  test-observer-frontend                19  10.152.183.175  no

Unit                         Workload  Agent  Address      Ports  Message
nginx-ingress-integrator/0*  active    idle   10.1.92.140         Ingress IP(s): 127.0.0.1, 127.0.0.1, Service IP(s): 10.152.183.58, 10.152.183.232
pg/0*                        active    idle   10.1.92.129         Primary
test-observer-api/0*         active    idle   10.1.92.145
test-observer-frontend/0*    active    idle   10.1.92.148

Relation provider                            Requirer                                          Interface          Type     Message
nginx-ingress-integrator:nginx-route         test-observer-api:nginx-route                     nginx-route        regular
nginx-ingress-integrator:nginx-route         test-observer-frontend:nginx-route                nginx-route        regular
pg:database                                  test-observer-api:database                        postgresql_client  regular
pg:database-peers                            pg:database-peers                                 postgresql_peers   peer
pg:restart                                   pg:restart                                        rolling_op         peer
test-observer-api:test-observer-rest-api-v1  test-observer-frontend:test-observer-rest-api-v1  http               regular
```

### Fetching the data platform libraries

In case you need to fetch the data platform libraries to update them, `charmcraft` is your friend:

```bash
cd backend/charm
charmcraft fetch-lib charms.data_platform_libs.v0.data_interfaces
charmcraft fetch-lib charms.nginx_ingress_integrator.v0.nginx_route
```

### Update the charm after making edits:

To update the deployed charms after making edits, do `charmcraft pack && juju refresh ...`:

```bash
pushd backend/charm
charmcraft pack
juju refresh test-observer-api --path ./test-observer_ubuntu-22.04-amd64.charm
popd

pushd frontend/charm
charmcraft pack
juju refresh test-observer-frontend --path ./test-observer-frontend_ubuntu-22.04-amd64.charm
popd
```

### Updating the image reference with `juju attach-resource`

To update the OCI image that the API server and frontend applications run, use `juju attach-resource`:

```bash
juju attach-resource test-observer-api api-image=ghcr.io/canonical/test_observer/backend:[tag or sha]
juju attach-resource test-observer-frontend api-image=ghcr.io/canonical/test_observer/frontend:[tag or sha]
```

### Handy documentation pointers about charming

- [Integrations (how to provide and require relations)](https://juju.is/docs/sdk/integration)
