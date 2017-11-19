import math
from . import github, cache


def fetch(full_name, repos=None):
    if repos is None:
        repos = {}
    full_name = full_name.lower()
    if full_name in repos:
        return
    r = github.repo(full_name)
    repos[full_name] = r
    if not r:
        return
    if 'fork' not in r:
        raise Exception(r)

    if r['fork']:
        fetch(r['parent']['full_name'], repos=repos)
        r['parent'] = r['parent']['full_name']
        r['source'] = r['source']['full_name']

    # r['tags'] = github.tags(full_name, per_page=100)
    r['heads'] = github.heads(full_name, per_page=100)

    if r['fork']:
        par = repos[r['parent']]
        par_heads = {h['ref']: h['object']['sha']
                     for h in par['heads']}
        for h in r['heads']:
            if h['ref'] == 'refs/heads/gh-pages':
                continue
            if h['ref'] in par_heads:
                par_head = h['ref']
            else:
                par_head = 'refs/heads/master'
            if h['object']['sha'] == par_heads[par_head]:
                h['unique'] = False
            else:
                h['compare'] = github.compare(
                    full_name=full_name,
                    base_owner=par['owner']['login'],
                    base_head=par_head.split('/heads/', 1)[-1],
                    owner=r['owner']['login'],
                    head=h['ref'].split('/heads/', 1)[-1])
                if h['compare']:
                    h['unique'] = bool(h['compare']['ahead_by'])
                else:
                    # print('No common:',
                    #       repo, h['ref'], par['full_name'], par_head)
                    h['unique'] = False

    if r['forks']:
        r['fork_names'] = []
        for p in range(1, int(math.ceil(r['forks']/100.0)) + 1):
            for f in github.forks(full_name, page=p, per_page=100):
                fn = f['full_name']
                if fn not in r['fork_names']:
                    r['fork_names'].append(fn)
                    fetch(fn, repos=repos)
    return repos


def strip_urls(d):
    if isinstance(d, dict):
        for k in list(d.keys()):
            if k.endswith('_url') or k == 'url':
                d.pop(k)
            else:
                strip_urls(d[k])
    elif isinstance(d, list):
        for i in d:
            strip_urls(i)
    return d


def get_forks(full_name):
    key = ('allforks/' + full_name, {})
    try:
        data = cache.get(key=key)
    except cache.DoesNotExist:
        data = fetch(full_name)
        cache.set(key, data)
    return data


def format_forks(data, name=None, known_heads=None, level=0):
    result = []
    if name is None:
        name = next(iter(data.values()))['source']
    if known_heads is None:
        known_heads = []
    ind1 = ' ' * 3
    ind = ind1 * level
    d = data.get(name.lower())
    if not d:
        return
    new_heads = []
    for h in d['heads']:
        if h['ref'].endswith('/gh-pages'):
            continue
        if h['object']['sha'] not in known_heads:
            known_heads.append(h['object']['sha'])
            branch = h['ref'].split('/heads/', 1)[-1]
            if not d['fork'] or h['unique']:
                commits = []
                if h.get('compare'):
                    branch += ' %s:%s' % (h['compare']['ahead_by'],
                                          h['compare']['behind_by'])
                    commits = [(c['commit']['author']['date'],
                                c['commit']['author']['name'],
                                c['commit']['message'])
                               for c in h['compare']['commits'][-10:]]
                new_heads.append((branch, commits))
    if new_heads:
        result.append('')
        result.append(ind + '📓 ' + name)
        for h, cc in new_heads:
            result.append(ind + ind1 + '↳ ' + h)
            for dt, nm, m in cc:
                result.append(ind + ind1 * 2 + '⊶ ' + dt +
                              '  ' + nm + '  ' + m.split('\n')[0])
    if d['forks']:
        for f in d['fork_names']:
            result += format_forks(data=data, name=f, known_heads=known_heads,
                                   level=level + 1)
    return result
