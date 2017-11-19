import json
import os
import urllib.parse
import requests
from . import conf


class DoesNotExist(Exception):
    pass


def get_cache_path(path, params):
    req = requests.PreparedRequest()
    req.prepare_url(url='http://' + path.lstrip('/'), params=params)
    cache_path = req.url.split('//', 1)[1]

    if '/compare/' in cache_path:
        d, _, f = cache_path.partition('/compare/')
        d += _
    else:
        d, f = os.path.dirname(cache_path), os.path.basename(cache_path)
    return os.path.join(conf.CACHE_ROOT, d,
                        urllib.parse.quote_plus(f) + '.json')


def get(key):
    cache_path = get_cache_path(*key)
    if os.path.exists(cache_path):
        with open(cache_path) as fp:
            return json.load(fp)
    raise DoesNotExist(cache_path)


def set(key, value):
    cache_path = get_cache_path(*key)
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'w+') as fp:
        json.dump(value, fp, indent=2)
