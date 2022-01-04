from prometheus_client import Counter

# Used to identify the source of metrics for actions which can be performed on
# both pods and nodes
POD_SOURCE = 'pods'

# Define Prometheus metrics to be stored in the default registry

TOTAL_POD_KILLS_METRIC_NAME = 'total_no_of_pods_killed'
TOTAL_POD_KILLS = Counter(TOTAL_POD_KILLS_METRIC_NAME,
                    'Total number of pods killed')

POD_KILLS_METRIC_NAME = 'pod_kills_total'
POD_KILLS = Counter(POD_KILLS_METRIC_NAME,
                    'Number of each pods killed ',
                    ['name', 'namespace'])

MATCHED_TO_EMPTY_SET_METRIC_NAME = 'empty_match_total'
MATCHED_TO_EMPTY_SET = Counter(MATCHED_TO_EMPTY_SET_METRIC_NAME,
                               'Increasing counter for cases where matching '
                               'returns an empty result',
                               ['source'])
class prom():
    def __init__(self):
        MATCHED_TO_EMPTY_SET.labels(POD_SOURCE).inc(0)

    def _add_pod_killed_metric(self, name, ns):
        POD_KILLS.labels(name, ns).inc()

    def _add_total_pod_killed_metric(self):
        TOTAL_POD_KILLS.inc()
