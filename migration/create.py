import argparse
import logging
import json
import requests
import random
import string
import bcrypt


def rand(N):
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(N))

accounts = json.load(open('./output/accounts.json', 'r'))


def create(host=None, namespace=None, debug=False, verbosity=None):
    if not (host and namespace):
        raise RuntimeError('Must specify host and namespace')

    verbosity = min(max(verbosity or 0, 0), 2)
    if verbosity == 1:
        logging.basicConfig(level=logging.INFO)
    elif verbosity == 2:
        logging.basicConfig(level=logging.DEBUG)

    url = '{}/v1/id/collections/{}.accounts/documents'.format(host, namespace)

    for account in accounts:
        aid = account.pop('id')
        account['password'] = bcrypt.hashpw(rand(12), bcrypt.gensalt())
        account['demographicsChildBirthdays'] = filter(
            bool,
            map(
                lambda x: x if x != 'FAILED' else None,
                map(
                    unicode.strip,
                    account.get('demographicsChildBirthdays') or []
                )
            )
        )

        res = requests.post(url, json={
            'data': {
                'id': '{}.accounts.{}'.format(namespace, aid),
                'type': 'documents',
                'attributes': account
            }
        })
        if res.status_code != 201:
            if res.status_code == 409:
                pass
            elif debug:
                import ipdb
                ipdb.set_trace()  # noqa
            else:
                print res.json()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', type=str, required=True)
    parser.add_argument('-N', '--namespace', type=str, required=True)
    parser.add_argument('-D', '--debug', type=bool, default=False)
    parser.add_argument('-V', '--verbosity', type=int, default=0, choices=(0, 1, 2))
    args = parser.parse_args()
    create(**vars(args))
