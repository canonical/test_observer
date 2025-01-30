# Juju deployment

Local Juju and charm deployment via microk8s and terraform.

## Setup

It is recommended to install the pre-requisites on a VM rather than your host machine. To do so, first install multipass:

```bash
sudo snap install multipass
```

Then launch the "charm-dev" VM blueprint that comes pre-setup with required tools (this will take a while):

```bash
multipass launch --mount $HOME charm-dev
```

Note the home mount to access the project files in the VM.

Once the VM initialization has been completed, you will need to enable microk8s ingress there:

```bash
multipass exec charm-dev -- sudo microk8s enable ingress
```

Then install terraform:

```bash
multipass exec charm-dev -- sudo snap install terraform --classic
```

And initialize it:

```bash
multipass exec charm-dev -- terraform init
```

## Deploy

You can deploy everything using terraform by running:

```bash
multipass exec charm-dev -- TF_VAR_environment=development TF_VAR_external_ingress_hostname=local terraform apply -auto-approve
```

Then wait for the deployment to settle and all the statuses to become active. You can watch the statuses via:

```bash
multipass exec charm-dev -- JUJU_MODEL=test-observer-development juju status --storage --relations --watch 5s
```

Look at the IPv4 addresses of your charm-dev vm through:

```bash
multipass info charm-dev
```

One of these connect to the ingress enabled inside the VM. To figure out which one try the following command on each IP address until you get response:

```bash
curl --connect-to ::<ip-address> http://test-observer-api.local
```

Once you find the IP address add the following entry to your host machine's `/etc/hosts` file:

```bash
<ip-address>   test-observer.local test-observer-api.local
```

After that you should be able to get to TO frontend on your host machine's browser through the url test-observer.local. You should also be able to access the API through test-observer-api.local.

## Teardown

To take everything down you can start with terraform:

```bash
multipass exec charm-dev -- TF_VAR_environment=development TF_VAR_external_ingress_hostname=local terraform destroy --auto-approve
```

The above step can take a while and may even get stuck with some applications in error state. You can watch it through:

```bash
multipass exec charm-dev -- JUJU_MODEL=test-observer-development juju status --storage --relations --watch 5s
```

To forcefully remove applications stuck in error state:

```bash
multipass exec charm-dev -- JUJU_MODEL=test-observer-development juju remove-application <application-name> --destroy-storage --force
```

Once everything is down and the juju model has been deleted you can stop the multipass VM:

```bash
multipass stop charm-dev
```

## Developing the charm

To develop and test updates to the backend and frontend charms, you would typically want to first complete the above steps to deploy a working system. Once you have done that, proceed with the following steps.

### Build and refresh the backend charm

You can make edits to the backend charm and refresh it in the running system on the fly with:

```bash
cd backend/charm
charmcraft pack
juju refresh api --path ./test-observer-api_ubuntu-22.04-amd64.charm

# to update the OCI image that runs the backend
juju attach-resource api api-image=ghcr.io/canonical/test_observer/backend:[tag or sha]
```

### Build and refresh the frontend charm

Same thing with the frontend:

```bash
cd frontend/charm
charmcraft pack

juju refresh frontend ./test-observer-frontend_ubuntu-22.04-amd64.charm

# to update the OCI image that runs the backend
juju attach-resource frontend frontend-image=ghcr.io/canonical/test_observer/frontend:[tag or sha]
```

Note that the frontend app is made aware of the backend URL to connect to using the global `window.testObserverAPIBaseURI`, which is set at runtime with some nginx config level trickery based on...

- the `test-observer-api` charm's `hostname` config value.
- the frontend charm's `test-observer-api-scheme` config value.

These in turn can be set using the terraform plan (`terraform/test-observer.tf` and associated variables).

## Running tests

To run the unit and integration tests for the frontend charms, do the following:

```bash
cd frontend/charm
tox -e unit
tox -e integration
```

## Releasing the charms

Charms are released through GitHub actions on push to main. If however you need to release charms on your branch before merging with main you could always just add your branch as a trigger to those same GitHub actions.

## VS Code & charm libraries

VS Code fails to find (for autocompletions and code navigation purposes) the charm libraries under `lib` in each of `backend/charm` and `frontend/charm`. There is a .vscode-settings-default.json found under each of these directories which you can copy to the `.gitignore`d path `.vscode/settings.json` to make them fly. Taking the backend charm as an example:

```bash
mkdir -p backend/charm/.vscode
cp backend/charm/.vscode-settings-default.json backend/charm/.vscode/settings.json

mkdir -p frontend/charm/.vscode
cp frontend/charm/.vscode-settings-default.json frontend/charm/.vscode/settings.json
```

Now if you use as your project the directory `backend/charm` and `frontend/charm` respectively (which you'll want to do also for them to keep their own virtual environments), VS Code should be happy.

## Handy documentation pointers about charming

- [Integrations (how to provide and require relations)](https://juju.is/docs/sdk/integration)
