import json
import argparse
import logging

from scripts import client as CLI


def delete(host=None, namespace=None, debug=False, verbosity=None, load=False):
    if not (host and namespace):
        raise RuntimeError('Must specify host and namespace')

    url = '{}/v1/id/collections/{}.accounts/_search?q=_exists_:migratedFrom'.format(host, namespace)  # noqa
    client = CLI.ExperimenterClient(
        access_token=CLI.OSF_ACCESS_TOKEN,
        url=host,
        namespace=namespace
    ).authenticate()

    accounts = None
    if not load:
        accounts = client.fetch_accounts('q=_exists_:migratedFrom')
    else:
        accounts = [CLI.Account(a['id'], a['name'], a['email']) for a in json.load(open('migration/output/accounts.json', 'r'))]

    verbosity = min(max(verbosity or 0, 0), 2)
    if verbosity == 1:
        logging.basicConfig(level=logging.INFO)
    elif verbosity == 2:
        logging.basicConfig(level=logging.DEBUG)

    for account in accounts:
        res = client.delete_account(account)
        if res.status_code != 204:
            if res.status_code == 404:
                pass
            elif debug:
                import ipdb; ipdb.set_trace()  # noqa
            else:
                print res

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', type=str, required=True)
    parser.add_argument('-N', '--namespace', type=str, required=True)
    parser.add_argument('-D', '--debug', type=bool, default=False)
    parser.add_argument('-V', '--verbosity', type=int, default=0, choices=(0, 1, 2))
    parser.add_argument('-L', '--load', type=bool, default=False)
    args = parser.parse_args()
    delete(**vars(args))
