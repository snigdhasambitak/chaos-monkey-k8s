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
