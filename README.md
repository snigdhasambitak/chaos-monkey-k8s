# chaos-monkey-k8s

This repository contains the Python scripts, Dockerfile and associated Kubernetes configuration for a Deployment that will randomly delete pods in a given namespace. This is implemented in Python mostly.

An image built from the Dockerfile in this repository is available on Docker Hub as  [snigdhasambit/chaos-monkey-k8s:1.2](https://hub.docker.com/repository/docker/snigdhasambit/chaos-monkey-k8s)

## Project structure and files

* The `root` directory of the project contains the following files
    * `k8s_pod_killer` folder that contains all the chaos monkey code base
      * `k8s_api_client.py` k8s client to import the kubeconfig and contexts
      * `k8s_logging.py` module to configure logging
      * `k8s_pod_utility.py` module to configure the utilities around pod deletion
      * `k8s_pod_terminator.py` module to randomly choose and delete a pod
      * `k8s_prom_metrics.py` module to export the pod deletion count metrics based on pod and namespace lables
      * `__init__.py` loads dependent modules
        
    * `charts` folder contains helm chart files.
      * `chaos-monkey-helm`
          * `configs`
            * `config.yaml` config file to set a number of options to change the apps behaviour like `updateFrequency`, `includedNamespaces`, `excludedNamespaces` etc
          * `templates` folder contains the following:
            * `deployment.yaml` contains K8s deployment specifics and env level variables.
            * `configmap.yaml` configMap object that has the `config.yaml` file to configure some app parameters
            * `hpa.yaml` is used to specify auto-pod scaling in the cluster
            * `NetworkPolicy.yaml` file manages external access to the services in a cluster, typically HTTP.
            * `pdb.yaml` file is used to manage Pod Distribution Budget that the cluster will honor
            * `service.yaml` specifies service management like the loadbalancer with AWS
            * `serviceaccount.yaml`  service account to be used for our deployment
            * `clusterrole.yaml`  cluster role object that grants our service account access to list/delete pods and create events
            * `clusterrolebinding.yaml`  cluster role binding object that binds the service account to the cluster role
          
          *`chart.yaml` is used to specify app-pod level information that is used throughout the K8s config
        
          *`values.yaml` is used to handle app information and specifics. we can use `values/dev.yaml`
      to override these values and use them for each environment.
    * `main.py` the main python script that runs our app by invoking all the modules and dependencies
    * `requirements.txt` contains all the python dependencies
    * `Makefile` for running things from lcoal, we can configure our scripts in the makefile
    * `Dockerfile` is the dockerfile used to build the image and/or run the app
    * `config.yaml` is the config file for local use
    

---

## Getting Started

The chaos-monkey app will run against the current Kubernetes context. It'll start finding and deleting pods against your locally authenticated cluster, or in your remote k8s cluster.

It will randomly kills a pod every `X` minutes. This can be set using the `updateFrequency` config variable. See `chart/chaos-monkey-helm/configs/config` or for local development you can find use the `config.yaml` found in the root of the project location

You can also set the `includedNamespaces`, `excludedNamespaces` and 'podAnnotation' based on your choice. 

You can specify a `config file` to set a number of options to change the agent's behaviour:

Defaults are set in `class Config` in `k8s_pod_killer/k8s_pods_utility.py`

When using `make local_run` , the `config.yaml` found in the root directory will be loaded


| Config Env Variable | Value |
|----------|-----------
| dryRun  | Set to `True` to just print the pod to be deleted, without taking action. By default it is set to `False`|
| updateFrequency  | The frequency of pod deletion. By default it is set to `45`
| randomiseFrequency  | If set to True, it will randomly sleep for a time between 1->`updateFrequency` seconds, rather than a regular cadence. It is set to `False` by default
| gracePeriod  | Seconds that the k8s api call will allow for the pod to shut down gracefully. Defaults to `0`
| numPodsToDelete  | How many pods to delete per cycle. Set to `0 to skip`, defaults to `1`
| includedNamespaces  | `[optional]` Only terminates pods within this namespace. Defaults to all namespaces
| excludedNamespaces  | `[optional]` Ignores pods in these namespaces. Defaults to `kube-system`
| podAnnotation  | `[optional]` Only delete pods using this annotations. Defaults to `empty: ''`. For testing please annotate your deployment with something like `chaos-monkey-k8s/enabled` and test



## Local Development

We can use the Makefile for local development. The contents of the makefile are as follows:

```shell
OSTYPE ?= darwin
env ?= dev
app_name ?= chaos-monkey-app
repo_root = ${PWD}
cluster_name ?= gke_test_cluster
namespace_name ?= test-delete
dry_run ?= true
debug ?= false
helm_root ?= ${PWD}/chart/chaos-monkey-helm
docker_repo ?= snigdhasambit/chaos-monkey-k8s
docker_release ?= 1.2
CFG_FILE ?= config.yaml
KUBECONFIG ?= /root/.kube/config


deps:
	pip3 install -r requirements.txt

set_namespace:
	kubectl config use-context ${cluster_name} --kubeconfig=${KUBECONFIG} \
  	kubectl config set-context ${cluster_name} --namespace ${namespace_name} --kubeconfig=${KUBECONFIG}

local_run: deps
	export CFG_FILE=${CFG_FILE}
	export DEBUG=True
	python -u main.py

docker_build:
	docker build ${repo_root} -t ${docker_repo}:${docker_release}

docker_release: docker_build
	docker push ${docker_repo}:${docker_release}

deploy_dry:
	helm upgrade -i ${app_name} ${helm_root} \
    --set ImageVersion=${docker_release} \
    --debug \
    --dry-run

deploy: docker_release
	helm upgrade -i ${app_name} ${helm_root} \
	--set ImageVersion=${docker_release} \
    --debug

destroy:
	helm delete ${app_name}
```
## Test

**Once your deploy the helm charts and run the app in `DRY-RUN` mode. You should be able to see the following logs**

```log
-> [INFO] [2021-05-15 14:02] Cannot find in-cluster config, trying the local kubernetes config. 
-> [INFO] [2021-05-15 14:02] Found local kubernetes config. Initialized with kube_config.
-> [INFO] [2021-05-15 14:02] DRY-RUN: Pod nginx-deployment-76fcc798b6-dfvdf in test-delete namespace would have been deleted and total no of pods deleted is 1
-> [INFO] [2021-05-15 14:02] DRY-RUN: Pod nginx-deployment-76fcc798b6-kq7ct in test-delete namespace would have been deleted and total no of pods deleted is 2
-> [INFO] [2021-05-15 14:02] DRY-RUN: Pod nginx-deployment-76fcc798b6-kq7ct in test-delete namespace would have been deleted and total no of pods deleted is 3
-> [INFO] [2021-05-15 14:02] DRY-RUN: Pod nginx-deployment-76fcc798b6-w6zxb in test-delete namespace would have been deleted and total no of pods deleted is 4
-> [INFO] [2021-05-15 14:02] DRY-RUN: Pod nginx-deployment-76fcc798b6-r6r68 in test-delete namespace would have been deleted and total no of pods deleted is 5
-> [INFO] [2021-05-15 14:02] DRY-RUN: Pod nginx-deployment-76fcc798b6-r6r68 in test-delete namespace would have been deleted and total no of pods deleted is 6
-> [INFO] [2021-05-15 14:03] DRY-RUN: Pod nginx-deployment-76fcc798b6-r6r68 in test-delete namespace would have been deleted and total no of pods deleted is 7
-> [INFO] [2021-05-15 14:03] DRY-RUN: Pod nginx-deployment-76fcc798b6-kq7ct in test-delete namespace would have been deleted and total no of pods deleted is 8
-> [INFO] [2021-05-15 14:03] DRY-RUN: Pod nginx-deployment-76fcc798b6-r6r68 in test-delete namespace would have been deleted and total no of pods deleted is 9
-> [INFO] [2021-05-15 14:03] DRY-RUN: Pod nginx-deployment-76fcc798b6-r6r68 in test-delete namespace would have been deleted and total no of pods deleted is 10
```

**In an actual deployment without `DRY-RUN` mode, you will have to set your environmet variable `DEBUG to True`**

```shell
export DEBUG=True
```

**The logs generated will be as follows:**

```log
chaos-monkey-app-68879d5c77-gt68f chaos-monkey-app -> [DEBUG] [2021-05-15 08:50] DEBUG mode enabled - actions will be printed to log
chaos-monkey-app-68879d5c77-gt68f chaos-monkey-app -> [DEBUG] [2021-05-15 08:50] Starting prometheus server on port 9000
chaos-monkey-app-68879d5c77-gt68f chaos-monkey-app -> [DEBUG] [2021-05-15 08:50] Config initialised with the following values:
chaos-monkey-app-68879d5c77-gt68f chaos-monkey-app -> [DEBUG] [2021-05-15 08:50]   Dry Run:                False
chaos-monkey-app-68879d5c77-gt68f chaos-monkey-app -> [DEBUG] [2021-05-15 08:50]   Update Frequency:       45
chaos-monkey-app-68879d5c77-gt68f chaos-monkey-app -> [DEBUG] [2021-05-15 08:50]   Grace Period:           30
chaos-monkey-app-68879d5c77-gt68f chaos-monkey-app -> [DEBUG] [2021-05-15 08:50]   Randomised Frequency:   False
chaos-monkey-app-68879d5c77-gt68f chaos-monkey-app -> [DEBUG] [2021-05-15 08:50]   Included Namespaces:    ['test-delete']
chaos-monkey-app-68879d5c77-gt68f chaos-monkey-app -> [DEBUG] [2021-05-15 08:50]   Excluded Namespaces:    ['kube-system', 'default']
chaos-monkey-app-68879d5c77-gt68f chaos-monkey-app -> [DEBUG] [2021-05-15 08:50]   Pods Annotation:
chaos-monkey-app-68879d5c77-gt68f chaos-monkey-app -> [DEBUG] [2021-05-15 08:50]   Pods To Delete:         1
chaos-monkey-app-68879d5c77-gt68f chaos-monkey-app -> [INFO] [2021-05-15 08:50] Initialized with in-cluster config.
chaos-monkey-app-68879d5c77-gt68f chaos-monkey-app -> [DEBUG] [2021-05-15 08:50] Found 12 pods
chaos-monkey-app-68879d5c77-gt68f chaos-monkey-app -> [DEBUG] [2021-05-15 08:50] Deleted pod: hello-node-7bf657c596-dxhjw in test-delete and total no of pods deleted is 1
chaos-monkey-app-68879d5c77-gt68f chaos-monkey-app -> [DEBUG] [2021-05-15 08:50] Sleeping for 45
- chaos-monkey-app-68879d5c77-xs685
chaos-monkey-app-68879d5c77-gt68f chaos-monkey-app -> [DEBUG] [2021-05-15 08:51] Found 11 pods
chaos-monkey-app-68879d5c77-gt68f chaos-monkey-app -> [DEBUG] [2021-05-15 08:51] Deleted pod: hello-node-7bf657c596-6kn8g in test-delete and total no of pods deleted is 2
chaos-monkey-app-68879d5c77-gt68f chaos-monkey-app -> [DEBUG] [2021-05-15 08:51] Sleeping for 45
chaos-monkey-app-68879d5c77-gt68f chaos-monkey-app -> [DEBUG] [2021-05-15 08:52] Found 11 pods
chaos-monkey-app-68879d5c77-gt68f chaos-monkey-app -> [DEBUG] [2021-05-15 08:52] Deleted pod: nginx-deployment-76fcc798b6-kq7ct in test-delete and total no of pods deleted is 3
chaos-monkey-app-68879d5c77-gt68f chaos-monkey-app -> [DEBUG] [2021-05-15 08:52] Sleeping for 45
chaos-monkey-app-68879d5c77-gt68f chaos-monkey-app -> [DEBUG] [2021-05-15 08:52] Found 11 pods
chaos-monkey-app-68879d5c77-gt68f chaos-monkey-app -> [DEBUG] [2021-05-15 08:52] Deleted pod: nginx-deployment-76fcc798b6-r6r68 in test-delete and total no of pods deleted is 4
chaos-monkey-app-68879d5c77-gt68f chaos-monkey-app -> [DEBUG] [2021-05-15 08:52] Sleeping for 45
```

## Expose Prometheus Metrics

We want to get the pod and namepsace lables along with the pod deletion counts. So, we have to use the prometheus client

By default prometheus is running on port `9000`

**For local testing:**

```shell
#locally run the app
make local_run

# open port 9000 to check the promnetheus metrics
open http://localhost:9000

```

**For testing in your k8s cluster**
```shell
# build, release and deploy the helm charts
make deploy

# check logs
kubectl logs chaos-monkey-app-68879d5c77-gt68f

#kubectl port forward to port 900, for viewing the prometheus metrics
kubectl port-forward pod/chaos-monkey-app-68879d5c77-gt68f 9000:9000

# open port 9000 to check the promnetheus metrics
open http://localhost:9000 
```

**You should be able to get the following prometheus metrics**

```log
# HELP python_gc_objects_collected_total Objects collected during gc
# TYPE python_gc_objects_collected_total counter
python_gc_objects_collected_total{generation="0"} 431.0
python_gc_objects_collected_total{generation="1"} 0.0
python_gc_objects_collected_total{generation="2"} 10.0
# HELP python_gc_objects_uncollectable_total Uncollectable object found during GC
# TYPE python_gc_objects_uncollectable_total counter
python_gc_objects_uncollectable_total{generation="0"} 0.0
python_gc_objects_uncollectable_total{generation="1"} 0.0
python_gc_objects_uncollectable_total{generation="2"} 0.0
# HELP python_gc_collections_total Number of times this generation was collected
# TYPE python_gc_collections_total counter
python_gc_collections_total{generation="0"} 576.0
python_gc_collections_total{generation="1"} 52.0
python_gc_collections_total{generation="2"} 4.0
# HELP python_info Python platform information
# TYPE python_info gauge
python_info{implementation="CPython",major="3",minor="9",patchlevel="5",version="3.9.5"} 1.0
# HELP process_virtual_memory_bytes Virtual memory size in bytes.
# TYPE process_virtual_memory_bytes gauge
process_virtual_memory_bytes 7.0483968e+07
# HELP process_resident_memory_bytes Resident memory size in bytes.
# TYPE process_resident_memory_bytes gauge
process_resident_memory_bytes 6.4557056e+07
# HELP process_start_time_seconds Start time of the process since unix epoch in seconds.
# TYPE process_start_time_seconds gauge
process_start_time_seconds 1.62106861677e+09
# HELP process_cpu_seconds_total Total user and system CPU time spent in seconds.
# TYPE process_cpu_seconds_total counter
process_cpu_seconds_total 2.36
# HELP process_open_fds Number of open file descriptors.
# TYPE process_open_fds gauge
process_open_fds 7.0
# HELP process_max_fds Maximum number of open file descriptors.
# TYPE process_max_fds gauge
process_max_fds 1.048576e+06
# HELP total_no_of_pods_killed_total Total number of pods killed
# TYPE total_no_of_pods_killed_total counter
total_no_of_pods_killed_total 4.0
# HELP total_no_of_pods_killed_created Total number of pods killed
# TYPE total_no_of_pods_killed_created gauge
total_no_of_pods_killed_created 1.6210686246915545e+09
# HELP pod_kills_total Number of each pods killed 
# TYPE pod_kills_total counter
pod_kills_total{name="hello-node-7bf657c596-dxhjw",namespace="test-delete"} 1.0
pod_kills_total{name="hello-node-7bf657c596-6kn8g",namespace="test-delete"} 1.0
pod_kills_total{name="nginx-deployment-76fcc798b6-kq7ct",namespace="test-delete"} 1.0
pod_kills_total{name="nginx-deployment-76fcc798b6-r6r68",namespace="test-delete"} 1.0
# HELP pod_kills_created Number of each pods killed 
# TYPE pod_kills_created gauge
pod_kills_created{name="hello-node-7bf657c596-dxhjw",namespace="test-delete"} 1.621068628889449e+09
pod_kills_created{name="hello-node-7bf657c596-6kn8g",namespace="test-delete"} 1.6210686779948852e+09
pod_kills_created{name="nginx-deployment-76fcc798b6-kq7ct",namespace="test-delete"} 1.621068726596903e+09
pod_kills_created{name="nginx-deployment-76fcc798b6-r6r68",namespace="test-delete"} 1.6210687755034993e+09
# HELP empty_match_total Increasing counter for cases where matching returns an empty result
# TYPE empty_match_total counter
empty_match_total{source="pods"} 0.0
# HELP empty_match_created Increasing counter for cases where matching returns an empty result
# TYPE empty_match_created gauge
empty_match_created{source="pods"} 1.621068624691711e+09
```

## Teardown

To tear down the deployment, please run

```shell
make destroy
```