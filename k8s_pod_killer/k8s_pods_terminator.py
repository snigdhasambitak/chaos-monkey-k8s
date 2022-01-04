from kubernetes import client
from kubernetes.client.rest import ApiException
from k8s_pod_killer.k8s_pod_utility import _random_num_list_generator
from k8s_pod_killer.k8s_logging import _logging
from k8s_pod_killer.k8s_prom_metrics import prom


#invoke logger
logger = _logging()

#invoke prom
metric_collector = prom()


def _kill_selected_pods(num_pods=1, dry_run=True, grace=0, inclusions=[], exclusions=[], podannotations=''):
    pods = _list_pods(included_namespaces=inclusions, excluded_namespaces=exclusions, pod_annotations=podannotations)
    if pods:
        return [_kill_pod(pod=pod, dry_run=dry_run, grace=grace) for pod in _random_pod_selector(pods, num_pods)]


def _get_pods():
    core_api = client.CoreV1Api()
    try:
        return core_api.list_pod_for_all_namespaces(timeout_seconds=60)
    except ApiException as e:
        logger.error(f"Could not fetch list of pods, error message: {e}")
        return None


def _list_pods(included_namespaces=[], excluded_namespaces=[], pod_annotations=''):
    all_pods = _get_pods()
    if all_pods:
        if len(included_namespaces) > 0:
            if pod_annotations:
                pods = [[pod.metadata.name, pod.metadata.namespace]
                        for pod in all_pods.items if all([pod.metadata.namespace in included_namespaces, pod.metadata.annotations and pod_annotations in pod.metadata.annotations])]
            else:
                pods = [[pod.metadata.name, pod.metadata.namespace]
                        for pod in all_pods.items if pod.metadata.namespace in included_namespaces]

        else:
            if pod_annotations:
                pods = [[pod.metadata.name, pod.metadata.namespace]
                        for pod in all_pods.items if all([pod.metadata.namespace not in excluded_namespaces, pod.metadata.annotations and pod_annotations in pod.metadata.annotations])]

            else:
                pods = [[pod.metadata.name, pod.metadata.namespace]
                        for pod in all_pods.items if pod.metadata.namespace not in excluded_namespaces]

        logger.debug(f"Found {len(pods)} pods")
        return pods


def _random_pod_selector(pods, num_pods=1):
    if len(pods) < num_pods:
        num_pods = len(pods)
        logger.warning("Found fewer pods than the number to be terminated! All pods will be deleted per cycle")
    pod_nums = _random_num_list_generator(len(pods), num_pods)
    return [tuple(pods[i]) for i in pod_nums]


def _kill_pod(pod, dry_run=False, grace=0, i=[0]):
    name = pod[0]
    ns = pod[1]
    i[0] += 1
    metric_collector._add_total_pod_killed_metric()
    if dry_run:
        logger.info(f"DRY-RUN: Pod {name} in {ns} namespace would have been deleted and total no of pods deleted is {i[0]}")
        metric_collector._add_pod_killed_metric(name, ns)
    else:
        core_api = client.CoreV1Api()
        try:
            core_api.delete_namespaced_pod(name=name, namespace=ns, grace_period_seconds=grace)
            logger.debug(f"Deleted pod: {name} in {ns} and total no of pods deleted is {i[0]}")
            metric_collector._add_pod_killed_metric(name, ns)
        except ApiException as e:
            logger.error(f"Failed to delete pod, error message: {e}")
