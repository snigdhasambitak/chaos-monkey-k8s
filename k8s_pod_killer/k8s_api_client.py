from kubernetes import config
import os
from kubernetes.config.config_exception import ConfigException
from kubernetes import client as k8s_client
from k8s_pod_killer.k8s_logging import _logging

#invoke logger
logger = _logging()

def _k8s_client():
    k8s_config_file = os.environ.get('KUBECONFIG')
    if k8s_config_file:
        try:
            logger.info('Loading kubernetes config from the file %s', k8s_config_file)
            config.load_kube_config(config_file=k8s_config_file)
        except Exception as e:
            raise RuntimeError('Can not load kube config from the file %s, error: %s', k8s_config_file, e)
    else:
        try:
            config.load_incluster_config()
            logger.info('Initialized with in-cluster config.')
        except:
            logger.info('Cannot find in-cluster config, trying the local kubernetes config. ')
            try:
                config.load_kube_config()
                logger.info('Found local kubernetes config. Initialized with kube_config.')
            except:
                raise RuntimeError('Please generate the kubeconfig file Check out the link: \
              https://cloud.google.com/kubernetes-engine/docs/how-to/cluster-access-for-kubectl for more information')
