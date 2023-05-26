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
juju deploy ./test-observer_ubuntu-22.04-amd64.charm --resource api-image=ghcr.io/canonical/test_observer/backend:[tag or sha]
```

Integrate the test observer service with the database:

```bash
juju integrate pg test-observer
```

Build and deploy the frontend charm:

```bash
cd frontend/charm
charmcraft pack
juju deploy ./test-observer_ubuntu-22.04-amd64.charm --resource api-image=ghcr.io/canonical/test_observer/frontend:[tag or sha]
```

Update the charm after making edits:

```bash
charmcraft pack
juju refresh test-observer --path ./test-observer_ubuntu-22.04-amd64.charm --resource api-image=ghcr.io/canonical/test_observer/backend:[tag or sha]
juju refresh test-observer-frontend --path ./test-observer-frontend_ubuntu-22.04-amd64.charm --resource frontend-image=ghcr.io/canonical/test_observer/frontend:[tag or sha]
```

### Fetching the data platform libraries

In case you need to fetch the data platform libraries to update them, `charmcraft` is your friend:

```bash
charmcraft fetch-lib charms.data_platform_libs.v0.data_interfaces
```
