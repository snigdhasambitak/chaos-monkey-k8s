import yaml
from os import getenv
from random import seed, randint, sample
from dataclasses import dataclass, field
from dacite import from_dict, exceptions
from typing import List
from k8s_pod_killer.k8s_logging import _logging

#invoke logger
logger = _logging()


def _random_num_generator(limit):
    seed()
    return randint(0, (limit - 1))


def _random_num_list_generator(limit, amount):
    if limit == amount:
        return range(0, limit)
    else:
        seed()
        return sample(range(0, (limit - 1)), amount)

def _interval_calc(frequency, randomise=False):
    if randomise:
        interval = _random_num_generator(limit=frequency)
        if interval == 0:
            interval = frequency
    else:
        interval = frequency
    return interval


def _ns_inclusions():
    return ['']


def _ns_exclusions():
    return ['kube-system']


def _config_load(filename='config.yaml'):
    data = {}
    try:
        with open(filename, 'r') as f:
            data = yaml.safe_load(f)
    except IOError as e:
        logger.error(f"config yaml not found, error was: {e}")
        logger.warning(f"default config values will be used: {Config()}")
    except yaml.YAMLError as e:
        logger.error(f"failed to parse config yaml, error was: {e}")
        logger.warning(f"default config values will be used: {Config()}")

    if data:
        try:
            return from_dict(data_class=Config, data=data)
        except exceptions.WrongTypeError as e:
            logger.error(f"wrong type in config file. See error message: {e}")
            logger.warning(f"default config values will be used: {Config()}")
            return Config()
        except TypeError as e:
            logger.error(f"wrong type in config file. See error message: {e}")
            logger.warning(f"default config values will be used: {Config()}")
            return Config()
    else:
        return Config()


@dataclass
class Config:
    dryRun: bool = True
    debug: bool = False
    gracePeriod: int = 0
    updateFrequency: int = 45
    randomiseFrequency: bool = False
    podAnnotation: str = '',
    numPodsToDelete: int = 1
    includedNamespaces: List = field(default_factory=_ns_inclusions)
    excludedNamespaces: List = field(default_factory=_ns_exclusions)
