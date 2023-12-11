# Test Observer

Observe the status and state of certification tests for various artefacts

## Prerequisites for deploying locally

- `juju` 3.1 or later (`sudo snap install juju --channel=3.1/stable`)
- `microk8s` 1.27 or later (`sudo snap install microk8s --channel=1.27-strict/stable`) + [permission setup steps after install](https://juju.is/docs/sdk/set-up-your-development-environment#heading--install-microk8s)
- `terraform` 1.4.6 or later (`sudo snap install terraform --classic`)
- `lxd` 5.19 or later (`sudo snap install lxd --channel=5.19/stable` or `sudo snap refresh lxd --channel=5.19/stable` if already installed) + `lxd init --auto` after install.
- `charmcraft` 2.3.0 or later (`sudo snap install charmcraft --channel=2.x/stable --classic`)
- optional: `jhack` for all kinds of handy Juju and charm SDK development and debugging operations (`sudo snap install jhack`)

## Deploying a copy of the system with terraform / juju in microk8s

Workaround for juju bug https://bugs.launchpad.net/juju/+bug/1988355

```
mkdir -p ~/.local/share
```

Fist configure microk8s with the needed extensions:

```
sudo microk8s enable dns hostpath-storage metallb ingress# metallb setup involves choosing a free IP range for the load balancer.
```

Setup juju:

```bash
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
- nginx as ingress
- backend connected to frontend (the backend's public facing base URI passed to the frontend app)
- backend connected to database
- backend connected to load balancer
- frontend connected to load balancer

Terraform works by applying changes between the current state of the system and what is in the plan (the test-observer.tf configuration file). When `terraform apply` is run the 1st time, there is no state -> it will create the Juju model and all resources inside it. When it is run with a pre-existing model already in place, it will instead set / unset config values that have changed, add / remove relations, add / remove applications, etc. Basically, it makes working with Juju declarative - yay!

The terraform juju provider is documented over here: https://registry.terraform.io/providers/juju/juju/latest/docs

Terraform tracks its state with a .tfstate file which is created as a result of running `terraform apply` -- for production purposes this will be stored in an S3-like bucket remotely, and for local development purposes it sits in the `terraform` directory aftery you have done a `terraform apply`).

After all is up, you can run `juju switch test-observer-development` to use the development juju model. Then `juju status --relations` should give you output to the direction of the following:

```bash
$ juju status --relations
Model                      Controller       Cloud/Region        Version  SLA          Timestamp
test-observer-development  juju-controller  microk8s/localhost  3.1.2    unsupported  15:38:51+03:00

App       Version  Status  Scale  Charm                     Channel      Rev  Address         Exposed  Message
api                active      1  test-observer-api         latest/edge   15  10.152.183.182  no       
db        14.7     active      1  postgresql-k8s            14/stable     73  10.152.183.172  no       Primary
frontend           active      1  test-observer-frontend    latest/edge    8  10.152.183.79   no       
ingress   25.3.0   active      1  nginx-ingress-integrator  stable        59  10.152.183.103  no       Ingress IP(s): 127.0.0.1, 127.0.0.1, Service IP(s): 10.152.183.72, 10.152.183.34

Unit         Workload  Agent  Address       Ports  Message
api/0*       active    idle   10.1.131.142         
db/0*        active    idle   10.1.131.132         Primary
frontend/0*  active    idle   10.1.131.169         
ingress/0*   active    idle   10.1.131.167         Ingress IP(s): 127.0.0.1, 127.0.0.1, Service IP(s): 10.152.183.72, 10.152.183.34

Relation provider           Requirer                         Interface          Type     Message
api:test-observer-rest-api  frontend:test-observer-rest-api  http               regular  
db:database                 api:database                     postgresql_client  regular  
db:database-peers           db:database-peers                postgresql_peers   peer     
db:restart                  db:restart                       rolling_op         peer     
ingress:nginx-route         api:nginx-route                  nginx-route        regular  
ingress:nginx-route         frontend:nginx-route             nginx-route        regular
```

## Add /etc/hosts entries

To test the application, you need to create some aliases in `/etc/hosts` to the IP address that the ingress got from `metallb` (`juju status` above will find you the ingress IP). Let's assume you have a domain `mah-domain.com` that you want to expose service under, the backend and frontend will be present as subdomains `test-observer.mah-domain.com` and `test-observer-api.mah-domain.com`, respectively:

```bash
$ cat /etc/hosts
192.168.0.202   test-observer.mah-domain.com test-observer-api.mah-domain.com
...
```

Note that without this step the frontend will fail to connect to api as it's trying to use `test-observer-api.mah-domain.com`

## Developing the charm

To develop and test updates to the backend and frontend charms, you would typically want to first complete the above steps to deploy a working system. Once you have done that, proceed with the following steps.

### Build and refresh the backend charm

You can make edits to the backend charm and refresh it in the running system on the fly with:

```bash
cd backend/charm
charmcraft pack
juju refresh test-observer-api --path ./test-observer-api_ubuntu-22.04-amd64.charm

# to update the OCI image that runs the backend
juju attach-resource test-observer-api api-image=ghcr.io/canonical/test_observer/backend:[tag or sha]
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

### Enable the K8s Dashboard

You need an auth token in case you want to connect to the kubernetes dashboard:

```bash
microk8s kubectl describe secret -n kube-system microk8s-dashboard-token
```
