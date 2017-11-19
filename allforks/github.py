import logging
from datetime import datetime
import requests
from . import cache, conf

_log = logging.getLogger(__name__)
session = requests.Session()
session.headers['Authorization'] = 'token ' + conf.GITHUB_TOKEN


def api(path, **params):
    try:
        return cache.get((path, params))
    except cache.DoesNotExist:
        pass

    # _log.debug('GET %s %s', path, params or '')
    resp = session.get('https://api.github.com' + path, params=params)
    _log.debug('%s rate-limit remaining %s, reset in %s',
        resp.status_code,
        resp.headers['X-RateLimit-Remaining'],
        datetime.utcfromtimestamp(int(resp.headers['X-RateLimit-Reset'])) -
        datetime.utcnow(),
    )
    if resp.ok or resp.status_code == 404:
        cache.set((path, params), resp.json() if resp.ok else None)
    if resp.ok:
        return resp.json()
    _log.error('%s %s', resp.status_code, resp.text[:100])


def repo(full_name):
    return api('/repos/' + full_name)


def forks(full_name, **params):
    return api('/repos/%s/forks' % full_name, **params)


def heads(full_name, **params):
    return api('/repos/%s/git/refs/heads' % full_name, **params)


def tags(full_name, **params):
    return api('/repos/%s/git/refs/tags' % full_name, **params)


def compare(full_name, base_owner, base_head, owner, head):
    r = api('/repos/%s/compare/%s:%s...%s:%s' % (
        full_name, base_owner, base_head, owner, head))
    if r:
        assert 'base' not in r
        r['base'] = '%s:%s' % (base_owner, base_head)
        return r
