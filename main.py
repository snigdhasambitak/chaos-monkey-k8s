import sys
import time
from os import getenv

from k8s_pod_killer.k8s_api_client import _k8s_client
from k8s_pod_killer.k8s_logging import _logging
from k8s_pod_killer.k8s_pods_terminator import _kill_selected_pods
from k8s_pod_killer.k8s_pod_utility import _config_load, _interval_calc
from prometheus_client import start_http_server


#invoke logger
logger = _logging()


def main():

    logger.debug('DEBUG mode enabled - actions will be printed to log')
    logger.debug('Starting prometheus server on port 9000')

    # start prom server
    start_http_server(9000)

    cfg_file = getenv('CONFIG_FILE', 'config.yaml')
    config = _config_load(cfg_file)

    logger.debug('Config initialised with the following values:')
    logger.debug(f'  Dry Run:                {config.dryRun}')
    logger.debug(f'  Update Frequency:       {config.updateFrequency}')
    logger.debug(f'  Grace Period:           {config.gracePeriod}')
    logger.debug(f'  Randomised Frequency:   {config.randomiseFrequency}')
    logger.debug(f'  Included Namespaces:    {config.includedNamespaces}')
    logger.debug(f'  Excluded Namespaces:    {config.excludedNamespaces}')
    logger.debug(f'  Pods Annotation:        {config.podAnnotation}')
    logger.debug(f'  Pods To Delete:         {config.numPodsToDelete}')

    _k8s_client()

    while True:

        _kill_selected_pods(num_pods=config.numPodsToDelete,
                                dry_run=config.dryRun,
                                grace=config.gracePeriod,
                                inclusions=config.includedNamespaces,
                                exclusions=config.excludedNamespaces,
                                podannotations=config.podAnnotation)

        interval = _interval_calc(frequency=config.updateFrequency, randomise=config.randomiseFrequency)
        logger.debug(f'Sleeping for {interval}')
        time.sleep(interval)


def init():
    if __name__ == '__main__':
        sys.exit(main())

init()
