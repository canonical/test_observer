# Juju deployment

Local Juju and charm deployment via microk8s and terraform.

## Setup a juju environment

Setup an environment to use for any juju deployment.

It is recommended to install the pre-requisites on a VM rather than your host machine. To do so, first install multipass:

```bash
sudo snap install multipass
```

Then launch a new VM instance using (this will take a while):

```bash
multipass launch noble --disk 50G --memory 4G --cpus 2 --name test-observer-juju --mount /path/to/test_observer:/home/ubuntu/test_observer --cloud-init /path/to/test_observer/terraform/cloud-init.yaml --timeout 1200
```

Feel free to increase the storage, memory, cpu limits or change the VM name.

## Initialize project's terraform

Now that everything has been set up, you can initialize the project's terraform.

In the terraform directory on your host machine, run:

```bash
multipass exec test-observer-juju -- terraform init
```

## Deploy everything

In the terraform directory on your host machine, run:

```bash
multipass exec test-observer-juju -- TF_VAR_environment=development TF_VAR_external_ingress_hostname=local terraform apply -auto-approve
```

Then wait for the deployment to settle and all the statuses to become active. You can watch the statuses via:

```bash
multipass exec test-observer-juju -- juju status --storage --relations --watch 5s
```

## Connect to your deployment

Look at the IPv4 addresses of your test-observer-juju vm through:

```bash
multipass info test-observer-juju
```

One of these connect to the ingress enabled inside the VM. To figure out which one try the following command on each IP address until you get response:

```bash
curl --connect-to ::<ip-address> http://test-observer-api.local
```

Once you find the IP address add the following entry to your host machine's `/etc/hosts` file:

```text
<ip-address>   test-observer.local test-observer-api.local
```

After that you should be able to get to TO frontend on your host machine's browser through the url `http://test-observer.local`. You should also be able to access the API through `http://test-observer-api.local`.

## Teardown

To take everything down you can start with terraform:

```bash
multipass exec test-observer-juju -- TF_VAR_environment=development TF_VAR_external_ingress_hostname=local terraform destroy -auto-approve
```

The above step can take a while and may even get stuck with some applications in error state. You can watch it through:

```bash
multipass exec test-observer-juju -- juju status --storage --relations --watch 5s
```

To forcefully remove applications stuck in error state:

```bash
multipass exec test-observer-juju -- juju remove-application <application-name> --destroy-storage --force
```

Once everything is down and the juju model has been deleted you can stop the multipass VM:

```bash
multipass stop test-observer-juju
```

Optionally, delete the VM:

```bash
multipass delete --purge test-observer-juju
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
