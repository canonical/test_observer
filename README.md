# Test Observer

Observe the status and state of certification tests for various artefacts

## Developing and deploying the charm locally

Install prerequisites for developing the Test Observer charm:

- juju 3.1 or later (`sudo snap install juju --channel=3.1/stable`)
- microk8s 1.27 or later (`sudo snap install microk8s --channel=1.27-strict/stable`)
- charmcraft (`sudo snap install charmcraft`)

Get a GitHub personal access token at https://github.com/settings/tokens/new with the `package:read` permission.

Configure containerd in microk8s over at `/var/snap/microk8s/current/args/containerd-template.toml` with the auth credentials needed to pull images from non-default, authorisation requiring OCI registries:

```yaml
[plugins."io.containerd.grpc.v1.cri".registry.configs."ghcr.io".auth]
  username = "mz2"
  password = "your-GitHub-API-token"
```

Create a microk8s Juju controller and model:

```
juju bootstrap microk8s
juju add-model test-observer

# enable debug logging
juju model-config logging-config="<root>=DEBUG"
```

Build and deploy the charm:

```
charmcraft pack
juju deploy ./test-observer_ubuntu-22.04-amd64.charm --resource api-image=ghcr.io/canonical/test_observer:charm
```

Update the charm after making edits:
```
charmcraft pack
juju refresh test-observer --path ./test-observer_ubuntu-22.04-amd64.charm --resource api-image=ghcr.io/canonical/test_observer:charm
```
